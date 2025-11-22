"""
V2 Controller - Orchestrates bubble-guided deformation demo (CPU fallback)
"""

import carb
import omni.usd
import omni.kit.app

from .v2_tendroid import V2Tendroid
from .v2_bubble import V2Bubble
from .v2_deformer import V2Deformer
from .v2_bubble_visual import V2BubbleVisual


class V2Controller:
    """
    Controls the V2 bubble-guided deformation demo (CPU version).
    
    Bubble grows from cylinder diameter (no deformation) to max diameter
    (full deformation) over a configurable height range.
    """
    
    def __init__(self):
        """Initialize V2 controller."""
        self.tendroid = None
        self.bubble = None
        self.deformer = None
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
    
    def start(self):
        """Start the V2 demo."""
        ctx = omni.usd.get_context()
        if not ctx:
            carb.log_error("[V2Controller] No USD context")
            return False
        
        self._stage = ctx.get_stage()
        if not self._stage:
            carb.log_error("[V2Controller] No USD stage")
            return False
        
        self._setup_environment()
        self._create_components()
        self._start_update_loop()
        carb.log_info("[V2Controller] Demo started")
        return True
    
    def _setup_environment(self):
        """Setup lighting, sky, and sea floor."""
        try:
            from ..v1.sea_floor.sea_floor_controller import SeaFloorController
            SeaFloorController.create_sea_floor(self._stage)
        except Exception as e:
            carb.log_warn(f"[V2Controller] Environment setup failed: {e}")
    
    def _create_components(self):
        """Create tendroid, bubble, and deformer."""
        self.tendroid = V2Tendroid(
            stage=self._stage, path="/World/V2_Tendroid",
            radius=self.cylinder_radius, length=self.cylinder_length,
            radial_segments=24, height_segments=48
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
        
        amplitude = (self.max_bubble_radius - self.cylinder_radius) / self.cylinder_radius
        
        self.deformer = V2Deformer(
            cylinder_radius=self.cylinder_radius,
            cylinder_length=self.cylinder_length,
            max_bulge_amplitude=amplitude,
            bulge_width=1.2
        )
    
    def _start_update_loop(self):
        """Start the per-frame update subscription."""
        self._running = True
        app = omni.kit.app.get_app()
        self._update_sub = app.get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="V2Controller_Update"
        )
    
    def stop(self):
        """Stop the animation loop."""
        self._running = False
        self._update_sub = None
        carb.log_info("[V2Controller] Animation stopped")
    
    def clear(self):
        """Clear all V2 objects from the scene."""
        self.stop()
        if self.tendroid:
            self.tendroid.destroy()
            self.tendroid = None
        if self._bubble_visual:
            self._bubble_visual.destroy()
            self._bubble_visual = None
        self.bubble = None
        self.deformer = None
        carb.log_info("[V2Controller] Scene cleared")
    
    def cleanup(self):
        """Alias for clear()."""
        self.clear()
    
    def reset_bubble(self):
        """Reset bubble to start position."""
        if self.bubble:
            self.bubble.reset()
    
    def _on_update(self, event):
        """Per-frame update callback."""
        if not self._running or not self.bubble:
            return
        
        dt = event.payload.get("dt", 1.0 / 60.0)
        
        still_active = self.bubble.update(dt)
        if not still_active:
            self.bubble.reset()
        
        current_radius = self.bubble.get_current_radius()
        
        if self._bubble_visual:
            self._bubble_visual.update(self.bubble.y, current_radius)
        
        if self.tendroid and self.deformer:
            self.tendroid.apply_deformation(
                self.deformer, self.bubble.y, current_radius
            )
