"""
Warp GPU Kernels for Bubble Physics

Batch-processes bubble physics for all tendroids in parallel on GPU.
Eliminates CPU-bound Python loops.

Complete lifecycle: spawn → rise → exit → release → pop → respawn
"""

import warp as wp

wp.init()


@wp.kernel
def update_bubble_physics_kernel(
  # Input state
  y_positions: wp.array(dtype=float),
  velocities_x: wp.array(dtype=float),
  velocities_y: wp.array(dtype=float),
  velocities_z: wp.array(dtype=float),
  world_x: wp.array(dtype=float),
  world_y: wp.array(dtype=float),
  world_z: wp.array(dtype=float),
  phases: wp.array(dtype=int),  # 0=idle, 1=rising, 2=exiting, 3=released, 4=popped
  ages: wp.array(dtype=float),
  release_timers: wp.array(dtype=float),
  current_radius: wp.array(dtype=float),  # Current bubble radius
  respawn_timers: wp.array(dtype=float),  # Countdown to respawn
  
  # Tendroid properties
  tendroid_x: wp.array(dtype=float),
  tendroid_y: wp.array(dtype=float),
  tendroid_z: wp.array(dtype=float),
  tendroid_lengths: wp.array(dtype=float),
  tendroid_radius: wp.array(dtype=float),
  
  # Bubble config (per-bubble)
  spawn_heights: wp.array(dtype=float),
  pop_heights: wp.array(dtype=float),
  max_diameter_heights: wp.array(dtype=float),
  max_radii: wp.array(dtype=float),
  
  # Config
  dt: float,
  rise_speed: float,
  released_rise_speed: float,
  respawn_delay: float,
  
  # Wave state (if enabled)
  wave_enabled: int,
  wave_displacement: float,
  wave_amplitude: float,
  wave_dir_x: float,
  wave_dir_z: float,
):
  """
  Update bubble physics for one bubble - COMPLETE LIFECYCLE.
  
  Each thread handles one tendroid's bubble.
  Phases: 0=idle, 1=rising, 2=exiting, 3=released, 4=popped
  """
  tid = wp.tid()
  
  phase = phases[tid]
  
  # Idle phase - waiting to spawn
  if phase == 0:
    return
  
  # Update age for active bubbles
  ages[tid] = ages[tid] + dt
  
  # Get tendroid info
  t_x = tendroid_x[tid]
  t_y = tendroid_y[tid]
  t_z = tendroid_z[tid]
  t_len = tendroid_lengths[tid]
  t_radius = tendroid_radius[tid]
  
  # Get bubble config
  spawn_y = spawn_heights[tid]
  pop_height = pop_heights[tid]
  max_diam_y = max_diameter_heights[tid]
  max_radius = max_radii[tid]
  
  # Rising phase
  if phase == 1:
    y_positions[tid] = y_positions[tid] + rise_speed * dt
    y = y_positions[tid]
    
    # Calculate radius growth: starts at 50%, grows to max
    min_radius = t_radius * 0.5
    if y <= spawn_y:
      current_radius[tid] = min_radius
    elif y >= max_diam_y:
      current_radius[tid] = max_radius
    else:
      t_progress = (y - spawn_y) / (max_diam_y - spawn_y)
      t_smooth = 1.0 - (1.0 - t_progress) * (1.0 - t_progress)
      current_radius[tid] = min_radius + t_smooth * (max_radius - min_radius)
    
    # Update world position with wave
    world_y[tid] = t_y + y
    
    # Calculate height factor for wave
    height_ratio = y / t_len if t_len > 0.0 else 0.0
    height_ratio = wp.clamp(height_ratio, 0.0, 1.0)
    h_factor = height_ratio * height_ratio * (3.0 - 2.0 * height_ratio)
    
    # Apply wave displacement
    if wave_enabled == 1:
      spatial_phase = t_x * 0.003 + t_z * 0.002
      spatial_factor = 1.0 + wp.sin(spatial_phase) * 0.15
      disp = wave_displacement * spatial_factor
      wave_dx = disp * wave_amplitude * wave_dir_x * h_factor
      wave_dz = disp * wave_amplitude * wave_dir_z * h_factor
      world_x[tid] = t_x + wave_dx
      world_z[tid] = t_z + wave_dz
    else:
      world_x[tid] = t_x
      world_z[tid] = t_z
    
    # Check if reached mouth (transition to exiting)
    if y >= t_len:
      phases[tid] = 2
  
  # Exiting phase
  elif phase == 2:
    y_positions[tid] = y_positions[tid] + rise_speed * dt
    y = y_positions[tid]
    
    # Update world position (same as rising)
    world_y[tid] = t_y + y
    
    height_ratio = y / t_len if t_len > 0.0 else 0.0
    height_ratio = wp.clamp(height_ratio, 0.0, 1.0)
    h_factor = height_ratio * height_ratio * (3.0 - 2.0 * height_ratio)
    
    if wave_enabled == 1:
      spatial_phase = t_x * 0.003 + t_z * 0.002
      spatial_factor = 1.0 + wp.sin(spatial_phase) * 0.15
      disp = wave_displacement * spatial_factor
      wave_dx = disp * wave_amplitude * wave_dir_x * h_factor
      wave_dz = disp * wave_amplitude * wave_dir_z * h_factor
      world_x[tid] = t_x + wave_dx
      world_z[tid] = t_z + wave_dz
    else:
      world_x[tid] = t_x
      world_z[tid] = t_z
    
    # Check if fully clear (transition to released)
    bubble_radius = current_radius[tid]
    if y >= t_len + bubble_radius:
      phases[tid] = 3
      release_timers[tid] = 0.0
  
  # Released phase
  elif phase == 3:
    release_timers[tid] = release_timers[tid] + dt
    
    # Velocity transition
    t = release_timers[tid]
    if t < 0.2:
      accel_factor = 1.0 - (1.0 - t / 0.2) * (1.0 - t / 0.2)
      velocities_y[tid] = rise_speed + (released_rise_speed - rise_speed) * accel_factor
    else:
      velocities_y[tid] = released_rise_speed
    
    # Wave drift
    if wave_enabled == 1:
      bubble_x = world_x[tid]
      bubble_z = world_z[tid]
      spatial_phase = bubble_x * 0.003 + bubble_z * 0.002
      spatial_factor = 1.0 + wp.sin(spatial_phase) * 0.15
      disp = wave_displacement * spatial_factor
      wave_dx = disp * wave_amplitude * wave_dir_x
      wave_dz = disp * wave_amplitude * wave_dir_z
      
      drift_strength = 0.15
      velocities_x[tid] = velocities_x[tid] * 0.92 + wave_dx * drift_strength
      velocities_z[tid] = velocities_z[tid] * 0.92 + wave_dz * drift_strength
    else:
      velocities_x[tid] = velocities_x[tid] * 0.95
      velocities_z[tid] = velocities_z[tid] * 0.95
    
    # Update position
    world_x[tid] = world_x[tid] + velocities_x[tid] * dt
    world_y[tid] = world_y[tid] + velocities_y[tid] * dt
    world_z[tid] = world_z[tid] + velocities_z[tid] * dt
    
    y_positions[tid] = world_y[tid] - t_y
    
    # Check for pop (transition to popped)
    if world_y[tid] >= pop_height:
      phases[tid] = 4
      respawn_timers[tid] = respawn_delay
  
  # Popped phase - countdown to respawn
  elif phase == 4:
    respawn_timers[tid] = respawn_timers[tid] - dt
    
    # Check for respawn (transition back to rising)
    if respawn_timers[tid] <= 0.0:
      phases[tid] = 1
      y_positions[tid] = spawn_y
      ages[tid] = 0.0
      velocities_x[tid] = 0.0
      velocities_y[tid] = 0.0
      velocities_z[tid] = 0.0
      current_radius[tid] = t_radius * 0.5
