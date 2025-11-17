"""
Warp Kernels for Testing

Simple deformation kernels to test memory behavior with Warp-based vertex manipulation.
Starts with basic sine wave, progressively adds complexity.
"""

import warp as wp


@wp.kernel
def sine_wave_deform(
  positions: wp.array(dtype=wp.vec3),
  original_positions: wp.array(dtype=wp.vec3),
  time: float,
  amplitude: float,
  frequency: float
):
  """
  Simple sine wave deformation along Y axis.

  Phase 1 kernel: Minimal complexity for baseline testing.
  """
  tid = wp.tid()

  orig_pos = original_positions[tid]
  y = orig_pos[1]

  # Simple sine wave based on Y position and time
  offset = amplitude * wp.sin(frequency * y + time)

  new_pos = wp.vec3(
    orig_pos[0] + offset,
    orig_pos[1],
    orig_pos[2]
  )

  positions[tid] = new_pos


@wp.kernel
def radial_pulse_deform(
  positions: wp.array(dtype=wp.vec3),
  original_positions: wp.array(dtype=wp.vec3),
  time: float,
  amplitude: float,
  frequency: float,
  center: wp.vec3
):
  """
  Radial pulse deformation from center point.

  Phase 2 kernel: Adds distance calculations and radial motion.
  """
  tid = wp.tid()

  orig_pos = original_positions[tid]

  # Calculate distance from center
  to_point = orig_pos - center
  dist = wp.length(to_point)

  # Normalize direction
  direction = wp.normalize(to_point) if dist > 0.001 else wp.vec3(0.0, 1.0, 0.0)

  # Pulse based on distance and time
  pulse = amplitude * wp.sin(frequency * dist - time)

  new_pos = orig_pos + direction * pulse
  positions[tid] = new_pos


@wp.kernel
def breathing_wave_deform(
  positions: wp.array(dtype=wp.vec3),
  original_positions: wp.array(dtype=wp.vec3),
  time: float,
  base_amplitude: float,
  wave_speed: float,
  radial_scale: float
):
  """
  Combined breathing and traveling wave - similar to actual Tendroid motion.

  Phase 3 kernel: Most complex, closest to production use case.
  """
  tid = wp.tid()

  orig_pos = original_positions[tid]
  y = orig_pos[1]

  # Traveling wave component
  wave_phase = wave_speed * time - y * 2.0
  wave_amplitude = base_amplitude * (1.0 + 0.3 * wp.sin(wave_phase))

  # Radial expansion (breathing)
  radial_dist = wp.sqrt(orig_pos[0] * orig_pos[0] + orig_pos[2] * orig_pos[2])
  radial_factor = 1.0 + radial_scale * wp.sin(wave_phase)

  # Combine motions
  new_x = orig_pos[0] * radial_factor
  new_y = orig_pos[1] + wave_amplitude * wp.sin(wave_phase)
  new_z = orig_pos[2] * radial_factor

  positions[tid] = wp.vec3(new_x, new_y, new_z)


class WarpKernelManager:
  """Manages Warp kernel execution and buffer lifecycle"""

  def __init__(self):
    wp.init()
    self.device = wp.get_device("cuda:0")
    self.positions_buffer = None
    self.original_positions_buffer = None

  def initialize_buffers(self, vertex_count: int, initial_positions):
    """Create Warp buffers for vertex data"""
    self.positions_buffer = wp.array(initial_positions, dtype=wp.vec3, device=self.device)
    self.original_positions_buffer = wp.array(initial_positions, dtype=wp.vec3, device=self.device)

  def apply_sine_wave(self, time: float, amplitude: float = 0.5, frequency: float = 2.0):
    """Execute sine wave kernel"""
    wp.launch(
      sine_wave_deform,
      dim=len(self.positions_buffer),
      inputs=[self.positions_buffer, self.original_positions_buffer, time, amplitude, frequency],
      device=self.device
    )
    wp.synchronize()

  def apply_radial_pulse(self, time: float, amplitude: float = 0.3, frequency: float = 1.5):
    """Execute radial pulse kernel"""
    center = wp.vec3(0.0, 0.0, 0.0)
    wp.launch(
      radial_pulse_deform,
      dim=len(self.positions_buffer),
      inputs=[self.positions_buffer, self.original_positions_buffer, time, amplitude, frequency, center],
      device=self.device
    )
    wp.synchronize()

  def apply_breathing_wave(self, time: float, amplitude: float = 0.2, wave_speed: float = 2.0):
    """Execute breathing wave kernel"""
    wp.launch(
      breathing_wave_deform,
      dim=len(self.positions_buffer),
      inputs=[self.positions_buffer, self.original_positions_buffer, time, amplitude, wave_speed, 0.1],
      device=self.device
    )
    wp.synchronize()

  def get_positions(self):
    """Retrieve current positions from GPU"""
    return self.positions_buffer.numpy()

  def cleanup(self):
    """Release GPU resources"""
    self.positions_buffer = None
    self.original_positions_buffer = None
