"""
POC Controller - Orchestrates bubble-guided deformation demo

Manages the tendroid, bubble, and deformer to demonstrate
the concept of bubble-driven cylinder deformation.
"""

import carb
import omni.usd
import omni.kit.app
from pxr import Usd, UsdGeom, Gf

from .poc_tendroid import POCTendroid
from .poc_bubble import POCBubble
from .poc_deformer import POCDeformer


class POCController:
    """
    Controls the proof-of-concept bubble-guided deformation demo.
    
    Creates a single tendroid with a rising bubble that drives
    the deformation bulge position.
    """
    
    def __init__(self):
        """Initialize POC controller."""
        self.tendroid = None
        self.bubble = None
        self.deformer = None
        self.bubble_prim = None
        self._bubble_translate_op = None
        
        self._update_sub = None
        self._running = False
        self._stage = None
        
        # Configuration - bubble size relative to cylinder
        self.cylinder_radius = 10.0
        self.cylinder_length = 200.0   # Cylinder height
        self.bubble_radius = 8.0
        self.bubble_rise_speed = 15.0
        
        carb.log_info("[POCController] Initialized")
    
    def start(self):
        """Start the POC demo."""
        ctx = omni.usd.get_context()
        if not ctx:
            carb.log_error("[POCController] No USD context")
            return False
        
        self._stage = ctx.get_stage()
        if not self._stage:
            carb.log_error("[POCController] No USD stage")
            return False
        
        # Setup environment first (lighting, sky, sea floor)
        self._setup_environment()
        
        # Create components
        self._create_tendroid()
        self._create_bubble()
        self._create_deformer()
        
        # Start update loop
        self._running = True
        app = omni.kit.app.get_app()
        self._update_sub = app.get_update_event_stream().create_subscription_to_pop(
            self._on_update,
            name="POCController_Update"
        )
        
        carb.log_info("[POCController] Demo started")
        return True
    
    def _setup_environment(self):
        """Setup lighting, sky, and sea floor."""
        try:
            from ..sea_floor.sea_floor_controller import SeaFloorController
            SeaFloorController.create_sea_floor(self._stage)
            carb.log_info("[POCController] Environment setup complete")
        except Exception as e:
            carb.log_warn(f"[POCController] Environment setup failed: {e}")
    
    def stop(self):
        """Stop the animation loop."""
        self._running = False
        if self._update_sub:
            self._update_sub = None
        carb.log_info("[POCController] Animation stopped")
    
    def clear(self):
        """Clear all POC objects from the scene."""
        self.stop()
        
        if self._stage:
            if self.tendroid:
                self.tendroid.destroy()
                self.tendroid = None
            if self.bubble_prim:
                self._stage.RemovePrim(self.bubble_prim.GetPath())
                self.bubble_prim = None
        
        self.bubble = None
        self.deformer = None
        self._bubble_translate_op = None
        carb.log_info("[POCController] Scene cleared")
    
    def cleanup(self):
        """Alias for clear()."""
        self.clear()
    
    def reset_bubble(self):
        """Reset bubble to start position."""
        if self.bubble:
            self.bubble.reset()
            carb.log_info("[POCController] Bubble reset")

    def _create_tendroid(self):
        """Create the POC tendroid mesh."""
        self.tendroid = POCTendroid(
            stage=self._stage,
            path="/World/POC_Tendroid",
            radius=self.cylinder_radius,
            length=self.cylinder_length,
            radial_segments=24,
            height_segments=48
        )
    
    def _create_bubble(self):
        """Create the bubble and its visual representation."""
        # Exit distance - bubble needs to travel far enough past cylinder top
        # for Gaussian deformation to fully dissipate (3 sigma rule)
        bulge_width = 2.0  # matches deformer setting
        exit_distance = self.bubble_radius * bulge_width * 3  # ~3 sigma
        
        # Logic bubble (drives deformation)
        self.bubble = POCBubble(
            start_y=self.bubble_radius,
            radius=self.bubble_radius,
            rise_speed=self.bubble_rise_speed,
            cylinder_length=self.cylinder_length,
            exit_distance=exit_distance
        )
        
        # Visual sphere - should fill the deformed cylinder space
        deformed_radius = self.cylinder_radius * (1.0 + 0.8)  # 18
        visual_radius = deformed_radius * 0.85  # ~15, leaves gap to wall
        self._visual_bubble_radius = visual_radius
        
        bubble_path = "/World/POC_Bubble"
        
        existing = self._stage.GetPrimAtPath(bubble_path)
        if existing.IsValid():
            self._stage.RemovePrim(bubble_path)
        
        sphere = UsdGeom.Sphere.Define(self._stage, bubble_path)
        sphere.CreateRadiusAttr(visual_radius)
        
        # Translucent blue
        sphere.CreateDisplayColorAttr([(0.3, 0.6, 0.9)])
        sphere.CreateDisplayOpacityAttr([0.5])
        
        xform = UsdGeom.Xformable(sphere.GetPrim())
        xform.ClearXformOpOrder()
        self._bubble_translate_op = xform.AddTranslateOp()
        self._bubble_translate_op.Set(Gf.Vec3d(0.0, visual_radius, 0.0))
        
        # Update start position in logic bubble
        self.bubble.y = visual_radius
        
        self.bubble_prim = sphere.GetPrim()
        carb.log_info(
            f"[POCController] Visual bubble r={visual_radius:.1f}, "
            f"exit_dist={exit_distance:.1f}"
        )
    
    def _create_deformer(self):
        """Create the deformer with settings tuned to bubble size."""
        # Amplitude: how much the cylinder expands at maximum
        # 0.8 = 80% expansion, so radius 10 becomes 18 at peak
        amplitude = 0.8
        
        # Bulge width controls how far the deformation spreads
        # 2.0 gives smooth natural-looking transitions
        bulge_width = 2.0
        
        self.deformer = POCDeformer(
            cylinder_radius=self.cylinder_radius,
            cylinder_length=self.cylinder_length,
            max_bulge_amplitude=amplitude,
            bulge_width=bulge_width,
            visual_bubble_radius=self._visual_bubble_radius
        )
        carb.log_info(
            f"[POCController] Deformer: amplitude={amplitude:.0%}, "
            f"bulge_width={bulge_width}"
        )
    
    def _on_update(self, event):
        """Per-frame update callback."""
        if not self._running:
            return
        
        dt = event.payload.get("dt", 1.0 / 60.0)
        
        if self.bubble:
            still_active = self.bubble.update(dt)
            
            if not still_active:
                self.bubble.reset()
            
            # Update visual FIRST
            self._update_bubble_visual()
            
            # Then apply deformation at SAME position
            if self.tendroid and self.deformer:
                bubble_y = self.bubble.y
                self.tendroid.apply_deformation(
                    self.deformer,
                    bubble_y,
                    self.bubble.radius
                )
                
                # Debug: log positions periodically
                if int(bubble_y) % 20 == 0:
                    carb.log_info(f"[POC] Bubble Y={bubble_y:.1f}, radius={self.bubble.radius}")
    
    def _update_bubble_visual(self):
        """Update the visual sphere position to match bubble Y position."""
        if not self.bubble:
            return
        
        try:
            if self._bubble_translate_op:
                self._bubble_translate_op.Set(Gf.Vec3d(0.0, self.bubble.y, 0.0))
        except Exception as e:
            carb.log_warn(f"[POCController] Bubble visual update error: {e}")
