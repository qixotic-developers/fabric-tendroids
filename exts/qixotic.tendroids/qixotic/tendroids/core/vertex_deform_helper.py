"""
Vertex deformation helper - SIMPLIFIED

Uses pure Python MeshVertexUpdater (fast enough at 40 fps)
C++ hybrid approach abandoned (slower due to tuple conversion fallback)
"""

import carb


class VertexDeformHelper:
  """
  Placeholder helper - always returns False to force Python fallback.
  
  The C++ hybrid approach was slower than pure Python due to:
  - Vt.Vec3fArray.FromBuffer() not available
  - Fallback to tuple creation (60k tuples/frame)
  - Added overhead worse than pure Python
  
  Result: Pure Python MeshVertexUpdater is faster (40 fps vs 26 fps)
  """
  
  def __init__(self, mesh_path: str):
    self.mesh_path = mesh_path
    self._initialized = False
    carb.log_info(
      f"[VertexDeformHelper] Created for '{mesh_path}' "
      f"(will use Python MeshVertexUpdater)"
    )
  
  def initialize(self, stage, fast_mesh_updater) -> bool:
    """Always return False to force Python fallback."""
    carb.log_info(
      f"[VertexDeformHelper] Using Python MeshVertexUpdater "
      f"(C++ hybrid abandoned - was slower)"
    )
    return False
  
  def update_vertices(self, deformed_vertices) -> bool:
    """Not used - Python fallback handles updates."""
    return False
  
  def cleanup(self):
    """Nothing to cleanup."""
    pass
  
  def is_initialized(self) -> bool:
    """Always False to force fallback."""
    return False
