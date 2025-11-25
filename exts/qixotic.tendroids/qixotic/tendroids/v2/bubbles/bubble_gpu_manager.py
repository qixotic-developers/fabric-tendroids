"""
GPU-Accelerated Bubble Manager

Manages bubble physics using Warp kernels for parallel processing.
Replaces CPU-bound Python loops with GPU batch operations.
"""

import warp as wp
import numpy as np
from .bubble_physics import update_bubble_physics_kernel

wp.init()


class BubbleGPUManager:
    """
    Manages bubble physics on GPU using Warp kernels.
    
    All bubble state lives in GPU arrays. Updates happen in parallel.
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
        
        # Tendroid properties (constant per bubble)
        self.tendroid_x_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.tendroid_y_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.tendroid_z_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        self.tendroid_lengths_gpu = wp.zeros(max_bubbles, dtype=float, device=device)
        
        # CPU mirrors for readback (only when needed)
        self._phases_cpu = None
        self._world_positions_cpu = None
    
    def register_bubble(
        self,
        bubble_id: int,
        tendroid_position: tuple,
        tendroid_length: float,
        spawn_y: float
    ):
        """
        Register a new bubble with its tendroid properties.
        
        Args:
            bubble_id: Index in array (0 to max_bubbles-1)
            tendroid_position: (x, y, z) world position
            tendroid_length: Cylinder height
            spawn_y: Starting Y position
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
        
        # Set tendroid properties
        t_x = self.tendroid_x_gpu.numpy()
        t_y = self.tendroid_y_gpu.numpy()
        t_z = self.tendroid_z_gpu.numpy()
        t_len = self.tendroid_lengths_gpu.numpy()
        
        t_x[bubble_id] = tendroid_position[0]
        t_y[bubble_id] = tendroid_position[1]
        t_z[bubble_id] = tendroid_position[2]
        t_len[bubble_id] = tendroid_length
        
        self.tendroid_x_gpu = wp.array(t_x, dtype=float, device=self.device)
        self.tendroid_y_gpu = wp.array(t_y, dtype=float, device=self.device)
        self.tendroid_z_gpu = wp.array(t_z, dtype=float, device=self.device)
        self.tendroid_lengths_gpu = wp.array(t_len, dtype=float, device=self.device)
        
        self.active_count += 1
    
    def update_all(
        self,
        dt: float,
        rise_speed: float,
        released_rise_speed: float,
        spawn_height_pct: float,
        wave_state: dict = None
    ):
        """
        Update all bubble physics in parallel on GPU.
        
        Args:
            dt: Delta time
            rise_speed: Rising speed
            released_rise_speed: Free-float speed
            spawn_height_pct: Spawn height percentage
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
                self.tendroid_x_gpu,
                self.tendroid_y_gpu,
                self.tendroid_z_gpu,
                self.tendroid_lengths_gpu,
                dt,
                rise_speed,
                released_rise_speed,
                spawn_height_pct,
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
            (phases, world_positions) as numpy arrays
            phases: [N] int array
            world_positions: [N, 3] float array
        """
        phases = self.phases_gpu.numpy()
        
        wx = self.world_x_gpu.numpy()
        wy = self.world_y_gpu.numpy()
        wz = self.world_z_gpu.numpy()
        
        world_positions = np.stack([wx, wy, wz], axis=-1)
        
        return phases, world_positions
    
    def destroy(self):
        """Free GPU resources."""
        self.y_positions_gpu = None
        self.velocities_x_gpu = None
        self.velocities_y_gpu = None
        self.velocities_z_gpu = None
        self.world_x_gpu = None
        self.world_y_gpu = None
        self.world_z_gpu = None
        self.phases_gpu = None
        self.ages_gpu = None
        self.release_timers_gpu = None
        self.tendroid_x_gpu = None
        self.tendroid_y_gpu = None
        self.tendroid_z_gpu = None
        self.tendroid_lengths_gpu = None
