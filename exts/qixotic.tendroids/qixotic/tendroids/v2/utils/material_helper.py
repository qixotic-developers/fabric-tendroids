"""
V2 Material Helper - Creates and applies materials to V2 meshes
"""

import carb
from pxr import Gf, Sdf, UsdGeom, UsdShade


def apply_material(stage, mesh_prim):
    """
    Apply a material to the mesh, using existing Carpaint or creating fallback.
    
    Args:
        stage: USD stage
        mesh_prim: The mesh prim to apply material to
    """
    carpaint_path = "/World/Looks/Carpaint_02"
    material_prim = stage.GetPrimAtPath(carpaint_path)

    if material_prim.IsValid():
        material = UsdShade.Material(material_prim)
    else:
        material = _create_fallback_material(stage)

    UsdShade.MaterialBindingAPI(mesh_prim).Bind(material)


def _create_fallback_material(stage) -> UsdShade.Material:
    """Create a fallback material if Carpaint doesn't exist."""
    looks_path = "/World/Looks"
    if not stage.GetPrimAtPath(looks_path).IsValid():
        UsdGeom.Scope.Define(stage, looks_path)

    mat_path = "/World/Looks/V2_Tendroid_Mat"
    material = UsdShade.Material.Define(stage, mat_path)

    shader_path = f"{mat_path}/Shader"
    shader = UsdShade.Shader.Define(stage, shader_path)
    shader.CreateIdAttr("UsdPreviewSurface")

    # Coral/pink color
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.9, 0.4, 0.5)
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)

    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    
    carb.log_info(f"[V2Material] Created fallback material: {mat_path}")
    return material
