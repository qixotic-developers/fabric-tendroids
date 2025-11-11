"""
Sea floor USD controller

Handles USD mesh creation for contoured sea floor terrain.
"""

import carb
from pxr import Gf, Sdf, UsdGeom, UsdShade

from .sea_floor_config import SeaFloorConfig
from .sea_floor_helper import initialize_height_map
from ..scene.environment_config import EnvironmentConfig
from ..scene.environment_setup import EnvironmentSetup


class SeaFloorController:
  """Controller for creating sea floor USD geometry."""
  
  @staticmethod
  def create_sea_floor(stage, config: SeaFloorConfig = None) -> bool:
    """
    Create contoured sea floor mesh in USD stage.
    
    Args:
        stage: USD stage
        config: Configuration for terrain generation (uses JSON if None)
    
    Returns:
        True if successful, False otherwise
    """
    try:
      if config is None:
        config = SeaFloorConfig.from_json()
      
      # Generate height map
      initialize_height_map(config)
      
      # Import height map after it's been initialized
      from .sea_floor_helper import _height_map
      
      if _height_map is None:
        carb.log_error("[SeaFloorController] Height map generation failed")
        return False
      
      # Setup environment (Sky, DistantLight) - uses JSON config
      env_config = EnvironmentConfig.from_json()
      EnvironmentSetup.setup_environment(stage, env_config)
      
      # Ensure parent path exists
      parent_prim = stage.GetPrimAtPath(config.parent_path)
      if not parent_prim.IsValid():
        UsdGeom.Xform.Define(stage, config.parent_path)
      
      # Create mesh
      mesh_prim = UsdGeom.Mesh.Define(stage, config.mesh_path)
      
      # Build vertices with height variation
      vertices = SeaFloorController._build_vertices(config, _height_map)
      mesh_prim.CreatePointsAttr(vertices)
      
      # Build face topology (quads)
      face_counts, face_indices = SeaFloorController._build_faces(config)
      mesh_prim.CreateFaceVertexCountsAttr(face_counts)
      mesh_prim.CreateFaceVertexIndicesAttr(face_indices)
      
      # Build normals
      normals = SeaFloorController._build_normals(config, vertices)
      mesh_prim.CreateNormalsAttr(normals)
      mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
      
      # Build UVs
      uvs = SeaFloorController._build_uvs(config)
      primvar_api = UsdGeom.PrimvarsAPI(mesh_prim)
      uv_primvar = primvar_api.CreatePrimvar(
        "st",
        Sdf.ValueTypeNames.TexCoord2fArray,
        UsdGeom.Tokens.vertex
      )
      uv_primvar.Set(uvs)
      
      # Compute extent
      extent = UsdGeom.PointBased(mesh_prim).ComputeExtent(vertices)
      mesh_prim.CreateExtentAttr(extent)
      
      # Set subdivision
      mesh_prim.CreateSubdivisionSchemeAttr("none")
      
      # Apply material
      material = EnvironmentSetup.get_sea_floor_material(
        stage, 
        env_config.sea_floor_material
      )
      UsdShade.MaterialBindingAPI(mesh_prim).Bind(material)
      
      carb.log_info(
        f"[SeaFloorController] Created sea floor: {config.mesh_path}, "
        f"{len(vertices)} vertices, {len(face_counts)} faces"
      )
      
      return True
      
    except Exception as e:
      carb.log_error(f"[SeaFloorController] Failed to create sea floor: {e}")
      import traceback
      traceback.print_exc()
      return False
  
  @staticmethod
  def _build_vertices(config: SeaFloorConfig, height_map) -> list:
    """Build vertex positions with height map."""
    if height_map is None:
      raise ValueError("Height map cannot be None")
    
    vertices = []
    half_width = config.width / 2.0
    half_depth = config.depth / 2.0
    
    for y_idx in range(config.resolution_y + 1):
      for x_idx in range(config.resolution_x + 1):
        x = -half_width + (x_idx * config.grid_spacing_x)
        z = -half_depth + (y_idx * config.grid_spacing_y)
        y = height_map[y_idx, x_idx]
        
        vertices.append(Gf.Vec3f(x, y, z))
    
    return vertices
  
  @staticmethod
  def _build_faces(config: SeaFloorConfig) -> tuple:
    """Build face topology (quads)."""
    face_counts = []
    face_indices = []
    
    cols = config.resolution_x + 1
    
    for y_idx in range(config.resolution_y):
      for x_idx in range(config.resolution_x):
        # Quad corners (counter-clockwise)
        i0 = y_idx * cols + x_idx
        i1 = i0 + 1
        i2 = i0 + cols + 1
        i3 = i0 + cols
        
        face_counts.append(4)
        face_indices.extend([i0, i1, i2, i3])
    
    return face_counts, face_indices
  
  @staticmethod
  def _build_normals(config: SeaFloorConfig, vertices: list) -> list:
    """Build vertex normals (simple upward for now)."""
    # For simplicity, use upward normals
    # Could be enhanced to compute actual surface normals
    return [Gf.Vec3f(0, 1, 0) for _ in vertices]
  
  @staticmethod
  def _build_uvs(config: SeaFloorConfig) -> list:
    """Build UV coordinates."""
    uvs = []
    scale_x = 8.0
    scale_y = 8.0
    
    for y_idx in range(config.resolution_y + 1):
      v = (y_idx / config.resolution_y) * scale_y
      for x_idx in range(config.resolution_x + 1):
        u = (x_idx / config.resolution_x) * scale_x
        uvs.append(Gf.Vec2f(u, v))
    
    return uvs
