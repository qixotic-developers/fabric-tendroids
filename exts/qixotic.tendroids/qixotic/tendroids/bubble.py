"""
Bubble Entity
Represents a single bubble with physics and lifecycle.
"""

from pxr import UsdGeom, Gf, Sdf
from .bubble_config import BubbleConfig
import random


class Bubble:
    """Individual bubble with physics simulation."""
    
    def __init__(self, bubble_id: int, tendroid_id: int, initial_position: Gf.Vec3d, 
                 stage, pop_time: float):
        """
        Initialize bubble.
        
        Args:
            bubble_id: Unique bubble identifier
            tendroid_id: Parent Tendroid ID
            initial_position: Starting world position
            stage: USD stage reference
            pop_time: Seconds until bubble pops
        """
        self.bubble_id = bubble_id
        self.tendroid_id = tendroid_id
        self.stage = stage
        self.position = Gf.Vec3d(initial_position)
        self.start_position = Gf.Vec3d(initial_position)
        self.age = 0.0
        self.pop_time = pop_time
        self.is_popped = False
        
        # Random bubble size (0.3 to 0.8 units)
        self.radius = random.uniform(0.3, 0.8)
        
        # Random drift direction
        self.drift_direction = Gf.Vec3d(
            random.uniform(-1, 1),
            0,
            random.uniform(-1, 1)
        )
        if self.drift_direction.GetLength() > 0:
            self.drift_direction.Normalize()
        
        # Create USD geometry
        self.prim_path = f"/World/Bubbles/Bubble_{bubble_id}"
        self._create_geometry()
        
    def _create_geometry(self):
        """Create sphere primitive for bubble."""
        sphere = UsdGeom.Sphere.Define(self.stage, self.prim_path)
        sphere.GetRadiusAttr().Set(self.radius)  # Use random radius
        
        # Set initial position
        sphere.AddTranslateOp().Set(self.position)
        
        # Create glass material
        self._apply_glass_material(sphere.GetPrim())
        
    def _apply_glass_material(self, prim):
        """Apply glass/transparent material to bubble."""
        from pxr import UsdShade
        
        material_path = Sdf.Path(f"{self.prim_path}/Material")
        material = UsdShade.Material.Define(self.stage, material_path)
        
        shader = UsdShade.Shader.Define(self.stage, material_path.AppendPath("Shader"))
        shader.CreateIdAttr("UsdPreviewSurface")
        
        # Glass properties
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.7, 0.9, 1.0))
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(BubbleConfig.BUBBLE_OPACITY)
        shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.33)
        
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        
        # Bind material
        UsdShade.MaterialBindingAPI(prim).Bind(material)
        
    def update(self, dt: float) -> bool:
        """
        Update bubble physics and position.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if bubble should continue, False if cleanup needed
        """
        self.age += dt
        
        # Check if time to pop
        if self.age >= self.pop_time and not self.is_popped:
            self.is_popped = True
            return False  # Signal for pop effect and cleanup
        
        # Rise with lateral drift
        rise = Gf.Vec3d(0, BubbleConfig.RISE_SPEED * dt, 0)
        drift = self.drift_direction * BubbleConfig.LATERAL_DRIFT * dt
        
        self.position += rise + drift
        
        # Update USD transform
        prim = self.stage.GetPrimAtPath(self.prim_path)
        if prim.IsValid():
            sphere = UsdGeom.Sphere(prim)
            sphere.GetPrim().GetAttribute("xformOp:translate").Set(self.position)
        
        # Check if exceeded max rise distance
        rise_distance = self.position[1] - self.start_position[1]
        if rise_distance > BubbleConfig.MAX_RISE_DISTANCE:
            return False
            
        return True
        
    def cleanup(self):
        """Remove bubble from USD stage."""
        prim = self.stage.GetPrimAtPath(self.prim_path)
        if prim.IsValid():
            self.stage.RemovePrim(self.prim_path)
