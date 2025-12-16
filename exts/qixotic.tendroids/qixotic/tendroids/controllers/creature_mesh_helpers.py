"""
Creature Mesh Helpers - USD mesh creation for creature visualization

Separated from CreatureController for maintainability.
Handles body cylinder, nose cone, and material creation.
"""

from pxr import Gf, UsdGeom, UsdShade, Sdf


def create_creature_mesh(stage, creature_radius: float, creature_length: float):
    """
    Create creature mesh with body and nose cone.
    
    Args:
        stage: USD stage
        creature_radius: Cylinder/cone radius
        creature_length: Body cylinder length
    
    Returns:
        Tuple of (parent_prim, translate_op, rotate_op, initial_rotation)
    """
    parent_path = "/World/Creature"
    if stage.GetPrimAtPath(parent_path):
        stage.RemovePrim(parent_path)
    
    parent_xform = UsdGeom.Xform.Define(stage, parent_path)
    xformable = UsdGeom.Xformable(parent_xform)
    translate_op = xformable.AddTranslateOp()
    rotate_op = xformable.AddRotateXYZOp()
    
    initial_rotation = Gf.Vec3f(0, 90, 0)  # Start horizontal
    rotate_op.Set(initial_rotation)
    
    # Body cylinder
    body = UsdGeom.Cylinder.Define(stage, f"{parent_path}/Body")
    body.CreateRadiusAttr().Set(creature_radius)
    body.CreateHeightAttr().Set(creature_length)
    body.CreateAxisAttr().Set("Z")
    
    # Nose cone
    nose = UsdGeom.Cone.Define(stage, f"{parent_path}/Nose")
    nose.CreateRadiusAttr().Set(creature_radius)
    nose.CreateHeightAttr().Set(creature_radius * 2.0)
    nose.CreateAxisAttr().Set("Z")
    
    # Position nose at front
    nose_xform = UsdGeom.Xformable(nose)
    nose_translate = nose_xform.AddTranslateOp()
    nose_offset = (creature_length / 2.0) + creature_radius
    nose_translate.Set(Gf.Vec3d(0, 0, nose_offset))
    
    # Create and apply materials
    _apply_body_material(stage, body)
    _apply_nose_material(stage, nose)
    
    return parent_xform.GetPrim(), translate_op, rotate_op, initial_rotation


def _apply_body_material(stage, body_prim):
    """Apply cyan material to creature body."""
    mat_path = "/World/Materials/CreatureBody"
    material = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, f"{mat_path}/Surface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.2, 0.8, 0.9)  # Cyan
    )
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.3)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    UsdShade.MaterialBindingAPI(body_prim).Bind(material)


def _apply_nose_material(stage, nose_prim):
    """Apply orange material to creature nose."""
    mat_path = "/World/Materials/CreatureNose"
    material = UsdShade.Material.Define(stage, mat_path)
    shader = UsdShade.Shader.Define(stage, f"{mat_path}/Surface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(1.0, 0.5, 0.1)  # Orange
    )
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.2)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    UsdShade.MaterialBindingAPI(nose_prim).Bind(material)
