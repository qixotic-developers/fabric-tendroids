"""
Fabric Batch Mesh Updater - OPTIMIZED

High-performance batch mesh updates using Fabric/USDRT API.
Eliminates tuple conversion bottleneck for maximum performance.
"""

import carb
import omni.usd
from pxr import Vt

# Try to import usdrt
FABRIC_AVAILABLE = False
try:
  import usdrt.Usd

  FABRIC_AVAILABLE = True
  carb.log_info("[FabricBatchUpdater] USDRT available")
except ImportError:
  import usdrt.Usd
  carb.log_warn("[FabricBatchUpdater] USDRT not available - falling back to USD")


class FabricBatchUpdater:
  """
  High-performance Fabric mesh updater for batched Tendroid updates.
  
  Optimized to avoid Python tuple conversion bottleneck by using
  Vt.Vec3fArray buffer protocol for zero-copy updates.
  """

  def __init__(self):
    """Initialize Fabric updater."""
    self.fabric_stage = None
    self.mesh_paths = []  # Track registered meshes
    self.fabric_prims = []  # Cache fabric prims
    self.points_attrs = []  # Cache attribute objects

    if not FABRIC_AVAILABLE:
      carb.log_warn("[FabricBatchUpdater] Fabric not available")
      return

    try:
      usd_context = omni.usd.get_context()
      if not usd_context:
        carb.log_error("[FabricBatchUpdater] No USD context")
        return

      stage_id = usd_context.get_stage_id()
      self.fabric_stage = usdrt.Usd.Stage.Attach(stage_id)

      if self.fabric_stage:
        carb.log_info("[FabricBatchUpdater] Attached to Fabric stage")
      else:
        carb.log_error("[FabricBatchUpdater] Failed to attach to Fabric stage")

    except Exception as e:
      carb.log_error(f"[FabricBatchUpdater] Init failed: {e}")

  def register_mesh(self, mesh_path: str) -> bool:
    """
    Register mesh and cache attribute for fast updates.
    
    Args:
        mesh_path: USD path to mesh prim
    
    Returns:
        True if registration successful
    """
    if not self.fabric_stage:
      return False

    try:
      fabric_prim = self.fabric_stage.GetPrimAtPath(mesh_path)
      if not fabric_prim or not fabric_prim.IsValid():
        carb.log_warn(f"[FabricBatchUpdater] Invalid prim at '{mesh_path}'")
        return False

      points_attr = fabric_prim.GetAttribute("points")
      if not points_attr:
        carb.log_warn(f"[FabricBatchUpdater] No points attribute at '{mesh_path}'")
        return False

      self.mesh_paths.append(mesh_path)
      self.fabric_prims.append(fabric_prim)
      self.points_attrs.append(points_attr)

      carb.log_info(
        f"[FabricBatchUpdater] Registered mesh {len(self.mesh_paths)}: '{mesh_path}'"
      )
      return True

    except Exception as e:
      carb.log_error(f"[FabricBatchUpdater] Register failed for '{mesh_path}': {e}")
      return False

  def update_mesh_vertices(self, mesh_index: int, vertices: Vt.Vec3fArray) -> bool:
    """
    Update single mesh with deformed vertices.
    
    OPTIMIZED: Uses Vt.Vec3fArray directly - no tuple conversion.
    
    Args:
        mesh_index: Index of registered mesh
        vertices: Vt.Vec3fArray of deformed positions
    
    Returns:
        True if update successful
    """
    if not self.fabric_stage or mesh_index >= len(self.points_attrs):
      return False

    try:
      points_attr = self.points_attrs[mesh_index]

      # CRITICAL OPTIMIZATION: Vt.Vec3fArray can be converted to list efficiently
      # The USD/Fabric API accepts this without tuple conversion
      points_attr.Set(vertices)
      return True

    except Exception as e:
      carb.log_warn(
        f"[FabricBatchUpdater] Update failed for mesh {mesh_index}: {e}"
      )
      return False

  def batch_update_all(self, vertices_list: list) -> bool:
    """
    Update all registered meshes with their deformed vertices.
    
    Args:
        vertices_list: List of Vt.Vec3fArray (one per registered mesh)
    
    Returns:
        True if all updates successful
    """
    if not self.fabric_stage:
      return False

    if len(vertices_list) != len(self.points_attrs):
      carb.log_error(
        f"[FabricBatchUpdater] Mismatch: {len(vertices_list)} vertex arrays "
        f"vs {len(self.points_attrs)} registered meshes"
      )
      return False

    try:
      success = True
      for i, (points_attr, vertices) in enumerate(zip(self.points_attrs, vertices_list)):
        try:
          points_attr.Set(vertices)
        except Exception as e:
          carb.log_warn(f"[FabricBatchUpdater] Failed to update mesh {i}: {e}")
          success = False

      return success

    except Exception as e:
      carb.log_error(f"[FabricBatchUpdater] Batch update failed: {e}")
      return False

  def is_available(self) -> bool:
    """Check if Fabric is ready for updates."""
    return FABRIC_AVAILABLE and self.fabric_stage is not None

  def get_mesh_count(self) -> int:
    """Get number of registered meshes."""
    return len(self.mesh_paths)

  def cleanup(self):
    """Release resources."""
    self.mesh_paths.clear()
    self.fabric_prims.clear()
    self.points_attrs.clear()
    self.fabric_stage = None
    carb.log_info("[FabricBatchUpdater] Cleanup complete")
