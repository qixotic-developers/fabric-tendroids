"""
Bubble material helper - Creates proper transparent USD materials
"""

from pxr import Sdf, UsdShade, Gf


def create_transparent_bubble_material(
    stage,
    material_path: str,
    color: tuple = (0.7, 0.9, 1.0),
    opacity: float = 0.25,
    metallic: float = 0.0,
    roughness: float = 0.1
):
    """
    Create a proper transparent material for bubbles.
    
    Uses UsdPreviewSurface with opacity input for real transparency.
    
    Args:
        stage: USD stage
        material_path: Path for the material prim
        color: RGB color tuple (0-1 range)
        opacity: Opacity value (0=transparent, 1=opaque)
        metallic: Metallic value (0-1)
        roughness: Roughness value (0-1)
    
    Returns:
        UsdShade.Material prim
    """
    # Create material
    material = UsdShade.Material.Define(stage, material_path)
    
    # Create PreviewSurface shader
    shader = UsdShade.Shader.Define(stage, f"{material_path}/Shader")
    shader.CreateIdAttr("UsdPreviewSurface")
    
    # Set shader inputs
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*color))
    shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(opacity)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("opacityThreshold", Sdf.ValueTypeNames.Float).Set(0.0)  # Enable transparency
    
    # Connect shader to material outputs
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    
    return material


def apply_bubble_material(mesh_prim, material):
    """
    Apply a material to a mesh prim.
    
    Args:
        mesh_prim: USD mesh prim
        material: UsdShade.Material to apply
    """
    from pxr import UsdShade
    
    binding_api = UsdShade.MaterialBindingAPI(mesh_prim)
    binding_api.Bind(material)
