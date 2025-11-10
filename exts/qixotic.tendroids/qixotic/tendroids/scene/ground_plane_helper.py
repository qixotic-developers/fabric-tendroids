"""
Ground plane setup helper for Tendroid environment

Creates and configures ground plane geometry.
"""

import carb
from pxr import UsdGeom, Gf, Sdf


def setup_ground_plane(
  stage,
  plane_path: str = "/Environment/surface",
  texture_scale: tuple = (8.0, 8.0),
  size: float = 1000.0
) -> bool:
  """
  Create ground plane with UV coordinates ready for material binding.
  
  Args:
      stage: USD stage
      plane_path: Path for ground plane mesh
      texture_scale: (X, Y) texture coordinate scaling for future materials
      size: Size of the ground plane
  
  Returns:
      True if successful, False otherwise
  """
  try:
    # Ensure parent path exists
    parent_path = plane_path.rsplit('/', 1)[0]
    parent_prim = stage.GetPrimAtPath(parent_path)
    if not parent_prim.IsValid():
      UsdGeom.Xform.Define(stage, parent_path)
      carb.log_info(f"[GroundPlane] Created parent: {parent_path}")
    
    # Create ground plane mesh
    plane = UsdGeom.Mesh.Define(stage, plane_path)
    
    # Define quad vertices (centered at origin, XZ plane)
    half_size = size / 2.0
    vertices = [
      Gf.Vec3f(-half_size, 0, -half_size),
      Gf.Vec3f(half_size, 0, -half_size),
      Gf.Vec3f(half_size, 0, half_size),
      Gf.Vec3f(-half_size, 0, half_size)
    ]
    
    plane.CreatePointsAttr(vertices)
    
    # Define face (single quad)
    plane.CreateFaceVertexCountsAttr([4])
    plane.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    
    # Define normals (pointing up)
    normals = [Gf.Vec3f(0, 1, 0)] * 4
    plane.CreateNormalsAttr(normals)
    plane.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
    
    # Define UVs with texture scaling (ready for future material)
    scale_x, scale_y = texture_scale
    uvs = [
      Gf.Vec2f(0, 0),
      Gf.Vec2f(scale_x, 0),
      Gf.Vec2f(scale_x, scale_y),
      Gf.Vec2f(0, scale_y)
    ]
    
    primvar_api = UsdGeom.PrimvarsAPI(plane)
    uv_primvar = primvar_api.CreatePrimvar(
      "st",
      Sdf.ValueTypeNames.TexCoord2fArray,
      UsdGeom.Tokens.vertex
    )
    uv_primvar.Set(uvs)
    uv_primvar.SetIndices([0, 1, 2, 3])
    
    # Compute extent
    extent = UsdGeom.PointBased(plane).ComputeExtent(vertices)
    plane.CreateExtentAttr(extent)
    
    # Set subdivision
    plane.CreateSubdivisionSchemeAttr("none")
    
    carb.log_info(
      f"[GroundPlane] Created plane: {plane_path}, "
      f"size={size}, UV scale=({scale_x}, {scale_y})"
    )
    
    return True
    
  except Exception as e:
    carb.log_error(f"[GroundPlane] Failed to create ground plane: {e}")
    import traceback
    traceback.print_exc()
    return False
