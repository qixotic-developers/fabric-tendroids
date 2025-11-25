"""
GPU-Accelerated Pop Particle Manager

Manages pop particle physics using Warp kernels for parallel processing.
Handles spawning, physics updates, and state synchronization.
"""

import math
import random

import numpy as np
import warp as wp

from .pop_particle_physics import update_pop_particles_kernel, spawn_particles_kernel

wp.init()


class PopParticleGPUManager:
    """
    Manages pop particle physics on GPU using Warp kernels.
    
    All particle state lives in GPU arrays. Updates happen in parallel.
    CPU only handles spawning decisions and USD visual updates.
    """
    
    def __init__(self, max_particles: int = 200, device: str = "cuda:0"):
        """
        Args:
            max_particles: Maximum concurrent particles
            device: Warp device ("cuda:0" for GPU)
        """
        self.max_particles = max_particles
        self.device = device
        self.gravity = -5.0
        
        # GPU arrays - positions
        self.pos_x_gpu = wp.zeros(max_particles, dtype=float, device=device)
        self.pos_y_gpu = wp.zeros(max_particles, dtype=float, device=device)
        self.pos_z_gpu = wp.zeros(max_particles, dtype=float, device=device)
        
        # GPU arrays - velocities
        self.vel_x_gpu = wp.zeros(max_particles, dtype=float, device=device)
        self.vel_y_gpu = wp.zeros(max_particles, dtype=float, device=device)
        self.vel_z_gpu = wp.zeros(max_particles, dtype=float, device=device)
        
        # GPU arrays - lifecycle
        self.ages_gpu = wp.zeros(max_particles, dtype=float, device=device)
        self.lifetimes_gpu = wp.zeros(max_particles, dtype=float, device=device)
        self.alive_flags_gpu = wp.zeros(max_particles, dtype=int, device=device)
        
        # Free slot tracking (CPU side)
        self.free_slots = list(range(max_particles))
        self.active_slots = set()
    
    def get_active_count(self) -> int:
        """Return number of active particles."""
        return len(self.active_slots)
    
    def has_capacity(self, count: int) -> bool:
        """Check if we can spawn count more particles."""
        return len(self.free_slots) >= count
    
    def spawn_spray(
        self,
        pop_position: tuple,
        bubble_velocity: list,
        num_particles: int,
        particle_speed: float,
        particle_spread: float,
        base_lifetime: float
    ) -> list:
        """
        Spawn a spray of particles at pop location.
        
        Args:
            pop_position: (x, y, z) where bubble popped
            bubble_velocity: [vx, vy, vz] bubble's velocity at pop
            num_particles: How many particles to spawn
            particle_speed: Base spray speed
            particle_spread: Spread angle in degrees
            base_lifetime: Base lifetime (will be randomized +/- 30%)
            
        Returns:
            List of slot indices that were spawned (for USD creation)
        """
        actual_count = min(num_particles, len(self.free_slots))
        if actual_count == 0:
            return []
        
        # Claim slots
        spawned_indices = []
        for _ in range(actual_count):
            idx = self.free_slots.pop()
            self.active_slots.add(idx)
            spawned_indices.append(idx)
        
        # Build spawn data arrays
        spawn_pos_x = np.full(actual_count, pop_position[0], dtype=np.float32)
        spawn_pos_y = np.full(actual_count, pop_position[1], dtype=np.float32)
        spawn_pos_z = np.full(actual_count, pop_position[2], dtype=np.float32)
        
        spawn_vel_x = np.zeros(actual_count, dtype=np.float32)
        spawn_vel_y = np.zeros(actual_count, dtype=np.float32)
        spawn_vel_z = np.zeros(actual_count, dtype=np.float32)
        spawn_lifetimes = np.zeros(actual_count, dtype=np.float32)
        
        # Generate random velocities for each particle
        for i in range(actual_count):
            angle = random.uniform(0, 2 * math.pi)
            elevation = random.uniform(-particle_spread / 2, particle_spread)
            
            spray_vx = particle_speed * math.cos(angle) * math.cos(math.radians(elevation))
            spray_vy = particle_speed * math.sin(math.radians(elevation))
            spray_vz = particle_speed * math.sin(angle) * math.cos(math.radians(elevation))
            
            spawn_vel_x[i] = bubble_velocity[0] + spray_vx
            spawn_vel_y[i] = bubble_velocity[1] + spray_vy
            spawn_vel_z[i] = bubble_velocity[2] + spray_vz
            
            spawn_lifetimes[i] = base_lifetime * random.uniform(0.7, 1.3)
        
        # Upload spawn data to GPU
        indices_gpu = wp.array(spawned_indices, dtype=int, device=self.device)
        spawn_px = wp.array(spawn_pos_x, dtype=float, device=self.device)
        spawn_py = wp.array(spawn_pos_y, dtype=float, device=self.device)
        spawn_pz = wp.array(spawn_pos_z, dtype=float, device=self.device)
        spawn_vx = wp.array(spawn_vel_x, dtype=float, device=self.device)
        spawn_vy = wp.array(spawn_vel_y, dtype=float, device=self.device)
        spawn_vz = wp.array(spawn_vel_z, dtype=float, device=self.device)
        spawn_lt = wp.array(spawn_lifetimes, dtype=float, device=self.device)
        
        # Launch spawn kernel
        wp.launch(
            kernel=spawn_particles_kernel,
            dim=actual_count,
            inputs=[
                self.pos_x_gpu, self.pos_y_gpu, self.pos_z_gpu,
                self.vel_x_gpu, self.vel_y_gpu, self.vel_z_gpu,
                self.ages_gpu, self.lifetimes_gpu, self.alive_flags_gpu,
                indices_gpu,
                spawn_px, spawn_py, spawn_pz,
                spawn_vx, spawn_vy, spawn_vz,
                spawn_lt,
            ],
            device=self.device
        )
        
        return spawned_indices
    
    def update(self, dt: float) -> list:
        """
        Update all particle physics on GPU.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            List of slot indices that died this frame (for USD cleanup)
        """
        if not self.active_slots:
            return []
        
        # Launch physics kernel for ALL slots (dead ones skip internally)
        wp.launch(
            kernel=update_pop_particles_kernel,
            dim=self.max_particles,
            inputs=[
                self.pos_x_gpu, self.pos_y_gpu, self.pos_z_gpu,
                self.vel_x_gpu, self.vel_y_gpu, self.vel_z_gpu,
                self.ages_gpu, self.lifetimes_gpu, self.alive_flags_gpu,
                dt, self.gravity,
            ],
            device=self.device
        )
        
        # Check for newly dead particles
        alive_flags = self.alive_flags_gpu.numpy()
        dead_slots = []
        
        for idx in list(self.active_slots):
            if alive_flags[idx] == 0:
                dead_slots.append(idx)
                self.active_slots.remove(idx)
                self.free_slots.append(idx)
        
        return dead_slots
    
    def get_positions(self) -> np.ndarray:
        """
        Download all particle positions from GPU.
        
        Returns:
            [max_particles, 3] float array of positions
        """
        px = self.pos_x_gpu.numpy()
        py = self.pos_y_gpu.numpy()
        pz = self.pos_z_gpu.numpy()
        return np.stack([px, py, pz], axis=-1)
    
    def get_active_positions(self) -> dict:
        """
        Get positions only for active particles.
        
        Returns:
            Dict mapping slot_index -> (x, y, z) tuple of Python floats
        """
        if not self.active_slots:
            return {}
        
        positions = self.get_positions()
        # Convert numpy.float32 to Python float for USD compatibility
        return {
            idx: (float(positions[idx][0]), float(positions[idx][1]), float(positions[idx][2]))
            for idx in self.active_slots
        }
    
    def clear_all(self) -> list:
        """
        Mark all particles as dead and return their indices.
        
        Returns:
            List of all previously active slot indices
        """
        dead_slots = list(self.active_slots)
        
        # Reset alive flags on GPU
        alive_flags = np.zeros(self.max_particles, dtype=np.int32)
        self.alive_flags_gpu = wp.array(alive_flags, dtype=int, device=self.device)
        
        # Reset tracking
        self.free_slots = list(range(self.max_particles))
        self.active_slots = set()
        
        return dead_slots
    
    def destroy(self):
        """Free GPU resources."""
        arrays = [
            'pos_x_gpu', 'pos_y_gpu', 'pos_z_gpu',
            'vel_x_gpu', 'vel_y_gpu', 'vel_z_gpu',
            'ages_gpu', 'lifetimes_gpu', 'alive_flags_gpu'
        ]
        for attr in arrays:
            setattr(self, attr, None)
