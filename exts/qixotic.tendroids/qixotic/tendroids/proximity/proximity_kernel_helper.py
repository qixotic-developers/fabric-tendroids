"""
Proximity Kernel Helper Functions

GPU-accelerated Warp kernels for creature-tendroid proximity detection.

TEND-16: Implement proximity kernel for single tendroid
TEND-71: Write @wp.kernel for proximity detection
TEND-72: Implement horizontal distance calculation to tendroid surface
TEND-73: Output force vector for detected proximity
"""

import warp as wp

# Initialize Warp (safe to call multiple times)
wp.init()


# ============================================================================
# TEND-71: Proximity Detection Kernel
# ============================================================================

@wp.kernel
def proximity_check_kernel(
  grid: wp.uint64,
  creature_positions: wp.array(dtype=wp.vec3),
  tendroid_positions: wp.array(dtype=wp.vec3),
  tendroid_radii: wp.array(dtype=float),
  detection_radius: float,
  # Outputs
  detected_flags: wp.array(dtype=int),
  nearest_tendroid_idx: wp.array(dtype=int),
  surface_distances: wp.array(dtype=float)
):
  """
  GPU kernel for proximity detection with O(1) neighbor queries.

  Checks each creature position against the hash grid to find
  nearby tendroids and computes horizontal distance to surface.

  TEND-71: Core proximity detection kernel

  Args:
      grid: Hash grid ID for spatial queries
      creature_positions: Array of creature center positions
      tendroid_positions: Array of tendroid center positions
      tendroid_radii: Array of tendroid radii
      detection_radius: Maximum detection distance
      detected_flags: Output - 1 if tendroid detected, 0 otherwise
      nearest_tendroid_idx: Output - index of nearest tendroid (-1 if none)
      surface_distances: Output - distance to nearest tendroid surface
  """
  tid = wp.tid()
  creature_pos = creature_positions[tid]

  min_surface_dist = detection_radius * 2.0
  nearest_idx = int(-1)

  # Query hash grid for nearby tendroids
  query_result = wp.hash_grid_query(grid, creature_pos, detection_radius)

  for t_idx in query_result:
    tendroid_pos = tendroid_positions[t_idx]
    tendroid_radius = tendroid_radii[t_idx]

    # TEND-72: Horizontal (XZ plane) distance calculation
    dx = creature_pos[0] - tendroid_pos[0]
    dz = creature_pos[2] - tendroid_pos[2]
    horizontal_dist = wp.sqrt(dx * dx + dz * dz)

    # Distance to tendroid surface (not center)
    surface_dist = horizontal_dist - tendroid_radius

    if surface_dist < min_surface_dist:
      min_surface_dist = surface_dist
      nearest_idx = t_idx

  # Store results
  if nearest_idx >= 0:
    detected_flags[tid] = 1
    nearest_tendroid_idx[tid] = nearest_idx
    surface_distances[tid] = min_surface_dist
  else:
    detected_flags[tid] = 0
    nearest_tendroid_idx[tid] = -1
    surface_distances[tid] = detection_radius


# ============================================================================
# TEND-72: Horizontal Distance Calculation Kernel
# ============================================================================

@wp.kernel
def horizontal_distance_kernel(
  creature_positions: wp.array(dtype=wp.vec3),
  tendroid_position: wp.vec3,
  tendroid_radius: float,
  surface_distances: wp.array(dtype=float),
  direction_vectors: wp.array(dtype=wp.vec3)
):
  """
  Compute horizontal distance from creature to single tendroid surface.

  Uses XZ plane distance (ignores Y/height) for horizontal proximity.
  This handles cases where creature and tendroid are at different heights.

  TEND-72: Horizontal distance calculation

  Args:
      creature_positions: Array of creature positions
      tendroid_position: Single tendroid center position
      tendroid_radius: Tendroid cylinder radius
      surface_distances: Output - distance to surface (negative = inside)
      direction_vectors: Output - normalized direction from tendroid to creature
  """
  tid = wp.tid()
  creature_pos = creature_positions[tid]

  # Horizontal displacement (XZ plane only)
  dx = creature_pos[0] - tendroid_position[0]
  dz = creature_pos[2] - tendroid_position[2]
  horizontal_dist = wp.sqrt(dx * dx + dz * dz)

  # Distance to surface (can be negative if inside)
  surface_dist = horizontal_dist - tendroid_radius
  surface_distances[tid] = surface_dist

  # Normalized direction vector (horizontal only)
  if horizontal_dist > 0.0001:
    dir_x = dx / horizontal_dist
    dir_z = dz / horizontal_dist
    direction_vectors[tid] = wp.vec3(dir_x, 0.0, dir_z)
  else:
    # At center - arbitrary direction
    direction_vectors[tid] = wp.vec3(1.0, 0.0, 0.0)


# ============================================================================
# TEND-73: Force Vector Output Kernel
# ============================================================================

@wp.kernel
def compute_repulsion_force_kernel(
  creature_positions: wp.array(dtype=wp.vec3),
  tendroid_position: wp.vec3,
  tendroid_radius: float,
  detection_radius: float,
  force_strength: float,
  forces: wp.array(dtype=wp.vec3)
):
  """
  Compute repulsion force vector for creatures near tendroid.

  Force increases as creature approaches tendroid surface.
  Uses smooth falloff for natural avoidance behavior.

  TEND-73: Force vector output for repulsion

  Args:
      creature_positions: Array of creature positions
      tendroid_position: Single tendroid center position
      tendroid_radius: Tendroid cylinder radius
      detection_radius: Maximum force range
      force_strength: Base force magnitude
      forces: Output - repulsion force vectors
  """
  tid = wp.tid()
  creature_pos = creature_positions[tid]

  # Horizontal displacement
  dx = creature_pos[0] - tendroid_position[0]
  dz = creature_pos[2] - tendroid_position[2]
  horizontal_dist = wp.sqrt(dx * dx + dz * dz)

  # Distance to surface
  surface_dist = horizontal_dist - tendroid_radius

  if surface_dist <= 0.0:
    # Inside tendroid - maximum repulsion outward
    if horizontal_dist > 0.0001:
      dir_x = dx / horizontal_dist
      dir_z = dz / horizontal_dist
      forces[tid] = wp.vec3(dir_x * force_strength, 0.0, dir_z * force_strength)
    else:
      forces[tid] = wp.vec3(force_strength, 0.0, 0.0)
  elif surface_dist < detection_radius:
    # Within detection range - smooth falloff
    # Force = strength * (1 - distance/max_distance)^2
    t = surface_dist / detection_radius
    falloff = (1.0 - t) * (1.0 - t)
    magnitude = force_strength * falloff

    # Direction away from tendroid (horizontal)
    if horizontal_dist > 0.0001:
      dir_x = dx / horizontal_dist
      dir_z = dz / horizontal_dist
      forces[tid] = wp.vec3(dir_x * magnitude, 0.0, dir_z * magnitude)
    else:
      forces[tid] = wp.vec3(magnitude, 0.0, 0.0)
  else:
    # Outside detection range - no force
    forces[tid] = wp.vec3(0.0, 0.0, 0.0)


@wp.kernel
def compute_zone_based_force_kernel(
  surface_distances: wp.array(dtype=float),
  direction_vectors: wp.array(dtype=wp.vec3),
  epsilon: float,
  minimum: float,
  warning: float,
  detection: float,
  force_contact: float,
  force_recovering: float,
  force_approaching: float,
  force_detected: float,
  forces: wp.array(dtype=wp.vec3),
  zones: wp.array(dtype=int)
):
  """
  Compute zone-based repulsion forces using approach parameters.

  Zones (from tendroid surface outward):
    0 = contact (< epsilon) - maximum force
    1 = recovering (< minimum) - strong force
    2 = approaching (< warning) - moderate force
    3 = detected (< detection) - light force
    4 = idle (>= detection) - no force

  Args:
      surface_distances: Pre-computed distances to surface
      direction_vectors: Pre-computed normalized directions
      epsilon/minimum/warning/detection: Zone thresholds
      force_*: Force magnitudes per zone
      forces: Output - force vectors
      zones: Output - zone indices
  """
  tid = wp.tid()
  dist = surface_distances[tid]
  direction = direction_vectors[tid]

  zone = int(4)  # idle
  magnitude = float(0.0)

  if dist <= epsilon:
    zone = 0
    magnitude = force_contact
  elif dist <= minimum:
    zone = 1
    magnitude = force_recovering
  elif dist <= warning:
    zone = 2
    magnitude = force_approaching
  elif dist <= detection:
    zone = 3
    magnitude = force_detected

  forces[tid] = direction * magnitude
  zones[tid] = zone
