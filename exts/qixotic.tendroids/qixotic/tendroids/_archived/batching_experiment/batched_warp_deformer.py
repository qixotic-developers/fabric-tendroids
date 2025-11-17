"""
Batched Warp deformer for processing multiple Tendroids of same size class

Processes all Tendroids in a size class with a single kernel launch,
reducing GPU dispatch overhead from N launches to 1 launch per size class.
"""

import warp as wp
import numpy as np
import carb
from pxr import Vt


@wp.kernel
def batch_deform_breathing(
  # Concatenated vertex arrays for all Tendroids in batch
  original_positions: wp.array(dtype=wp.vec3),
  deformed_positions: wp.array(dtype=wp.vec3),
  # Per-Tendroid parameters (indexed by tendroid_id)
  wave_centers: wp.array(dtype=float),
  bulge_lengths: wp.array(dtype=float),
  amplitudes: wp.array(dtype=float),
  deform_start_heights: wp.array(dtype=float),
  wave_growth_distances: wp.array(dtype=float),
  distances_traveled: wp.array(dtype=float),
  # Geometry info
  verts_per_tendroid: int
):
  """
  Batch breathing deformation kernel.
  
  Processes multiple Tendroids in a single kernel launch.
  Each Tendroid's parameters are stored in arrays indexed by tendroid_id.
  
  This is the SAME deformation logic as WarpDeformer, but batched.
  """
  vid = wp.tid()
  
  # Calculate which Tendroid this vertex belongs to
  tendroid_id = vid // verts_per_tendroid
  local_vid = vid % verts_per_tendroid
  
  # Get this Tendroid's parameters
  wave_center = wave_centers[tendroid_id]
  bulge_length = bulge_lengths[tendroid_id]
  amplitude = amplitudes[tendroid_id]
  deform_start_y = deform_start_heights[tendroid_id]
  wave_growth_distance = wave_growth_distances[tendroid_id]
  distance_traveled = distances_traveled[tendroid_id]
  
  # Get original position
  pos = original_positions[vid]
  x = pos[0]
  y = pos[1]
  z = pos[2]
  
  # Skip vertices below deformation zone
  if y < deform_start_y:
    deformed_positions[vid] = pos
    return
  
  # Calculate radial distance from Y axis
  radial_dist = wp.sqrt(x * x + z * z)
  
  # Avoid division by zero
  if radial_dist < 0.001:
    deformed_positions[vid] = pos
    return
  
  # Calculate distance from wave center
  distance_from_center = y - wave_center
  half_bulge = bulge_length / 2.0
  
  # Outside bulge influence - no deformation
  if wp.abs(distance_from_center) > half_bulge:
    deformed_positions[vid] = pos
    return
  
  # Inside bulge - raised cosine envelope
  normalized_dist = distance_from_center / half_bulge
  envelope = 0.5 * (1.0 + wp.cos(3.14159265 * normalized_dist))
  
  # Calculate wave growth factor (fade-in from leading edge)
  growth_factor = 1.0
  if distance_traveled < wave_growth_distance:
    if wave_growth_distance > 0.001:
      growth_factor = distance_traveled / wave_growth_distance
      growth_factor = 1.0 - wp.pow(1.0 - growth_factor, 2.0)
  
  # Combine envelope with growth factor
  final_envelope = envelope * growth_factor
  
  # Apply radial displacement
  displacement = 1.0 + (final_envelope * amplitude)
  new_x = x * displacement
  new_z = z * displacement
  
  deformed_positions[vid] = wp.vec3(new_x, y, new_z)


class BatchedWarpDeformer:
  """
  Processes multiple Tendroids of the same size class in a single batch.
  
  All Tendroids must have identical vertex count but can have different
  animation parameters (wave position, amplitude, etc.).
  """
  
  def __init__(self, batch_size: int, verts_per_tendroid: int):
    """
    Initialize batched deformer.
    
    Args:
        batch_size: Number of Tendroids in this batch
        verts_per_tendroid: Vertex count per Tendroid (must be same for all)
    """
    self.batch_size = batch_size
    self.verts_per_tendroid = verts_per_tendroid
    self.total_verts = batch_size * verts_per_tendroid
    
    # Allocate GPU arrays for concatenated vertices
    self.original_positions = wp.zeros(self.total_verts, dtype=wp.vec3, device="cuda")
    self.deformed_positions = wp.zeros(self.total_verts, dtype=wp.vec3, device="cuda")
    
    # Per-Tendroid parameter arrays
    self.wave_centers = wp.zeros(batch_size, dtype=float, device="cuda")
    self.bulge_lengths = wp.zeros(batch_size, dtype=float, device="cuda")
    self.amplitudes = wp.zeros(batch_size, dtype=float, device="cuda")
    self.deform_start_heights = wp.zeros(batch_size, dtype=float, device="cuda")
    self.wave_growth_distances = wp.zeros(batch_size, dtype=float, device="cuda")
    self.distances_traveled = wp.zeros(batch_size, dtype=float, device="cuda")
    
    carb.log_info(
      f"[BatchedWarpDeformer] Initialized for {batch_size} Tendroids "
      f"({self.total_verts} total vertices, {verts_per_tendroid} per Tendroid)"
    )
  
  def set_base_geometry(self, tendroid_idx: int, original_vertices: list, deform_start_height: float):
    """
    Set base geometry for a specific Tendroid in the batch.
    
    Args:
        tendroid_idx: Index of this Tendroid in batch (0 to batch_size-1)
        original_vertices: List of Gf.Vec3f vertices for this Tendroid
        deform_start_height: Y height where deformation begins
    """
    start_idx = tendroid_idx * self.verts_per_tendroid
    
    # Convert vertices to flat array
    vertices_data = [(v[0], v[1], v[2]) for v in original_vertices]
    
    # Copy to GPU at appropriate offset
    temp_array = wp.array(vertices_data, dtype=wp.vec3, device="cuda")
    wp.copy(
      dest=self.original_positions,
      src=temp_array,
      dest_offset=start_idx,
      src_offset=0,
      count=self.verts_per_tendroid
    )
    
    # Also initialize deformed positions
    wp.copy(
      dest=self.deformed_positions,
      src=temp_array,
      dest_offset=start_idx,
      src_offset=0,
      count=self.verts_per_tendroid
    )
  
  def update_batch(
    self,
    wave_centers_np: np.ndarray,
    bulge_lengths_np: np.ndarray,
    amplitudes_np: np.ndarray,
    deform_start_heights_np: np.ndarray,
    wave_growth_distances_np: np.ndarray,
    distances_traveled_np: np.ndarray
  ) -> list:
    """
    Update entire batch with current animation parameters.
    
    Args:
        wave_centers_np: Array of wave center Y positions (one per Tendroid)
        bulge_lengths_np: Array of bulge lengths
        amplitudes_np: Array of max expansions
        deform_start_heights_np: Array of deform start heights
        wave_growth_distances_np: Array of growth distances
        distances_traveled_np: Array of distances traveled
    
    Returns:
        List of Vt.Vec3fArray (one per Tendroid in batch)
    """
    # Update parameter arrays on GPU
    self.wave_centers.assign(wave_centers_np)
    self.bulge_lengths.assign(bulge_lengths_np)
    self.amplitudes.assign(amplitudes_np)
    self.deform_start_heights.assign(deform_start_heights_np)
    self.wave_growth_distances.assign(wave_growth_distances_np)
    self.distances_traveled.assign(distances_traveled_np)
    
    # Launch kernel for entire batch (SINGLE GPU dispatch)
    wp.launch(
      kernel=batch_deform_breathing,
      dim=self.total_verts,
      inputs=[
        self.original_positions,
        self.deformed_positions,
        self.wave_centers,
        self.bulge_lengths,
        self.amplitudes,
        self.deform_start_heights,
        self.wave_growth_distances,
        self.distances_traveled,
        self.verts_per_tendroid
      ],
      device="cuda"
    )
    
    # Copy results back to CPU
    deformed_data = self.deformed_positions.numpy()
    
    # Split into per-Tendroid arrays
    result_arrays = []
    for i in range(self.batch_size):
      start_idx = i * self.verts_per_tendroid
      end_idx = start_idx + self.verts_per_tendroid
      
      tendroid_verts = deformed_data[start_idx:end_idx]
      vt_array = Vt.Vec3fArray.FromBuffer(tendroid_verts)
      result_arrays.append(vt_array)
    
    return result_arrays
  
  def cleanup(self):
    """Release GPU resources."""
    self.original_positions = None
    self.deformed_positions = None
    self.wave_centers = None
    self.bulge_lengths = None
    self.amplitudes = None
    self.deform_start_heights = None
    self.wave_growth_distances = None
    self.distances_traveled = None
