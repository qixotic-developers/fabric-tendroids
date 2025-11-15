"""
Vertex deformation helper using FastMeshUpdater

Bridges Warp GPU deformation with C++ high-performance mesh updates.
"""

import carb
import numpy as np
from typing import Optional


class VertexDeformHelper:
  """
  Manages vertex deformation animation using FastMeshUpdater.
  
  Workflow:
  1. WarpDeformer generates deformed vertices on GPU
  2. Convert Gf.Vec3f list to numpy array
  3. FastMeshUpdater writes directly to USD mesh (bypassing Python overhead)
  
  This avoids the tuple conversion bottleneck from Phase 1.
  
  NOTE: Current FastMeshUpdater C++ extension only has compute_tube_vertices()
  and batch_compute_vertices(). The USD mesh update methods (attach_stage,
  register_mesh, etc.) are not yet implemented. This class gracefully falls
  back when those methods are unavailable.
  """
  
  def __init__(self, mesh_path: str):
    """
    Initialize deformation helper.
    
    Args:
        mesh_path: USD prim path to mesh (e.g., "/World/Tendroids/tendroid_001/Mesh")
    """
    self.mesh_path = mesh_path
    self.updater: Optional[object] = None  # FastMeshUpdater instance
    self._initialized = False
    
    carb.log_info(f"[VertexDeformHelper] Created for '{mesh_path}'")
  
  def initialize(self, stage_id: int, fast_mesh_updater) -> bool:
    """
    Attach to USD stage and register mesh.
    
    Args:
        stage_id: Stage pointer as integer from omni.usd.get_context().get_stage_id()
        fast_mesh_updater: FastMeshUpdater C++ instance
    
    Returns:
        True if initialization successful
    """
    try:
      self.updater = fast_mesh_updater
      
      # Check if FastMeshUpdater has USD mesh update methods
      # Current version only has compute methods, not USD integration
      if not hasattr(self.updater, 'is_stage_attached'):
        carb.log_warn(
          f"[VertexDeformHelper] FastMeshUpdater missing USD mesh methods\n"
          f"  Current version only supports compute_tube_vertices() and batch_compute_vertices()\n"
          f"  Vertex deformation helper cannot be used - Tendroid will fall back to Python"
        )
        return False
      
      # Attach to stage (may already be attached, that's fine)
      if not self.updater.is_stage_attached():
        if not self.updater.attach_stage(stage_id):
          carb.log_error(f"[VertexDeformHelper] Failed to attach stage")
          return False
      
      # Register this mesh
      if not self.updater.register_mesh(self.mesh_path):
        carb.log_error(f"[VertexDeformHelper] Failed to register mesh '{self.mesh_path}'")
        return False
      
      self._initialized = True
      carb.log_info(
        f"[VertexDeformHelper] Initialized successfully for '{self.mesh_path}' "
        f"(total meshes: {self.updater.get_mesh_count()})"
      )
      return True
    
    except AttributeError as e:
      # Missing method - FastMeshUpdater version doesn't support USD integration yet
      carb.log_warn(
        f"[VertexDeformHelper] FastMeshUpdater method not available: {e}\n"
        f"  Vertex deformation helper cannot be used - falling back to Python"
      )
      return False
    
    except Exception as e:
      carb.log_error(f"[VertexDeformHelper] Initialization failed: {e}")
      return False
  
  def update_vertices(self, deformed_vertices: list) -> bool:
    """
    Update mesh with deformed vertices via FastMeshUpdater.
    
    Args:
        deformed_vertices: List of Gf.Vec3f deformed positions from WarpDeformer
    
    Returns:
        True if update successful
    """
    if not self._initialized or not self.updater:
      return False
    
    try:
      # Convert Gf.Vec3f list to numpy array (minimal overhead)
      # Shape: (N, 3) where N is vertex count
      vertices_np = np.array(
        [[v[0], v[1], v[2]] for v in deformed_vertices],
        dtype=np.float32
      )
      
      # FastMeshUpdater.update_mesh_vertices uses zero-copy numpy buffer protocol
      return self.updater.update_mesh_vertices(self.mesh_path, vertices_np)
    
    except Exception as e:
      carb.log_warn(f"[VertexDeformHelper] Update failed: {e}")
      return False
  
  def cleanup(self):
    """Release resources."""
    self._initialized = False
    self.updater = None
  
  def is_initialized(self) -> bool:
    """Check if helper is ready for updates."""
    return self._initialized
