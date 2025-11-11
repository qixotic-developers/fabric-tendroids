"""
USD mesh vertex updater for Tendroid

Handles writing deformed vertices to USD mesh efficiently.
"""

import carb
from pxr import UsdGeom, Vt, Gf


class MeshVertexUpdater:
  """
  Manages USD mesh vertex updates for deformation animation.
  
  Provides optimized vertex writing to USD mesh points attribute.
  Handles error cases gracefully to prevent animation crashes.
  """
  
  def __init__(self, mesh_prim):
    """
    Initialize mesh updater.
    
    Args:
        mesh_prim: USD mesh prim to update
    """
    self.mesh_prim = mesh_prim
    self.mesh = UsdGeom.Mesh(mesh_prim)
    self.points_attr = self.mesh.GetPointsAttr()
    
    # Validate
    if not self.points_attr:
      carb.log_error("[MeshVertexUpdater] Failed to get points attribute")
  
  def update_vertices(self, vertices: list) -> bool:
    """
    Write deformed vertices to USD mesh.
    
    Args:
        vertices: List of Gf.Vec3f positions
    
    Returns:
        True if update successful, False otherwise
    """
    if not self.points_attr:
      return False
    
    try:
      self.points_attr.Set(Vt.Vec3fArray(vertices))
      return True
    except Exception as e:
      carb.log_warn(f"[MeshVertexUpdater] Vertex update failed: {e}")
      return False
  
  def is_valid(self) -> bool:
    """Check if updater has valid mesh reference."""
    return self.points_attr is not None
