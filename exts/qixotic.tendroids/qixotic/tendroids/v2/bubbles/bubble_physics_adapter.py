"""
GPU Bubble Physics Integration Helper

Provides a drop-in replacement interface for CPU-based bubble physics.
Makes it easy to switch between CPU and GPU implementations.
"""

from .bubble_gpu_manager import BubbleGPUManager


class BubblePhysicsAdapter:
    """
    Adapter that provides same interface as CPU bubble manager
    but uses GPU acceleration under the hood.
    """
    
    def __init__(self, use_gpu: bool = True, max_bubbles: int = 100):
        """
        Args:
            use_gpu: Enable GPU acceleration
            max_bubbles: Maximum concurrent bubbles (GPU only)
        """
        self.use_gpu = use_gpu
        self.gpu_manager = None
        
        if use_gpu:
            self.gpu_manager = BubbleGPUManager(max_bubbles=max_bubbles)
        
        # Map tendroid names to bubble IDs
        self._name_to_id = {}
        self._id_to_name = {}
        self._next_id = 0
    
    def register_tendroid(self, tendroid):
        """Register a tendroid and allocate GPU slot."""
        if not self.use_gpu:
            return
        
        name = tendroid.name
        if name in self._name_to_id:
            return
        
        bubble_id = self._next_id
        self._name_to_id[name] = bubble_id
        self._id_to_name[bubble_id] = name
        self._next_id += 1
        
        # Register with GPU manager
        if self.gpu_manager:
            spawn_y = tendroid.get_spawn_height(0.10)  # Default spawn height
            self.gpu_manager.register_bubble(
                bubble_id=bubble_id,
                tendroid_position=tendroid.position,
                tendroid_length=tendroid.length,
                spawn_y=spawn_y
            )
    
    def update_gpu(self, dt: float, config, wave_state=None):
        """
        Update all bubbles on GPU in one batch.
        
        Args:
            dt: Delta time
            config: Bubble config with rise_speed, etc.
            wave_state: Optional wave controller state dict
        """
        if not self.use_gpu or not self.gpu_manager:
            return
        
        self.gpu_manager.update_all(
            dt=dt,
            rise_speed=config.rise_speed,
            released_rise_speed=config.released_rise_speed,
            spawn_height_pct=config.spawn_height_pct,
            wave_state=wave_state
        )
    
    def get_bubble_positions(self) -> dict:
        """
        Get bubble world positions for all tendroids.
        
        Returns:
            Dict mapping tendroid_name -> (x, y, z) world position
        """
        if not self.use_gpu or not self.gpu_manager:
            return {}
        
        phases, world_positions = self.gpu_manager.get_bubble_states()
        
        positions = {}
        for name, bubble_id in self._name_to_id.items():
            if phases[bubble_id] > 0:  # Active bubble
                positions[name] = tuple(world_positions[bubble_id])
        
        return positions
    
    def get_bubble_phases(self) -> dict:
        """
        Get bubble phases for all tendroids.
        
        Returns:
            Dict mapping tendroid_name -> phase (0=idle, 1=rising, etc.)
        """
        if not self.use_gpu or not self.gpu_manager:
            return {}
        
        phases, _ = self.gpu_manager.get_bubble_states()
        
        phase_dict = {}
        for name, bubble_id in self._name_to_id.items():
            phase_dict[name] = int(phases[bubble_id])
        
        return phase_dict
    
    def destroy(self):
        """Clean up GPU resources."""
        if self.gpu_manager:
            self.gpu_manager.destroy()
            self.gpu_manager = None


def create_gpu_bubble_system(tendroids: list, config) -> BubblePhysicsAdapter:
    """
    Factory function to create GPU-accelerated bubble system.
    
    Args:
        tendroids: List of tendroids
        config: Bubble configuration
        
    Returns:
        BubblePhysicsAdapter ready to use
    """
    adapter = BubblePhysicsAdapter(use_gpu=True, max_bubbles=len(tendroids) * 2)
    
    for tendroid in tendroids:
        adapter.register_tendroid(tendroid)
    
    return adapter
