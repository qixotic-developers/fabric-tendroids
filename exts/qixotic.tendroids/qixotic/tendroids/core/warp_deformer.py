"""
Warp-based vertex deformer for smooth Tendroid breathing animation

OPTIMIZED VERSION - Eliminates Python list comprehension bottleneck.
Uses GPU-accelerated Warp kernels with single traveling bulge and fade-in effect.
"""

import warp as wp
from pxr import Vt


@wp.kernel
def deform_breathing_bulge(
  original_positions: wp.array(dtype=wp.vec3),
  deformed_positions: wp.array(dtype=wp.vec3),
  wave_center: float,
  bulge_length: float,
  amplitude: float,
  deform_start_y: float,
  wave_growth_distance: float,
  distance_traveled: float
):
  """
  Warp kernel: Single traveling bulge breathing effect with fade-in.

  Wave grows from zero at leading edge to full size, then shrinks to zero.
  Uses raised cosine envelope for smooth zero crossings plus growth factor.
  """
  tid = wp.tid()

  # Get original position
  pos = original_positions[tid]
  x = pos[0]
  y = pos[1]
  z = pos[2]

  # Skip vertices below deformation zone
  if y < deform_start_y:
    deformed_positions[tid] = pos
    return

  # Calculate radial distance from Y axis
  radial_dist = wp.sqrt(x * x + z * z)

  # Avoid division by zero
  if radial_dist < 0.001:
    deformed_positions[tid] = pos
    return

  # Calculate distance from wave center
  distance_from_center = y - wave_center
  half_bulge = bulge_length / 2.0

  # Outside bulge influence - no deformation
  if wp.abs(distance_from_center) > half_bulge:
    deformed_positions[tid] = pos
    return

  # Inside bulge - raised cosine envelope
  # 0.5 * (1 + cos(pi * distance / half_bulge))
  # Gives smooth zero-to-one-to-zero profile
  normalized_dist = distance_from_center / half_bulge
  envelope = 0.5 * (1.0 + wp.cos(3.14159265 * normalized_dist))
  
  # Calculate wave growth factor (fade-in from leading edge)
  # Wave grows from 0 to full size over wave_growth_distance
  growth_factor = 1.0
  if distance_traveled < wave_growth_distance:
    if wave_growth_distance > 0.001:
      growth_factor = distance_traveled / wave_growth_distance
      # Smooth the growth with ease-out
      growth_factor = 1.0 - wp.pow(1.0 - growth_factor, 2.0)
  
  # Combine envelope with growth factor
  final_envelope = envelope * growth_factor

  # Apply radial displacement
  displacement = 1.0 + (final_envelope * amplitude)
  new_x = x * displacement
  new_z = z * displacement

  deformed_positions[tid] = wp.vec3(new_x, y, new_z)


class WarpDeformer:
  """
  GPU-accelerated mesh deformer using Warp.

  Manages vertex buffers and applies single traveling bulge deformation
  with smooth fade-in effect.
  
  OPTIMIZATION: Returns Vt.Vec3fArray directly instead of Gf.Vec3f list,
  eliminating expensive Python list comprehension.
  """

  def __init__(self, original_vertices: list, deform_start_height: float):
    """
    Initialize deformer with mesh geometry.

    Args:
        original_vertices: List of Gf.Vec3f vertices
        deform_start_height: Y height where deformation begins
    """
    self.deform_start_height = deform_start_height
    self.num_vertices = len(original_vertices)

    # Convert to Warp arrays
    vertices_data = [(v[0], v[1], v[2]) for v in original_vertices]
    self.original_positions = wp.array(vertices_data, dtype=wp.vec3, device="cuda")
    self.deformed_positions = wp.array(vertices_data, dtype=wp.vec3, device="cuda")

  def update(
    self,
    wave_center: float,
    bulge_length: float,
    amplitude: float,
    wave_growth_distance: float = 0.0,
    distance_traveled: float = 0.0
  ) -> Vt.Vec3fArray:
    """
    Apply deformation and return updated vertex positions.
    
    OPTIMIZED: Returns Vt.Vec3fArray directly, avoiding Python list conversion.

    Args:
        wave_center: Current Y position of bulge center
        bulge_length: Length of the bulge (controls spread)
        amplitude: Maximum radial expansion factor
        wave_growth_distance: Distance over which wave grows to full size
        distance_traveled: How far wave has traveled from start

    Returns:
        Vt.Vec3fArray of deformed vertices (ready for USD)
    """
    # Launch Warp kernel
    wp.launch(
      kernel=deform_breathing_bulge,
      dim=self.num_vertices,
      inputs=[
        self.original_positions,
        self.deformed_positions,
        wave_center,
        bulge_length,
        amplitude,
        self.deform_start_height,
        wave_growth_distance,
        distance_traveled
      ],
      device="cuda"
    )

    # OPTIMIZATION: Direct GPU→CPU→USD conversion
    # Copy results back to CPU as numpy array
    deformed_data = self.deformed_positions.numpy()
    
    # Convert directly to Vt.Vec3fArray (zero-copy via buffer protocol)
    return Vt.Vec3fArray.FromBuffer(deformed_data)

  def cleanup(self):
    """Release Warp resources."""
    self.original_positions = None
    self.deformed_positions = None
