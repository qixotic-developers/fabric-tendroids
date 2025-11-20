"""
Enhanced scene manager with optional Warp GPU particle system

Extends the standard manager to support switching between particle systems.
"""

import carb
import omni.usd
from .tendroid_factory import TendroidFactory
from .animation_controller import AnimationController
from ..sea_floor.sea_floor_controller import SeaFloorController
from ..bubbles import BubbleManager, BubbleManagerEnhanced, BubbleConfig
from ..config import get_config_value


class TendroidSceneManager:
    """
    High-level scene coordinator for Tendroids and bubbles.
    
    Now supports optional Warp GPU particle system for improved performance.
    """
    
    def __init__(self, use_warp_particles: bool = None):
        """
        Initialize scene manager with bubble support.
        
        Args:
            use_warp_particles: Use Warp GPU particles if True, spheres if False,
                              auto-detect if None (tries Warp, falls back to spheres)
        """
        self.tendroids = []
        self.bubble_manager = None
        self.bubble_config = None
        self.use_warp_particles = use_warp_particles
        self.animation_controller = AnimationController()
        self._sea_floor_created = False
    
    def _ensure_sea_floor(self, stage):
        """
        Ensure sea floor exists in the stage.
        
        Args:
            stage: USD stage
        """
        if not self._sea_floor_created and stage:
            try:
                SeaFloorController.create_sea_floor(stage)
                self._sea_floor_created = True
            except Exception as e:
                carb.log_error(
                    f"[TendroidSceneManager] Failed to create sea floor: {e}"
                )
                import traceback
                traceback.print_exc()
    
    def _ensure_bubble_manager(self, stage):
        """
        Create bubble manager if bubble system is enabled.
        
        Args:
            stage: USD stage
        """
        if self.bubble_manager:
            return  # Already created
        
        # Check if bubble system is enabled
        enabled = get_config_value("bubble_system", "enabled", default=True)
        
        if not enabled:
            carb.log_info("[TendroidSceneManager] Bubble system disabled in config")
            return
        
        # Load bubble configuration from JSON
        bubble_config_dict = get_config_value("bubble_system", default={})
        self.bubble_config = BubbleConfig.from_json(bubble_config_dict)
        
        # Check if Warp particles are requested in config (override init param)
        if self.use_warp_particles is None:
            self.use_warp_particles = bubble_config_dict.get("use_warp_particles", False)
        
        # Create appropriate bubble manager
        if self.use_warp_particles:
            try:
                self.bubble_manager = BubbleManagerEnhanced(
                    stage, 
                    self.bubble_config,
                    use_warp_particles=True
                )
                carb.log_info("[TendroidSceneManager] Using Warp GPU particle system")
            except Exception as e:
                carb.log_error(f"[TendroidSceneManager] Failed to init Warp particles: {e}")
                carb.log_warn("[TendroidSceneManager] Falling back to sphere particles")
                self.bubble_manager = BubbleManager(stage, self.bubble_config)
                self.use_warp_particles = False
        else:
            # Use original sphere-based manager for compatibility
            self.bubble_manager = BubbleManager(stage, self.bubble_config)
            carb.log_info("[TendroidSceneManager] Using sphere-based particle system")
        
        # Wire up to animation controller
        self.animation_controller.set_bubble_manager(self.bubble_manager)
    
    def create_tendroids(
        self,
        count: int = 15,
        spawn_area: tuple = (200, 200),
        radius_range: tuple = (8, 12),
        num_segments: int = 16
    ) -> bool:
        """
        Create multiple Tendroids in the scene with bubble support.
        
        Args:
            count: Number of Tendroids to create
            spawn_area: (width, depth) of spawning area
            radius_range: (min, max) radius for random variation
            num_segments: Number of segments per Tendroid
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get USD context
            ctx = omni.usd.get_context()
            if not ctx:
                carb.log_error("[TendroidSceneManager] No USD context available")
                return False
            
            stage = ctx.get_stage()
            if not stage:
                carb.log_error("[TendroidSceneManager] No USD stage available")
                return False
            
            # Ensure sea floor exists before creating tendroids
            self._ensure_sea_floor(stage)
            
            # Ensure bubble manager exists
            self._ensure_bubble_manager(stage)
            
            # Clear existing Tendroids
            self.clear_tendroids(stage)
            
            # Create Tendroids using standard factory with bubble manager
            self.tendroids = TendroidFactory.create_batch(
                stage=stage,
                count=count,
                spawn_area=spawn_area,
                radius_range=radius_range,
                num_segments=num_segments,
                bubble_manager=self.bubble_manager
            )
            
            # Update animation controller
            self.animation_controller.set_tendroids(self.tendroids)
            
            return True
        
        except Exception as e:
            carb.log_error(f"[TendroidSceneManager] Failed to create Tendroids: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def create_single_tendroid(
        self,
        position: tuple = (0, 0, 0),
        radius: float = 10.0,
        length: float = 100.0,
        num_segments: int = 32,
        bulge_length_percent: float = 40.0,
        amplitude: float = 0.35,
        wave_speed: float = 40.0,
        cycle_delay: float = 2.0
    ) -> bool:
        """
        Create a single Tendroid with custom parameters and bubble support.
        
        Args:
            position: (x, y, z) world position
            radius: Cylinder radius
            length: Total length
            num_segments: Vertical resolution
            bulge_length_percent: Bulge size as % of length
            amplitude: Maximum radial expansion
            wave_speed: Wave travel speed
            cycle_delay: Pause between cycles
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get USD context
            ctx = omni.usd.get_context()
            if not ctx:
                carb.log_error("[TendroidSceneManager] No USD context available")
                return False
            
            stage = ctx.get_stage()
            if not stage:
                carb.log_error("[TendroidSceneManager] No USD stage available")
                return False
            
            # Ensure sea floor exists before creating tendroids
            self._ensure_sea_floor(stage)
            
            # Ensure bubble manager exists
            self._ensure_bubble_manager(stage)
            
            # Clear existing Tendroids
            self.clear_tendroids(stage)
            
            # Use factory to create single with bubble manager
            tendroid = TendroidFactory.create_single(
                stage=stage,
                position=position,
                radius=radius,
                length=length,
                num_segments=num_segments,
                bulge_length_percent=bulge_length_percent,
                amplitude=amplitude,
                wave_speed=wave_speed,
                cycle_delay=cycle_delay,
                bubble_manager=self.bubble_manager
            )
            
            if tendroid:
                self.tendroids = [tendroid]
                self.animation_controller.set_tendroids(self.tendroids)
                return True
            
            return False
        
        except Exception as e:
            carb.log_error(
                f"[TendroidSceneManager] Failed to create single Tendroid: {e}"
            )
            import traceback
            traceback.print_exc()
            return False
    
    def start_animation(self, enable_profiling: bool = False):
        """
        Start animating all Tendroids and bubbles.
        
        Args:
            enable_profiling: Enable periodic FPS logging (1s intervals)
        """
        self.animation_controller.start(enable_profiling=enable_profiling)
    
    def stop_animation(self):
        """Stop animating all Tendroids and bubbles."""
        self.animation_controller.stop()
    
    def get_profile_data(self):
        """
        Get performance profiling data from animation controller.
        
        Returns:
            Dict with profile data or None if profiling not enabled
        """
        return self.animation_controller.get_profile_data()
    
    def clear_tendroids(self, stage=None):
        """
        Remove all Tendroids and bubbles from the scene.
        
        Args:
            stage: USD stage (if None, will get current stage)
        """
        if not stage:
            ctx = omni.usd.get_context()
            if ctx:
                stage = ctx.get_stage()
        
        if stage:
            for tendroid in self.tendroids:
                tendroid.destroy(stage)
        
        # Clear all bubbles
        if self.bubble_manager:
            self.bubble_manager.clear_all_bubbles()
        
        self.tendroids.clear()
        self.animation_controller.set_tendroids([])
    
    def get_tendroid_count(self) -> int:
        """Get the number of active Tendroids."""
        return len(self.tendroids)
    
    def get_bubble_count(self) -> int:
        """Get the number of active bubbles."""
        if self.bubble_manager:
            return self.bubble_manager.get_bubble_count()
        return 0
    
    def get_particle_count(self) -> int:
        """Get the number of active pop particles."""
        if self.bubble_manager and hasattr(self.bubble_manager, 'get_particle_count'):
            return self.bubble_manager.get_particle_count()
        return 0
    
    def get_particle_system_type(self) -> str:
        """Get which particle system is being used."""
        if self.bubble_manager and hasattr(self.bubble_manager, 'get_particle_system_type'):
            return self.bubble_manager.get_particle_system_type()
        return "Sphere-based"
    
    def update_bubble_pop_timing(self, min_pop_time: float, max_pop_time: float):
        """
        Update bubble pop timing settings.
        
        Args:
            min_pop_time: Minimum time before bubble pops (seconds)
            max_pop_time: Maximum time before bubble pops (seconds)
        """
        if self.bubble_config:
            self.bubble_config.min_lifetime = min_pop_time
            self.bubble_config.max_lifetime = max_pop_time
            carb.log_info(f"[TendroidSceneManager] Updated pop timing: {min_pop_time:.1f}s - {max_pop_time:.1f}s")
        
        # Update bubble manager if it exists
        if self.bubble_manager:
            self.bubble_manager.config.min_lifetime = min_pop_time
            self.bubble_manager.config.max_lifetime = max_pop_time
    
    def set_all_active(self, active: bool):
        """Enable or disable animation for all Tendroids."""
        self.animation_controller.set_all_active(active)
    
    def shutdown(self):
        """Cleanup when shutting down."""
        self.animation_controller.shutdown()
        
        ctx = omni.usd.get_context()
        if ctx:
            stage = ctx.get_stage()
            if stage:
                self.clear_tendroids(stage)
        
        self.bubble_manager = None
