"""
GPU-Accelerated Bubble Manager

Manages bubble physics using Warp kernels for parallel processing.
Complete lifecycle management with CPU ↔ GPU state synchronization.
"""

import warp as wp
import numpy as np
from .bubble_physics import update_bubble_physics_kernel

wp.init()


class BubbleGPUManager:
    """
    Manages bubble physics on GPU using Warp kernels.
    
    All bubble state lives in GPU arrays. Updates happen in parallel.
    Includes full lifecycle: spawn, rise, exit, release, pop, respawn.
    """
    
    def __init__(self, max_bubbles: int = 100, device: str = "cuda:0"):
        """
        Args:
            max_bubbles: Maximum number of concurrent bubbles
            device: Warp device ("cuda:0" for GPU)
        """
        self.max_bubbles = max_bubbles
        self.device = device
        self.active_count = 0
        
        # Allocate GPU arrays for bubble state
        self.y_positions_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.velocities_x_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.velocities_y_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.velocities_z_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        
        self.world_x_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.world_y_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.world_z_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        
        # Phase: 0=idle, 1=rising, 2=exiting, 3=released, 4=popped
        self.phases_gpu = wp.zeros(max_bubbles, dtype=int, device=device)
        self.ages_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.release_timers_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        
        # NEW: Lifecycle state
        self.current_radius_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.respawn_timers_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        
        # Tendroid properties (constant per bubble)
        self.tendroid_x_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.tendroid_y_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.tendroid_z_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.tendroid_lengths_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.tendroid_radius_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        
        # Bubble config (per-bubble)
        self.spawn_heights_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.pop_heights_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.max_diameter_heights_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.max_radii_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
    
    def register_bubble(
        self,
        bubble_id: int,
        tendroid_position: tuple,
        tendroid_length: float,
        tendroid_radius: float,
        spawn_y: float,
        pop_height: float,
        max_diameter_y: float,
        max_radius: float
    ):
        """
        Register a new bubble with its tendroid properties.
        
        Args:
            bubble_id: Index in array (0 to max_bubbles-1)
            tendroid_position: (x, y, z) world position
            tendroid_length: Cylinder height
            tendroid_radius: Base cylinder radius
            spawn_y: Starting Y position
            pop_height: Y position where bubble pops
            max_diameter_y: Y position where bubble reaches max size
            max_radius: Maximum bubble radius
        """
        if bubble_id >= self.max_bubbles:
            return
        
        # Update CPU arrays then upload
        phases = self.phases_gpu.numpy()
        phases[bubble_id] = 1  # rising
        self.phases_gpu = wp.array(phases, dtype=int, device=self.device)
        
        y_pos = self.y_positions_gpu.numpy()
        y_pos[bubble_id] = spawn_y
        self.y_positions_gpu = wp.array(y_pos, dtype=float, device=self.device)
        
        # Set initial radius
        radii = self.current_radius_gpu.numpy()
        radii[bubble_id] = tendroid_radius * 0.5
        self.current_radius_gpu = wp.array(radii, dtype=float, device=self.device)
        
        # Set tendroid properties
        self._update_array(self.tendroid_x_gpu, bubble_id, tendroid_position[0])
        self._update_array(self.tendroid_y_gpu, bubble_id, tendroid_position[1])
        self._update_array(self.tendroid_z_gpu, bubble_id, tendroid_position[2])
        self._update_array(self.tendroid_lengths_gpu, bubble_id, tendroid_length)
        self._update_array(self.tendroid_radius_gpu, bubble_id, tendroid_radius)
        
        # Set bubble config
        self._update_array(self.spawn_heights_gpu, bubble_id, spawn_y)
        self._update_array(self.pop_heights_gpu, bubble_id, pop_height)
        self._update_array(self.max_diameter_heights_gpu, bubble_id, max_diameter_y)
        self._update_array(self.max_radii_gpu, bubble_id, max_radius)
        
        self.active_count += 1
    
    def _update_array(self, gpu_array, index: int, value: float):
        """Helper to update single element in GPU array."""
        arr = gpu_array.numpy()
        arr[index] = value
        gpu_array.assign(wp.array(arr, dtype=gpu_array.dtype, device=self.device))
    
    def update_bubble_state(self, bubble_id: int, y_pos: float, phase: int):
        """
        Update individual bubble state from CPU.
        
        Used for CPU-initiated spawns or state corrections.
        
        Args:
            bubble_id: Bubble index
            y_pos: New Y position
            phase: New phase (0-4)
        """
        if bubble_id >= self.max_bubbles:
            return
        
        self._update_array(self.y_positions_gpu, bubble_id, y_pos)
        
        phases = self.phases_gpu.numpy()
        phases[bubble_id] = phase
        self.phases_gpu = wp.array(phases, dtype=int, device=self.device)
    
    def spawn_bubble(self, bubble_id: int, spawn_y: float, tendroid_radius: float):
        """
        Reset bubble to spawn state.
        
        Args:
            bubble_id: Bubble index
            spawn_y: Starting Y position
            tendroid_radius: Base radius for initial size
        """
        if bubble_id >= self.max_bubbles:
            return
        
        # Reset to rising phase at spawn position
        self._update_array(self.y_positions_gpu, bubble_id, spawn_y)
        self._update_array(self.ages_gpu, bubble_id, 0.0)
        self._update_array(self.velocities_x_gpu, bubble_id, 0.0)
        self._update_array(self.velocities_y_gpu, bubble_id, 0.0)
        self._update_array(self.velocities_z_gpu, bubble_id, 0.0)
        self._update_array(self.current_radius_gpu, bubble_id, tendroid_radius * 0.5)
        
        phases = self.phases_gpu.numpy()
        phases[bubble_id] = 1  # rising
        self.phases_gpu = wp.array(phases, dtype=int, device=self.device)
    
    def update_all(
        self,
        dt: float,
        rise_speed: float,
        released_rise_speed: float,
        respawn_delay: float,
        wave_state: dict = None
    ):
        """
        Update all bubble physics in parallel on GPU.
        
        Args:
            dt: Delta time
            rise_speed: Rising speed inside cylinder
            released_rise_speed: Free-float speed
            respawn_delay: Seconds until respawn after pop
            wave_state: Optional wave controller state
        """
        if self.active_count == 0:
            return
        
        # Extract wave state
        wave_enabled = 0
        wave_displacement = 0.0
        wave_amplitude = 0.0
        wave_dir_x = 0.0
        wave_dir_z = 0.0
        
        if wave_state and wave_state.get('enabled', False):
            wave_enabled = 1
            wave_displacement = wave_state.get('displacement', 0.0)
            wave_amplitude = wave_state.get('amplitude', 0.0)
            wave_dir_x = wave_state.get('dir_x', 0.0)
            wave_dir_z = wave_state.get('dir_z', 0.0)
        
        # Launch kernel for ALL bubbles (idle bubbles skip in kernel)
        wp.launch(
            kernel=update_bubble_physics_kernel,
            dim=self.max_bubbles,
            inputs=[
                self.y_positions_gpu,
                self.velocities_x_gpu,
                self.velocities_y_gpu,
                self.velocities_z_gpu,
                self.world_x_gpu,
                self.world_y_gpu,
                self.world_z_gpu,
                self.phases_gpu,
                self.ages_gpu,
                self.release_timers_gpu,
                self.current_radius_gpu,
                self.respawn_timers_gpu,
                self.tendroid_x_gpu,
                self.tendroid_y_gpu,
                self.tendroid_z_gpu,
                self.tendroid_lengths_gpu,
                self.tendroid_radius_gpu,
                self.spawn_heights_gpu,
                self.pop_heights_gpu,
                self.max_diameter_heights_gpu,
                self.max_radii_gpu,
                dt,
                rise_speed,
                released_rise_speed,
                respawn_delay,
                wave_enabled,
                wave_displacement,
                wave_amplitude,
                wave_dir_x,
                wave_dir_z,
            ],
            device=self.device
        )
    
    def get_bubble_states(self) -> tuple:
        """
        Download bubble states from GPU.
        
        Returns:
            (phases, world_positions, radii) as numpy arrays
            phases: [N] int array
            world_positions: [N, 3] float array  
            radii: [N] float array
        """
        phases = self.phases_gpu.numpy()
        
        wx = self.world_x_gpu.numpy()
        wy = self.world_y_gpu.numpy()
        wz = self.world_z_gpu.numpy()
        
        world_positions = np.stack([wx, wy, wz], axis=-1)
        radii = self.current_radius_gpu.numpy()
        
        return phases, world_positions, radii
    
    def get_bubble_radii(self) -> np.ndarray:
        """
        Download current bubble radii from GPU.
        
        Returns:
            [N] float array of current radii
        """
        return self.current_radius_gpu.numpy()
    
    def destroy(self):
        """Free GPU resources."""
        # Clear all references to allow GPU memory cleanup
        arrays = [
            'y_positions_gpu', 'velocities_x_gpu', 'velocities_y_gpu', 'velocities_z_gpu',
            'world_x_gpu', 'world_y_gpu', 'world_z_gpu', 'phases_gpu', 'ages_gpu',
            'release_timers_gpu', 'current_radius_gpu', 'respawn_timers_gpu',
            'tendroid_x_gpu', 'tendroid_y_gpu', 'tendroid_z_gpu', 
            'tendroid_lengths_gpu', 'tendroid_radius_gpu',
            'spawn_heights_gpu', 'pop_heights_gpu', 'max_diameter_heights_gpu', 'max_radii_gpu'
        ]
        for attr in arrays:
            setattr(self, attr, None)
