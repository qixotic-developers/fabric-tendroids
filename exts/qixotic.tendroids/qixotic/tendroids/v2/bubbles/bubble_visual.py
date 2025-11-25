"""
V2 Bubble Visual Helper - Manages the visual sphere representation

Uses mesh-based sphere with vertex-down orientation to eliminate
the "snap" artifact when bubbles exit the cylinder. The vertex-down
geometry creates a smooth tapered transition instead of a flat face.
"""

import carb
from pxr import UsdGeom, Gf

from .sphere_geometry_helper import create_sphere_mesh


class V2BubbleVisual:
    """
    Manages the visual USD mesh sphere that represents the bubble.
    
    Uses vertex-down sphere geometry for smooth exit transitions.
    Visual radius matches logic radius with small gap to cylinder wall.
    """
    
    def __init__(self, stage, path: str = "/World/V2_Bubble"):
        self._stage = stage
        self._path = path
        self._mesh = None
        self._translate_op = None
        self._scale_op = None
        self._visual_scale = 0.95  # 95% of logic radius for wall gap
        self._base_radius = 1.0   # Mesh created at this radius, scaled dynamically
        
    def create(self, initial_radius: float, start_y: float):
        """Create the visual bubble sphere with vertex-down orientation."""
        existing = self._stage.GetPrimAtPath(self._path)
        if existing.IsValid():
            self._stage.RemovePrim(self._path)
        
        self._base_radius = initial_radius
        visual_radius = initial_radius * self._visual_scale
        
        # Create mesh sphere with vertex pointing down (eliminates exit snap)
        self._mesh = create_sphere_mesh(
            stage=self._stage,
            path=self._path,
            radius=visual_radius,
            horizontal_segments=16,
            vertical_segments=10,
            vertex_down=True
        )
        
        # Apply bubble material appearance
        self._mesh.CreateDisplayColorAttr([(0.3, 0.6, 0.9)])
        self._mesh.CreateDisplayOpacityAttr([0.5])
        
        # Setup transform ops for position and dynamic scaling
        xform = UsdGeom.Xformable(self._mesh.GetPrim())
        xform.ClearXformOpOrder()
        self._translate_op = xform.AddTranslateOp()
        self._scale_op = xform.AddScaleOp()
        
        self._translate_op.Set(Gf.Vec3d(0.0, start_y, 0.0))
        self._scale_op.Set(Gf.Vec3f(1.0, 1.0, 1.0))
        
    def update(self, y_position: float, current_radius: float):
        """Update visual position and size via scale transform."""
        try:
            if self._translate_op:
                self._translate_op.Set(Gf.Vec3d(0.0, y_position, 0.0))
            
            if self._scale_op and self._base_radius > 0:
                # Scale relative to base radius for dynamic size changes
                scale_factor = (current_radius * self._visual_scale) / (self._base_radius * self._visual_scale)
                self._scale_op.Set(Gf.Vec3f(scale_factor, scale_factor, scale_factor))
                
        except Exception as e:
            carb.log_warn(f"[V2BubbleVisual] Update error: {e}")
    
    def get_prim(self):
        """Get the USD prim for the bubble mesh."""
        return self._mesh.GetPrim() if self._mesh else None
    
    def destroy(self):
        """Remove the visual from the stage."""
        if self._stage and self._path:
            prim = self._stage.GetPrimAtPath(self._path)
            if prim.IsValid():
                self._stage.RemovePrim(self._path)
        self._mesh = None
        self._translate_op = None
        self._scale_op = None
