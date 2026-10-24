"""
GPU Bubble Physics Integration Helper

Provides a drop-in replacement interface for CPU-based bubble physics.
Makes it easy to switch between CPU and GPU implementations.

Updated for full lifecycle support.
"""

from .bubble_gpu_manager import BubbleGPUManager


class BubblePhysicsAdapter:
    """
    Adapter that provides same interface as CPU bubble manager
    but uses GPU acceleration under the hood.
    
    Supports full lifecycle: spawn, rise, exit, release, pop, respawn.
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
    
    def register_tendroid(self, tendroid, config):
        """
        Register a tendroid and allocate GPU slot with full lifecycle config.
        
        Args:
            tendroid: Tendroid instance
            config: Bubble config with lifecycle parameters
        """
        if not self.use_gpu:
            return
        
        name = tendroid.name
        if name in self._name_to_id:
            return
        
        bubble_id = self._next_id
        self._name_to_id[name] = bubble_id
        self._id_to_name[bubble_id] = name
        self._next_id += 1
        
        # Calculate lifecycle parameters
        spawn_y = tendroid.get_spawn_height(config.spawn_height_pct)
        max_diameter_y = tendroid.length * config.max_diameter_pct
        max_radius = tendroid.radius * (1.0 + tendroid.deformer.max_amplitude)
        
        # Generate random pop height in configured range
        import random
        pop_height = tendroid.position[1] + tendroid.length + random.uniform(
            config.min_pop_height, config.max_pop_height
        )
        
        # Register with GPU manager
        if self.gpu_manager:
            self.gpu_manager.register_bubble(
                bubble_id=bubble_id,
                tendroid_position=tendroid.position,
                tendroid_length=tendroid.length,
                tendroid_radius=tendroid.radius,
                spawn_y=spawn_y,
                pop_height=pop_height,
                max_diameter_y=max_diameter_y,
                max_radius=max_radius
            )
    
    def update_gpu(self, dt: float, config, wave_state=None):
        """
        Update all bubbles on GPU in one batch.
        
        Args:
            dt: Delta time
            config: Bubble config with lifecycle parameters
            wave_state: Optional wave controller state dict
        """
        if not self.use_gpu or not self.gpu_manager:
            return
        
        self.gpu_manager.update_all(
            dt=dt,
            rise_speed=config.rise_speed,
            released_rise_speed=config.released_rise_speed,
            respawn_delay=config.respawn_delay,
            wave_state=wave_state,
            max_concurrent_active=config.max_concurrent_active
        )
    
    def get_bubble_positions(self) -> dict:
        """
        Get bubble world positions for all tendroids.
        
        Returns:
            Dict mapping tendroid_name -> (x, y, z) world position
        """
        if not self.use_gpu or not self.gpu_manager:
            return {}
        
        phases, world_positions, _ = self.gpu_manager.get_bubble_states()
        
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
        
        phases, _, _ = self.gpu_manager.get_bubble_states()
        
        phase_dict = {}
        for name, bubble_id in self._name_to_id.items():
            phase_dict[name] = int(phases[bubble_id])
        
        return phase_dict
    
    def get_bubble_radii(self) -> dict:
        """
        Get current bubble radii for all tendroids.
        
        Returns:
            Dict mapping tendroid_name -> radius
        """
        if not self.use_gpu or not self.gpu_manager:
            return {}
        
        radii = self.gpu_manager.get_bubble_radii()
        
        radii_dict = {}
        for name, bubble_id in self._name_to_id.items():
            radii_dict[name] = float(radii[bubble_id])
        
        return radii_dict
    
    def pop_bubble(self, tendroid_name: str):
        """
        Force a bubble to pop immediately.
        
        Args:
            tendroid_name: Name of tendroid whose bubble should pop
        """
        if not self.use_gpu or not self.gpu_manager:
            return
        
        bubble_id = self._name_to_id.get(tendroid_name)
        if bubble_id is None:
            return
        
        # Get current position for pop effect
        phases, world_positions, _ = self.gpu_manager.get_bubble_states()
        if phases[bubble_id] > 0:  # Only pop if active
            # Set phase to 4 (popped)
            current_y = world_positions[bubble_id][1]
            self.gpu_manager.update_bubble_state(bubble_id, current_y, 4)
    
    def cancel_bubble(self, tendroid_name: str):
        """
        Silently cancel a bubble (no pop effect).
        
        Sets bubble to idle state immediately without triggering
        pop particles or sound effects.
        
        Args:
            tendroid_name: Name of tendroid whose bubble should cancel
        """
        if not self.use_gpu or not self.gpu_manager:
            return
        
        bubble_id = self._name_to_id.get(tendroid_name)
        if bubble_id is None:
            return
        
        phases, world_positions, _ = self.gpu_manager.get_bubble_states()
        if phases[bubble_id] > 0:  # Only cancel if active
            # Set phase to 0 (idle) - no pop effect
            current_y = world_positions[bubble_id][1]
            self.gpu_manager.update_bubble_state(bubble_id, current_y, 0)
    
    def spawn_bubble(self, tendroid_name: str, tendroid, config):
        """
        Manually spawn a bubble for a specific tendroid.
        
        Args:
            tendroid_name: Name of tendroid
            tendroid: Tendroid instance
            config: Bubble config
        """
        if not self.use_gpu or not self.gpu_manager:
            return
        
        bubble_id = self._name_to_id.get(tendroid_name)
        if bubble_id is None:
            return
        
        spawn_y = tendroid.get_spawn_height(config.spawn_height_pct)
        self.gpu_manager.spawn_bubble(bubble_id, spawn_y, tendroid.radius)
    
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
        config: Bubble configuration with lifecycle parameters
        
    Returns:
        BubblePhysicsAdapter ready to use with full lifecycle support
    """
    adapter = BubblePhysicsAdapter(use_gpu=True, max_bubbles=len(tendroids) * 2)
    
    for tendroid in tendroids:
        adapter.register_tendroid(tendroid, config)
    
    return adapter
