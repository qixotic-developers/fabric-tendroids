"""
V2 Material Helper - Creates and applies materials to V2 meshes
"""

import carb
from pxr import Gf, Sdf, UsdGeom, UsdShade


def apply_material(stage, mesh_prim):
    """
    Apply coral/pink tendroid material to the mesh.
    
    Always creates consistent material for V2 tendroids.
    
    Args:
        stage: USD stage
        mesh_prim: The mesh prim to apply material to
    """
    material = _get_or_create_tendroid_material(stage)
    UsdShade.MaterialBindingAPI(mesh_prim).Bind(material)


def _get_or_create_tendroid_material(stage) -> UsdShade.Material:
    """Get existing V2 tendroid material or create it."""
    mat_path = "/World/Looks/V2_Tendroid_Mat"
    
    # Check if already exists
    mat_prim = stage.GetPrimAtPath(mat_path)
    if mat_prim.IsValid():
        return UsdShade.Material(mat_prim)
    
    # Ensure Looks scope exists
    looks_path = "/World/Looks"
    if not stage.GetPrimAtPath(looks_path).IsValid():
        UsdGeom.Scope.Define(stage, looks_path)
    
    # Create material
    material = UsdShade.Material.Define(stage, mat_path)
    
    shader_path = f"{mat_path}/Shader"
    shader = UsdShade.Shader.Define(stage, shader_path)
    shader.CreateIdAttr("UsdPreviewSurface")
    
    # Coral/pink color - the good one!
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.9, 0.4, 0.5)
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)
    
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    
    carb.log_info(f"[V2Material] Created tendroid material: {mat_path}")
    return material
