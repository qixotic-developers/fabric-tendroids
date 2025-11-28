"""
Warp GPU Kernel for Pop Particle Physics

Batch-processes all pop particles in parallel on GPU.
Simple physics: gravity + velocity integration + lifetime tracking.
"""

import warp as wp

wp.init()


@wp.kernel
def update_pop_particles_kernel(
    # Positions (read/write)
    pos_x: wp.array(dtype=float),
    pos_y: wp.array(dtype=float),
    pos_z: wp.array(dtype=float),
    
    # Velocities (read/write)
    vel_x: wp.array(dtype=float),
    vel_y: wp.array(dtype=float),
    vel_z: wp.array(dtype=float),
    
    # Lifecycle (read/write)
    ages: wp.array(dtype=float),
    lifetimes: wp.array(dtype=float),
    alive_flags: wp.array(dtype=int),  # 1=alive, 0=dead
    
    # Config
    dt: float,
    gravity: float,
):
    """
    Update single particle physics.
    
    Each thread handles one particle.
    Dead particles (alive_flags=0) skip processing.
    """
    tid = wp.tid()
    
    # Skip dead particles
    if alive_flags[tid] == 0:
        return
    
    # Update age
    new_age = ages[tid] + dt
    ages[tid] = new_age
    
    # Check lifetime - mark dead if expired
    if new_age >= lifetimes[tid]:
        alive_flags[tid] = 0
        return
    
    # Apply gravity to Y velocity
    vel_y[tid] = vel_y[tid] + gravity * dt
    
    # Integrate position
    pos_x[tid] = pos_x[tid] + vel_x[tid] * dt
    pos_y[tid] = pos_y[tid] + vel_y[tid] * dt
    pos_z[tid] = pos_z[tid] + vel_z[tid] * dt


@wp.kernel
def spawn_particles_kernel(
    # Target arrays
    pos_x: wp.array(dtype=float),
    pos_y: wp.array(dtype=float),
    pos_z: wp.array(dtype=float),
    vel_x: wp.array(dtype=float),
    vel_y: wp.array(dtype=float),
    vel_z: wp.array(dtype=float),
    ages: wp.array(dtype=float),
    lifetimes: wp.array(dtype=float),
    alive_flags: wp.array(dtype=int),
    
    # Spawn data (one entry per particle to spawn)
    spawn_indices: wp.array(dtype=int),
    spawn_pos_x: wp.array(dtype=float),
    spawn_pos_y: wp.array(dtype=float),
    spawn_pos_z: wp.array(dtype=float),
    spawn_vel_x: wp.array(dtype=float),
    spawn_vel_y: wp.array(dtype=float),
    spawn_vel_z: wp.array(dtype=float),
    spawn_lifetimes: wp.array(dtype=float),
):
    """
    Spawn new particles at specified indices.
    
    Each thread initializes one particle slot.
    """
    tid = wp.tid()
    
    idx = spawn_indices[tid]
    
    pos_x[idx] = spawn_pos_x[tid]
    pos_y[idx] = spawn_pos_y[tid]
    pos_z[idx] = spawn_pos_z[tid]
    
    vel_x[idx] = spawn_vel_x[tid]
    vel_y[idx] = spawn_vel_y[tid]
    vel_z[idx] = spawn_vel_z[tid]
    
    ages[idx] = 0.0
    lifetimes[idx] = spawn_lifetimes[tid]
    alive_flags[idx] = 1
