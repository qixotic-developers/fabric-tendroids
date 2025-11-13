"""
Batch Geometry Builder

Creates shared base mesh for instanced geometry with uniform diameter.
Optimized for batch GPU processing of multiple identical tubes.
"""

import math
import carb
from pxr import Gf, UsdGeom, Vt


class BatchGeometryBuilder:
  """
  Builds shared base mesh for batch processing.
  
  Creates single mesh topology that can be instanced and deformed
  in parallel for multiple tubes with identical diameter.
  """
  
  def __init__(self, stage):
    """
    Initialize builder with USD stage.
    
    Args:
        stage: USD stage for geometry creation
    """
    self.stage = stage
  
  def create_shared_tube(
    self,
    path: str,
    height: float = 5.0,
    radius: float = 0.5,
    height_segments: int = 16,
    radial_segments: int = 32
  ) -> tuple:
    """
    Create shared tube mesh with flared base.
    
    This is the base geometry that all tubes will share.
    Only position/rotation differ per instance.
    
    Args:
        path: USD prim path for base mesh
        height: Total tube height
        radius: Cylinder radius (uniform for all tubes)
        height_segments: Vertical resolution
        radial_segments: Circumferential resolution
    
    Returns:
        Tuple of (mesh_prim, vertex_positions, vertex_count)
    """
    mesh = UsdGeom.Mesh.Define(self.stage, path)
    
    # Generate vertices with flared base (15% height, 2x radius)
    flare_height = height * 0.15
    flare_radius = radius * 2.0
    
    positions = []
    segment_height = height / height_segments
    
    for seg in range(height_segments + 1):
      y = seg * segment_height
      
      # Calculate radius at this height (flare taper)
      if y <= flare_height:
        t = y / flare_height
        current_radius = flare_radius - (flare_radius - radius) * t
      else:
        current_radius = radius
      
      # Generate ring of vertices
      for rad in range(radial_segments):
        angle = (rad / radial_segments) * 2.0 * math.pi
        x = current_radius * math.cos(angle)
        z = current_radius * math.sin(angle)
        positions.append(Gf.Vec3f(x, y, z))
    
    vertex_count = len(positions)
    
    # Generate face connectivity (quads)
    face_vertex_counts = []
    face_vertex_indices = []
    
    for seg in range(height_segments):
      for rad in range(radial_segments):
        next_rad = (rad + 1) % radial_segments
        
        # Quad vertices (counter-clockwise)
        v0 = seg * radial_segments + rad
        v1 = seg * radial_segments + next_rad
        v2 = (seg + 1) * radial_segments + next_rad
        v3 = (seg + 1) * radial_segments + rad
        
        face_vertex_counts.append(4)
        face_vertex_indices.extend([v0, v1, v2, v3])
    
    # Set mesh attributes
    mesh.GetPointsAttr().Set(Vt.Vec3fArray(positions))
    mesh.GetFaceVertexCountsAttr().Set(Vt.IntArray(face_vertex_counts))
    mesh.GetFaceVertexIndicesAttr().Set(Vt.IntArray(face_vertex_indices))
    
    carb.log_info(
      f"[BatchGeometryBuilder] Created shared tube: "
      f"{vertex_count} vertices, {len(face_vertex_counts)} faces, "
      f"radius={radius:.2f}, height={height:.1f}"
    )
    
    return mesh.GetPrim(), positions, vertex_count
  
  def create_tube_instance(
    self,
    base_path: str,
    instance_name: str,
    position: tuple,
    rotation_y: float = 0.0
  ) -> str:
    """
    Create positioned instance referencing shared geometry.
    
    Args:
        base_path: Path to shared base mesh
        instance_name: Unique name for this instance
        position: (x, y, z) world position
        rotation_y: Y-axis rotation in degrees
    
    Returns:
        Instance prim path
    """
    instance_path = f"/World/BatchTest/Instances/{instance_name}"
    
    # Create Xform for instance
    xform = UsdGeom.Xform.Define(self.stage, instance_path)
    xform_prim = xform.GetPrim()
    
    # Set transform
    xform.AddTranslateOp().Set(Gf.Vec3d(*position))
    if rotation_y != 0.0:
      xform.AddRotateYOp().Set(rotation_y)
    
    # Add reference to shared mesh
    xform_prim.GetReferences().AddReference(assetPath="", primPath=base_path)
    
    return instance_path
