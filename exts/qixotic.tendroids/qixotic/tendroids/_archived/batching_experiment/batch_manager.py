"""
Batch manager for coordinating size-class grouped Tendroid updates

Organizes Tendroids into size-class batches and coordinates their deformation
through batched Warp kernels AND batched Fabric USD updates.
"""

from typing import Dict, List

import carb
import numpy as np

from .batched_warp_deformer import BatchedWarpDeformer
from .fabric_batch_updater import FabricBatchUpdater


class TendroidBatchManager:
  """
  Manages batched vertex deformation for Tendroids grouped by size class.
  
  Reduces overhead through TWO optimizations:
  1. Batched Warp kernels (N individual launches → 3 batch launches)
  2. Batched Fabric updates (N USD writes → 3 batch writes)
  """

  def __init__(self, tendroids: List):
    """
    Initialize batch manager from list of Tendroids.
    
    Args:
        tendroids: List of Tendroid instances with batch_metadata
    """
    # Create Fabric updater FIRST (before organizing batches)
    self.fabric_updater = FabricBatchUpdater()

    # Now organize batches (which needs fabric_updater)
    self.batches = self._organize_into_batches(tendroids)

    carb.log_info(
      f"[TendroidBatchManager] Managing {len(self.batches)} size-class batches"
    )

    if self.fabric_updater.is_available():
      carb.log_info("[TendroidBatchManager] Using Fabric for fast USD updates")
    else:
      carb.log_warn("[TendroidBatchManager] Fabric unavailable - using USD fallback")

  def _organize_into_batches(self, tendroids: List) -> Dict[str, dict]:
    """
    Organize Tendroids into size-class batches.
    
    Returns:
        Dictionary mapping size class name to batch info
    """
    # Group Tendroids by size class
    groups = { 'SMALL': [], 'MEDIUM': [], 'LARGE': [] }

    for tendroid in tendroids:
      if hasattr(tendroid, 'batch_metadata'):
        size_class = tendroid.batch_metadata['size_class']
        groups[size_class].append(tendroid)

    # Create batch deformers for each non-empty group
    batches = { }

    for class_name, tendroid_list in groups.items():
      if not tendroid_list:
        continue

      batch_size = len(tendroid_list)

      # Get vertex count from first Tendroid's warp_deformer
      if not tendroid_list[0].warp_deformer:
        carb.log_warn(
          f"[TendroidBatchManager] Tendroids in class {class_name} "
          f"have no warp_deformer - skipping batch creation"
        )
        continue

      verts_per_tendroid = tendroid_list[0].warp_deformer.num_vertices

      # Create batched deformer
      deformer = BatchedWarpDeformer(
        batch_size=batch_size,
        verts_per_tendroid=verts_per_tendroid
      )

      # Set base geometry for each Tendroid
      for idx, tendroid in enumerate(tendroid_list):
        if hasattr(tendroid.warp_deformer, 'original_positions'):
          # Get original vertices from existing WarpDeformer
          original_verts_gpu = tendroid.warp_deformer.original_positions
          original_verts_cpu = original_verts_gpu.numpy()

          # Convert numpy array back to list of tuples for set_base_geometry
          original_verts_list = [
            (v[0], v[1], v[2]) for v in original_verts_cpu
          ]

          deformer.set_base_geometry(
            idx,
            original_verts_list,
            tendroid.deform_start_height
          )

      batches[class_name] = {
        'tendroids': tendroid_list,
        'deformer': deformer,
        'mesh_indices': []  # Will store Fabric mesh indices
      }

      # Register meshes with Fabric updater
      if self.fabric_updater and self.fabric_updater.is_available():
        mesh_indices = []
        for idx, tendroid in enumerate(tendroid_list):
          if tendroid.mesh_path:
            # Register returns success/failure - we track indices ourselves
            if self.fabric_updater.register_mesh(tendroid.mesh_path):
              mesh_indices.append(self.fabric_updater.get_mesh_count() - 1)
              carb.log_info(
                f"[TendroidBatchManager] Registered {tendroid.name} at index "
                f"{self.fabric_updater.get_mesh_count() - 1}"
              )
            else:
              carb.log_error(
                f"[TendroidBatchManager] FAILED to register {tendroid.name} "
                f"at path '{tendroid.mesh_path}'"
              )
              mesh_indices.append(-1)  # Mark as failed
        batches[class_name]['mesh_indices'] = mesh_indices

        carb.log_info(
          f"[TendroidBatchManager] Batch {class_name}: "
          f"{len([i for i in mesh_indices if i >= 0])}/{len(mesh_indices)} "
          f"meshes registered with Fabric"
        )
      else:
        carb.log_warn(
          f"[TendroidBatchManager] Fabric unavailable for batch {class_name}"
        )

      carb.log_info(
        f"[TendroidBatchManager] Created batch {class_name}: "
        f"{batch_size} Tendroids ({verts_per_tendroid} verts each)"
      )

    return batches

  def update_all_batches(self, dt: float):
    """
    Update all batches with current animation state.
    
    This replaces N individual Tendroid updates with 3 batched updates
    (one per size class), reducing GPU kernel launches from N to 3.
    
    Args:
        dt: Delta time in seconds
    """
    for class_name, batch_info in self.batches.items():
      self._update_batch(class_name, batch_info, dt)

  def _update_batch(self, class_name: str, batch_info: dict, dt: float):
    """
    Update a single size-class batch.
    
    Args:
        class_name: Size class identifier
        batch_info: Batch information dictionary
        dt: Delta time in seconds
    """
    tendroids = batch_info['tendroids']
    deformer = batch_info['deformer']
    batch_size = len(tendroids)

    # Collect animation parameters from all Tendroids in batch
    wave_centers = np.zeros(batch_size, dtype=np.float32)
    bulge_lengths = np.zeros(batch_size, dtype=np.float32)
    amplitudes = np.zeros(batch_size, dtype=np.float32)
    deform_start_heights = np.zeros(batch_size, dtype=np.float32)
    wave_growth_distances = np.zeros(batch_size, dtype=np.float32)
    distances_traveled = np.zeros(batch_size, dtype=np.float32)

    for idx, tendroid in enumerate(tendroids):
      # Check if Tendroid animation is enabled
      if not tendroid.is_animation_enabled():
        # Use default/zero values for inactive Tendroids
        continue

      # Update breathing animator to get current wave params
      if hasattr(tendroid, 'breathing_animator') and tendroid.breathing_animator:
        wave_params = tendroid.breathing_animator.update(dt)

        # Only apply deformation if wave is active
        if wave_params['active']:
          wave_centers[idx] = wave_params['wave_center']
          bulge_lengths[idx] = wave_params['bulge_length']
          amplitudes[idx] = wave_params['amplitude']
          deform_start_heights[idx] = tendroid.deform_start_height
          wave_growth_distances[idx] = wave_params.get('wave_growth_distance', 0.0)
          distances_traveled[idx] = wave_params.get('distance_traveled', 0.0)

    # Process entire batch with SINGLE kernel launch
    deformed_arrays = deformer.update_batch(
      wave_centers,
      bulge_lengths,
      amplitudes,
      deform_start_heights,
      wave_growth_distances,
      distances_traveled
    )

    # Apply deformed vertices using Fabric batch update if available
    if self.fabric_updater and self.fabric_updater.is_available():
      mesh_indices = batch_info['mesh_indices']

      # Update via Fabric (fast path)
      for idx, (mesh_index, deformed_verts) in enumerate(zip(mesh_indices, deformed_arrays)):
        if mesh_index >= 0:  # Valid Fabric registration
          self.fabric_updater.update_mesh_vertices(mesh_index, deformed_verts)
        else:
          # Fallback to Python for this specific Tendroid
          self._fallback_update(tendroids[idx], deformed_verts)
    else:
      # No Fabric - use Python fallback for all
      for idx, (tendroid, deformed_verts) in enumerate(zip(tendroids, deformed_arrays)):
        if tendroid.is_animation_enabled():
          self._fallback_update(tendroid, deformed_verts)

  def _fallback_update(self, tendroid, deformed_verts):
    """Fallback to Python mesh updater for single Tendroid."""
    if hasattr(tendroid, 'mesh_updater') and tendroid.mesh_updater:
      if tendroid.mesh_updater.is_valid():
        tendroid.mesh_updater.update_vertices(deformed_verts)

  def cleanup(self):
    """Release all batch resources."""
    if self.fabric_updater:
      self.fabric_updater.cleanup()

    for batch_info in self.batches.values():
      batch_info['deformer'].cleanup()

    self.batches.clear()
    carb.log_info("[TendroidBatchManager] Cleanup complete")
