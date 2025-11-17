"""
Fabric Batch Mesh Updater

High-performance mesh updates using Fabric/USDRT API.
Optimized for maximum FPS with minimal overhead.
"""

import carb
import omni.usd
import warp as wp

# Try to import usdrt
FABRIC_AVAILABLE = False
try:
  import usdrt.Usd
  import usdrt.Sdf

  FABRIC_AVAILABLE = True
  carb.log_info("[FabricBatchMeshUpdater] USDRT available")
except ImportError:
  import usdrt.Usd
  import usdrt.Sdf

  carb.log_warn("[FabricBatchMeshUpdater] USDRT not available")


class FabricBatchMeshUpdater:
  """
  High-performance Fabric mesh updater.
  Minimizes overhead for maximum FPS.
  """

  def __init__(self):
    """Initialize Fabric updater."""
    self.fabric_stage = None
    self.mesh_fabric_prims = []
    self.points_attrs = []  # Cache attribute objects

    if not FABRIC_AVAILABLE:
      return

    try:
      usd_context = omni.usd.get_context()
      if not usd_context:
        return

      stage_id = usd_context.get_stage_id()
      self.fabric_stage = usdrt.Usd.Stage.Attach(stage_id)

      if self.fabric_stage:
        carb.log_info("[FabricBatchMeshUpdater] Attached to Fabric stage")

    except Exception as e:
      carb.log_error(f"[FabricBatchMeshUpdater] Init failed: {e}")

  def register_mesh(self, mesh_path: str):
    """Register mesh and cache attribute for fast updates."""
    if not self.fabric_stage:
      return False

    try:
      fabric_prim = self.fabric_stage.GetPrimAtPath(mesh_path)
      if not fabric_prim or not fabric_prim.IsValid():
        return False

      points_attr = fabric_prim.GetAttribute("points")
      if not points_attr:
        return False

      self.mesh_fabric_prims.append(fabric_prim)
      self.points_attrs.append(points_attr)
      return True

    except Exception as e:
      carb.log_error(f"[FabricBatchMeshUpdater] Register failed: {e}")
      return False

  def batch_update_vertices_gpu(self, warp_array: wp.array, vertex_count_per_mesh: int):
    """
    Ultra-fast batch update - optimized hot path.
    
    Tests multiple conversion strategies to minimize Python overhead.
    """
    if not self.fabric_stage:
      return

    try:
      # Single CPU copy for all meshes
      all_vertices_np = warp_array.numpy()

      # Update all meshes - use cached attributes
      for i, points_attr in enumerate(self.points_attrs):
        start_idx = i * vertex_count_per_mesh
        end_idx = start_idx + vertex_count_per_mesh

        # Extract slice as numpy view (no copy)
        mesh_vertices_np = all_vertices_np[start_idx:end_idx]

        # OPTIMIZATION ATTEMPT 1: Try map() instead of list comprehension
        # map() is slightly faster for simple conversions
        fabric_vertices = list(map(lambda v: (float(v[0]), float(v[1]), float(v[2])), mesh_vertices_np))
        points_attr.Set(fabric_vertices)

    except Exception as e:
      carb.log_error(f"[FabricBatchMeshUpdater] Update failed: {e}")

  def is_fabric_available(self) -> bool:
    """Check if Fabric is ready."""
    return FABRIC_AVAILABLE and self.fabric_stage is not None

  def cleanup(self):
    """Release resources."""
    self.mesh_fabric_prims.clear()
    self.points_attrs.clear()
    self.fabric_stage = None
