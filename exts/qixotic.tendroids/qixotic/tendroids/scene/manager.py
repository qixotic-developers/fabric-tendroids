"""
Scene manager for multiple Tendroids

Coordinates creation, placement, and lifecycle of all Tendroids in the scene.
"""

import carb
import omni.usd
from .tendroid_factory import TendroidFactory
from .animation_controller import AnimationController
from ..sea_floor.sea_floor_controller import SeaFloorController


class TendroidSceneManager:
    """
    High-level scene coordinator for Tendroids.
    
    Delegates creation to TendroidFactory and animation to AnimationController,
    focusing on scene-level concerns like cleanup and Tendroid collection management.
    """
    
    def __init__(self):
        """Initialize scene manager."""
        self.tendroids = []
        self.animation_controller = AnimationController()
        self._sea_floor_created = False
        
        carb.log_info("[TendroidSceneManager] Initialized")
    
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
                carb.log_info("[TendroidSceneManager] Sea floor created")
            except Exception as e:
                carb.log_error(
                    f"[TendroidSceneManager] Failed to create sea floor: {e}"
                )
                import traceback
                traceback.print_exc()
    
    def create_tendroids(
        self,
        count: int = 15,
        spawn_area: tuple = (200, 200),
        radius_range: tuple = (8, 12),
        num_segments: int = 16
    ) -> bool:
        """
        Create multiple Tendroids in the scene.
        
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
            
            # Clear existing Tendroids
            self.clear_tendroids(stage)
            
            # Create Tendroids using standard factory
            self.tendroids = TendroidFactory.create_batch(
                stage=stage,
                count=count,
                spawn_area=spawn_area,
                radius_range=radius_range,
                num_segments=num_segments
            )
            
            # Update animation controller
            self.animation_controller.set_tendroids(self.tendroids)
            
            carb.log_info(
                f"[TendroidSceneManager] Created {len(self.tendroids)} Tendroids"
            )
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
        Create a single Tendroid with custom parameters.
        
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
            
            # Clear existing Tendroids
            self.clear_tendroids(stage)
            
            # Use factory to create single
            tendroid = TendroidFactory.create_single(
                stage=stage,
                position=position,
                radius=radius,
                length=length,
                num_segments=num_segments,
                bulge_length_percent=bulge_length_percent,
                amplitude=amplitude,
                wave_speed=wave_speed,
                cycle_delay=cycle_delay
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
    
    def start_animation(self):
        """Start animating all Tendroids."""
        self.animation_controller.start()
    
    def stop_animation(self):
        """Stop animating all Tendroids."""
        self.animation_controller.stop()
    
    def clear_tendroids(self, stage=None):
        """
        Remove all Tendroids from the scene.
        
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
        
        self.tendroids.clear()
        self.animation_controller.set_tendroids([])
        carb.log_info("[TendroidSceneManager] Cleared all Tendroids")
    
    def get_tendroid_count(self) -> int:
        """Get the number of active Tendroids."""
        return len(self.tendroids)
    
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
        
        carb.log_info("[TendroidSceneManager] Shutdown complete")
