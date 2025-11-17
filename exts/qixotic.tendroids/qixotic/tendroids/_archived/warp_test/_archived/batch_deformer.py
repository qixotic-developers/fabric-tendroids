"""
Batch Deformer

GPU-accelerated batch deformation using single Warp kernel.
Processes multiple tubes in parallel with shared geometry.
"""

import warp as wp
import carb


@wp.kernel
def batch_breathing_deform(
  original_positions: wp.array(dtype=wp.vec3),
  deformed_positions: wp.array(dtype=wp.vec3),
  wave_centers: wp.array(dtype=float),
  amplitudes: wp.array(dtype=float),
  bulge_lengths: wp.array(dtype=float),
  active_flags: wp.array(dtype=int),
  vertices_per_tube: int,
  deform_start_y: float
):
  """
  Batch breathing deformation kernel for multiple tubes.
  
  Processes all tubes in single kernel launch.
  Each thread handles one vertex of one tube.
  
  Thread organization:
    tid = tube_id * vertices_per_tube + vertex_id
  """
  tid = wp.tid()
  
  # Decode tube and vertex IDs
  tube_id = tid // vertices_per_tube
  vertex_id = tid % vertices_per_tube
  
  # Check if this tube is active
  if active_flags[tube_id] == 0:
    deformed_positions[tid] = original_positions[tid]
    return
  
  # Get vertex position
  pos = original_positions[tid]
  x = pos[0]
  y = pos[1]
  z = pos[2]
  
  # Skip vertices below deformation zone
  if y < deform_start_y:
    deformed_positions[tid] = pos
    return
  
  # Get wave parameters for this tube
  wave_center = wave_centers[tube_id]
  amplitude = amplitudes[tube_id]
  bulge_length = bulge_lengths[tube_id]
  half_bulge = bulge_length / 2.0
  
  # Calculate radial distance
  radial_dist = wp.sqrt(x * x + z * z)
  if radial_dist < 0.001:
    deformed_positions[tid] = pos
    return
  
  # Calculate distance from wave center
  distance_from_center = y - wave_center
  
  # Outside bulge influence
  if wp.abs(distance_from_center) > half_bulge:
    deformed_positions[tid] = pos
    return
  
  # Inside bulge - raised cosine envelope
  normalized_dist = distance_from_center / half_bulge
  envelope = 0.5 * (1.0 + wp.cos(3.14159265 * normalized_dist))
  
  # Apply radial displacement
  displacement = 1.0 + (envelope * amplitude)
  new_x = x * displacement
  new_z = z * displacement
  
  deformed_positions[tid] = wp.vec3(new_x, y, new_z)


class BatchDeformer:
  """
  Batch GPU deformer for multiple identical tubes.
  
  Uses single Warp kernel launch to process all tubes in parallel.
  Massive performance improvement over per-tube processing.
  """
  
  def __init__(
    self,
    tube_count: int,
    vertices_per_tube: int,
    base_positions: list,
    deform_start_height: float = 0.0
  ):
    """
    Initialize batch deformer.
    
    Args:
        tube_count: Number of tubes to process
        vertices_per_tube: Vertex count per tube (all identical)
        base_positions: Shared vertex positions for one tube
        deform_start_height: Y height where deformation begins
    """
    self.tube_count = tube_count
    self.vertices_per_tube = vertices_per_tube
    self.deform_start_height = deform_start_height
    self.total_vertices = tube_count * vertices_per_tube
    
    # Replicate base geometry for all tubes
    all_positions = []
    for _ in range(tube_count):
      all_positions.extend([(v[0], v[1], v[2]) for v in base_positions])
    
    # Create Warp buffers
    self.original_positions = wp.array(all_positions, dtype=wp.vec3, device="cuda")
    self.deformed_positions = wp.array(all_positions, dtype=wp.vec3, device="cuda")
    
    # Parameter buffers (updated per frame)
    self.wave_centers = wp.zeros(tube_count, dtype=float, device="cuda")
    self.amplitudes = wp.zeros(tube_count, dtype=float, device="cuda")
    self.bulge_lengths = wp.zeros(tube_count, dtype=float, device="cuda")
    self.active_flags = wp.zeros(tube_count, dtype=int, device="cuda")
    
    carb.log_info(
      f"[BatchDeformer] Initialized: {tube_count} tubes, "
      f"{vertices_per_tube} verts/tube, {self.total_vertices} total vertices"
    )
  
  def update(
    self,
    wave_centers: list,
    amplitudes: list,
    bulge_lengths: list,
    active_flags: list
  ) -> wp.array:
    """
    Apply batch deformation - returns GPU array.
    
    Args:
        wave_centers: Wave center Y position per tube
        amplitudes: Radial expansion per tube
        bulge_lengths: Bulge size per tube
        active_flags: Active state per tube (0 or 1)
    
    Returns:
        Warp array (GPU) with deformed vertices - NO CPU COPY
    """
    # Upload parameters to GPU
    self.wave_centers.assign(wave_centers)
    self.amplitudes.assign(amplitudes)
    self.bulge_lengths.assign(bulge_lengths)
    self.active_flags.assign(active_flags)
    
    # Single kernel launch for ALL tubes
    wp.launch(
      kernel=batch_breathing_deform,
      dim=self.total_vertices,
      inputs=[
        self.original_positions,
        self.deformed_positions,
        self.wave_centers,
        self.amplitudes,
        self.bulge_lengths,
        self.active_flags,
        self.vertices_per_tube,
        self.deform_start_height
      ],
      device="cuda"
    )
    
    # Return GPU array directly - NO .numpy() call!
    return self.deformed_positions
  
  def cleanup(self):
    """Release GPU resources"""
    self.original_positions = None
    self.deformed_positions = None
    self.wave_centers = None
    self.amplitudes = None
    self.bulge_lengths = None
    self.active_flags = None
