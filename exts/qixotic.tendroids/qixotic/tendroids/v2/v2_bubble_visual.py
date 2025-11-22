"""
V2 Bubble Visual Helper - Manages the visual sphere representation
"""

import carb
from pxr import UsdGeom, Gf


class V2BubbleVisual:
    """
    Manages the visual USD sphere that represents the bubble.
    Visual radius matches logic radius with small gap to cylinder wall.
    """
    
    def __init__(self, stage, path: str = "/World/V2_Bubble"):
        self._stage = stage
        self._path = path
        self._sphere = None
        self._translate_op = None
        self._visual_scale = 0.95  # 95% of logic radius for wall gap
        
    def create(self, initial_radius: float, start_y: float):
        """Create the visual bubble sphere."""
        existing = self._stage.GetPrimAtPath(self._path)
        if existing.IsValid():
            self._stage.RemovePrim(self._path)
        
        visual_radius = initial_radius * self._visual_scale
        
        self._sphere = UsdGeom.Sphere.Define(self._stage, self._path)
        self._sphere.CreateRadiusAttr(visual_radius)
        self._sphere.CreateDisplayColorAttr([(0.3, 0.6, 0.9)])
        self._sphere.CreateDisplayOpacityAttr([0.5])
        
        xform = UsdGeom.Xformable(self._sphere.GetPrim())
        xform.ClearXformOpOrder()
        self._translate_op = xform.AddTranslateOp()
        self._translate_op.Set(Gf.Vec3d(0.0, start_y, 0.0))
        
    def update(self, y_position: float, current_radius: float):
        """Update visual position and size."""
        try:
            if self._translate_op:
                self._translate_op.Set(Gf.Vec3d(0.0, y_position, 0.0))
            
            if self._sphere:
                visual_radius = current_radius * self._visual_scale
                self._sphere.GetRadiusAttr().Set(visual_radius)
                
        except Exception as e:
            carb.log_warn(f"[V2BubbleVisual] Update error: {e}")
    
    def get_prim(self):
        """Get the USD prim for the bubble sphere."""
        return self._sphere.GetPrim() if self._sphere else None
    
    def destroy(self):
        """Remove the visual from the stage."""
        if self._stage and self._path:
            prim = self._stage.GetPrimAtPath(self._path)
            if prim.IsValid():
                self._stage.RemovePrim(self._path)
        self._sphere = None
        self._translate_op = None
