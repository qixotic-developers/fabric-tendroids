"""
Bubble geometry creation helpers

Handles USD sphere creation and material application.
"""

import carb
from pxr import Gf, UsdGeom, UsdShade, Sdf


def create_bubble_sphere(
  stage,
  prim_path: str,
  position: tuple,
  diameter: float,
  resolution: int,
  config
) -> bool:
  """
  Create a sphere prim for a bubble.
  
  Args:
      stage: USD stage
      prim_path: Path for new sphere
      position: (x, y, z) initial position
      diameter: Sphere diameter
      resolution: Sphere subdivision
      config: BubbleConfig instance
  
  Returns:
      Success status
  """
  try:
    # Create sphere with unit radius (will be scaled)
    sphere = UsdGeom.Sphere.Define(stage, prim_path)
    
    # Set unit radius - actual size comes from scale
    sphere.GetRadiusAttr().Set(1.0)
    
    # Set position and scale via transform
    xform = UsdGeom.Xformable(sphere)
    translate_op = xform.AddTranslateOp()
    translate_op.Set(Gf.Vec3d(*position))
    
    # Initial scale from diameter
    initial_scale = diameter / 2.0
    scale_op = xform.AddScaleOp()
    scale_op.Set(Gf.Vec3f(initial_scale, initial_scale, initial_scale))
    
    # Apply material
    _apply_bubble_material(stage, sphere.GetPrim(), config)
    
    if config.debug_logging:
      carb.log_info(
        f"[BubbleHelpers] Created sphere at '{prim_path}', "
        f"radius={radius:.2f}"
      )
    
    return True
  
  except Exception as e:
    carb.log_error(f"[BubbleHelpers] Failed to create sphere: {e}")
    return False


def _apply_bubble_material(stage, prim, config):
  """
  Apply simple material to bubble sphere.
  
  Args:
      stage: USD stage
      prim: Sphere prim
      config: BubbleConfig instance
  """
  try:
    # Create material path
    material_path = "/World/Looks/BubbleMaterial"
    
    # Check if material already exists
    if not stage.GetPrimAtPath(material_path):
      _create_bubble_material(stage, material_path, config)
    
    # Bind material to sphere
    UsdShade.MaterialBindingAPI(prim).Bind(
      UsdShade.Material(stage.GetPrimAtPath(material_path))
    )
  
  except Exception as e:
    carb.log_error(f"[BubbleHelpers] Failed to apply material: {e}")


def _create_bubble_material(stage, material_path: str, config):
  """
  Create reusable bubble material.
  
  Args:
      stage: USD stage
      material_path: Path for material
      config: BubbleConfig instance
  """
  try:
    # Ensure /World/Looks exists
    looks_path = "/World/Looks"
    if not stage.GetPrimAtPath(looks_path):
      UsdGeom.Scope.Define(stage, looks_path)
    
    # Create material
    material = UsdShade.Material.Define(stage, material_path)
    
    # Create shader
    shader_path = f"{material_path}/Shader"
    shader = UsdShade.Shader.Define(stage, shader_path)
    shader.CreateIdAttr("UsdPreviewSurface")
    
    # Set shader parameters
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
      Gf.Vec3f(*config.color)
    )
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(config.opacity)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(config.metallic)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(config.roughness)
    
    # Connect shader to material
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    
    carb.log_info(f"[BubbleHelpers] Created bubble material at '{material_path}'")
  
  except Exception as e:
    carb.log_error(f"[BubbleHelpers] Failed to create material: {e}")
