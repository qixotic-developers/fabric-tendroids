"""
V2 Warp Controller - GPU-accelerated bubble-guided deformation demo
"""

import carb
import omni.usd
import omni.kit.app

from .v2_warp_tendroid import V2WarpTendroid
from .v2_bubble import V2Bubble
from .v2_bubble_visual import V2BubbleVisual


class V2WarpController:
    """
    GPU-accelerated V2 controller using Warp kernels.
    """
    
    def __init__(self):
        self.tendroid = None
        self.bubble = None
        self._bubble_visual = None
        self._update_sub = None
        self._running = False
        self._stage = None
        
        self.cylinder_radius = 10.0
        self.cylinder_length = 200.0
        self.max_bubble_radius = 18.0
        self.bubble_rise_speed = 15.0
        self.starting_diameter_pct = 0.10
        self.max_diameter_pct = 0.40
        self.bulge_width = 0.9
    
    def start(self):
        """Start the demo."""
        ctx = omni.usd.get_context()
        if not ctx:
            carb.log_error("[V2WarpController] No USD context")
            return False
        
        self._stage = ctx.get_stage()
        if not self._stage:
            carb.log_error("[V2WarpController] No USD stage")
            return False
        
        self._setup_environment()
        self._create_components()
        self._start_update_loop()
        carb.log_info("[V2WarpController] GPU-accelerated demo started")
        return True
    
    def _setup_environment(self):
        """Setup lighting, sky, and sea floor."""
        try:
            from ..sea_floor.sea_floor_controller import SeaFloorController
            SeaFloorController.create_sea_floor(self._stage)
        except Exception as e:
            carb.log_warn(f"[V2WarpController] Environment setup failed: {e}")
    
    def _create_components(self):
        """Create Warp tendroid and bubble."""
        amplitude = (self.max_bubble_radius - self.cylinder_radius) / self.cylinder_radius
        
        self.tendroid = V2WarpTendroid(
            stage=self._stage, path="/World/V2_Tendroid",
            radius=self.cylinder_radius, length=self.cylinder_length,
            radial_segments=24, height_segments=48,
            max_amplitude=amplitude, bulge_width=self.bulge_width
        )
        
        self.bubble = V2Bubble(
            cylinder_radius=self.cylinder_radius,
            cylinder_length=self.cylinder_length,
            max_radius=self.max_bubble_radius,
            rise_speed=self.bubble_rise_speed,
            starting_diameter_pct=self.starting_diameter_pct,
            max_diameter_pct=self.max_diameter_pct
        )
        
        self._bubble_visual = V2BubbleVisual(self._stage)
        start_y = self.cylinder_length * self.starting_diameter_pct
        self._bubble_visual.create(self.cylinder_radius, start_y)
    
    def _start_update_loop(self):
        """Start per-frame updates."""
        self._running = True
        app = omni.kit.app.get_app()
        self._update_sub = app.get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="V2WarpController_Update"
        )
    
    def stop(self):
        """Stop animation."""
        self._running = False
        self._update_sub = None
        carb.log_info("[V2WarpController] Stopped")
    
    def clear(self):
        """Clear all objects."""
        self.stop()
        if self.tendroid:
            self.tendroid.destroy()
            self.tendroid = None
        if self._bubble_visual:
            self._bubble_visual.destroy()
            self._bubble_visual = None
        self.bubble = None
        carb.log_info("[V2WarpController] Cleared")
    
    def cleanup(self):
        self.clear()
    
    def reset_bubble(self):
        if self.bubble:
            self.bubble.reset()
    
    def _on_update(self, event):
        """Per-frame update."""
        if not self._running or not self.bubble:
            return
        
        dt = event.payload.get("dt", 1.0 / 60.0)
        
        still_active = self.bubble.update(dt)
        if not still_active:
            self.bubble.reset()
        
        current_radius = self.bubble.get_current_radius()
        
        if self._bubble_visual:
            self._bubble_visual.update(self.bubble.y, current_radius)
        
        if self.tendroid:
            self.tendroid.apply_deformation(self.bubble.y, current_radius)
