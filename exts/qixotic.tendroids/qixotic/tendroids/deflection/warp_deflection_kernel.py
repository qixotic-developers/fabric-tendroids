"""
Warp GPU Kernel for Batch Deflection Calculations

TEND-88: Create Warp GPU kernel for batch deflection calculation

Processes all tendroid deflection calculations in a single GPU pass
for maximum performance with large tendroid counts.
"""

import warp as wp

# Initialize Warp
wp.init()


@wp.kernel
def batch_deflection_kernel(
  # Tendroid geometry (per-tendroid)
  tendroid_centers_x: wp.array(dtype=float),
  tendroid_centers_z: wp.array(dtype=float),
  tendroid_base_y: wp.array(dtype=float),
  tendroid_heights: wp.array(dtype=float),
  tendroid_radii: wp.array(dtype=float),
  # Creature state (broadcast)
  creature_x: float,
  creature_y: float,
  creature_z: float,
  creature_vx: float,
  creature_vy: float,
  creature_vz: float,
  # Detection zones
  detection_range: float,
  approach_buffer: float,
  # Deflection limits
  min_deflection: float,
  max_deflection: float,
  # Output arrays
  out_target_angles: wp.array(dtype=float),
  out_direction_x: wp.array(dtype=float),
  out_direction_z: wp.array(dtype=float),
  out_approach_types: wp.array(dtype=int),
):
  """
  GPU kernel to calculate deflection for all tendroids in parallel.

  Each thread processes one tendroid:
  1. Calculate horizontal distance to creature
  2. Detect approach type (vertical, head-on, pass-by)
  3. Calculate deflection angle proportional to height
  4. Output direction and angle
  """
  tid = wp.tid()

  # Get tendroid geometry
  center_x = tendroid_centers_x[tid]
  center_z = tendroid_centers_z[tid]
  base_y = tendroid_base_y[tid]
  height = tendroid_heights[tid]
  radius = tendroid_radii[tid]

  # Calculate horizontal distance (XZ plane only)
  dx = creature_x - center_x
  dz = creature_z - center_z
  horizontal_dist = wp.sqrt(dx * dx + dz * dz)

  # Default: no deflection
  target_angle = 0.0
  dir_x = 0.0
  dir_z = 0.0
  approach_type = 0  # NONE

  # Check if within detection range
  if horizontal_dist < detection_range:
    # Calculate height ratio for deflection
    tip_y = base_y + height

    # Check vertical proximity (creature within tendroid Y range)
    if creature_y >= base_y and creature_y <= tip_y:
      # Calculate height ratio (0 at base, 1 at tip)
      height_ratio = (creature_y - base_y) / height
      height_ratio = wp.clamp(height_ratio, 0.0, 1.0)

      # Calculate distance ratio (0 at contact, 1 at detection_range)
      contact_dist = radius + approach_buffer
      if horizontal_dist < contact_dist:
        dist_ratio = 0.0
      else:
        dist_ratio = (horizontal_dist - contact_dist) / (detection_range - contact_dist)
      dist_ratio = wp.clamp(dist_ratio, 0.0, 1.0)

      # Interpolate deflection angle based on height
      angle_range = max_deflection - min_deflection
      base_angle = min_deflection + height_ratio * angle_range

      # Apply distance falloff (closer = more deflection)
      falloff = 1.0 - dist_ratio
      target_angle = base_angle * falloff

      # Calculate deflection direction (away from creature)
      if horizontal_dist > 0.001:
        dir_x = -dx / horizontal_dist
        dir_z = -dz / horizontal_dist
      else:
        dir_x = 1.0
        dir_z = 0.0

      # Determine approach type based on velocity
      vel_mag = wp.sqrt(creature_vx * creature_vx + creature_vz * creature_vz)

      if vel_mag > 0.1:
        # Normalize velocity
        vel_nx = creature_vx / vel_mag
        vel_nz = creature_vz / vel_mag

        # Dot product with direction to tendroid
        dot = vel_nx * (-dir_x) + vel_nz * (-dir_z)

        if dot > 0.7:
          approach_type = 2  # HEAD_ON
        elif wp.abs(dot) < 0.5:
          approach_type = 3  # PASS_BY
        else:
          approach_type = 1  # VERTICAL
      else:
        approach_type = 1  # VERTICAL (hovering)

  # Write outputs
  out_target_angles[tid] = target_angle
  out_direction_x[tid] = dir_x
  out_direction_z[tid] = dir_z
  out_approach_types[tid] = approach_type


@wp.kernel
def smooth_deflection_kernel(
  current_angles: wp.array(dtype=float),
  target_angles: wp.array(dtype=float),
  dt: float,
  deflection_rate: float,
  recovery_rate: float,
  out_angles: wp.array(dtype=float),
):
  """
  GPU kernel to smooth deflection transitions.

  Applies different rates for deflecting vs recovering.
  """
  tid = wp.tid()

  current = current_angles[tid]
  target = target_angles[tid]

  # Choose rate based on direction
  if target > current:
    rate = deflection_rate
  else:
    rate = recovery_rate

  # Calculate max change for this frame
  max_change = rate * dt

  # Apply change
  diff = target - current
  if wp.abs(diff) <= max_change:
    out_angles[tid] = target
  elif diff > 0.0:
    out_angles[tid] = current + max_change
  else:
    out_angles[tid] = current - max_change
