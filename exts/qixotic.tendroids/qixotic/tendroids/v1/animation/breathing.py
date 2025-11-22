"""
Breathing animation controller for Tendroids

Manages single traveling bulge timing and parameters with wave growth effect.
"""

from ..utils.math_helpers import calculate_wave_position


class BreathingAnimator:
  """
  Controls single bulge breathing animation.

  Bulge grows from zero at start, travels upward, shrinks to zero at top.
  """

  def __init__(
    self,
    length: float,
    deform_start_height: float,
    wave_speed: float = 40.0,
    bulge_length_percent: float = 40.0,
    amplitude: float = 0.5,
    cycle_delay: float = 2.0
  ):
    """
    Initialize breathing animator.

    Args:
        length: Total Tendroid length
        deform_start_height: Y position where deformation begins
        wave_speed: Bulge travel speed (units/second)
        bulge_length_percent: Bulge size as % of total length (5-50)
        amplitude: Maximum radial expansion (0.5 = 50%)
        cycle_delay: Pause between cycles (seconds)
    """
    self.length = length
    self.deform_start_height = deform_start_height
    self.wave_speed = wave_speed
    self.bulge_length_percent = bulge_length_percent
    self.amplitude = amplitude
    self.cycle_delay = cycle_delay

    # Calculate bulge length
    self.bulge_length = length * (bulge_length_percent / 100.0)
    
    # Wave growth distance (distance needed for wave to reach full size)
    self.wave_growth_distance = self.bulge_length * 0.5

    # Calculate timing
    travel_distance = (length - deform_start_height) + self.bulge_length
    self.travel_time = travel_distance / wave_speed
    self.cycle_duration = self.travel_time + cycle_delay

    # State
    self.time = 0.0
    self.last_bubble_time = -999.0

  def update(self, dt: float) -> dict:
    """
    Update animation and return bulge parameters.

    Args:
        dt: Delta time since last update (seconds)

    Returns:
        Dictionary with wave_center, bulge_length, amplitude, wave_growth, active
    """
    self.time += dt
    cycle_time = self.time % self.cycle_duration

    # Check if in delay period
    if cycle_time >= self.travel_time:
      return {
        'wave_center': -1000.0,  # Off-screen
        'bulge_length': self.bulge_length,
        'amplitude': 0.0,  # No deformation during delay
        'wave_growth_distance': self.wave_growth_distance,
        'active': False
      }

    # Calculate active bulge position
    wave_center = calculate_wave_position(
      cycle_time,
      self.wave_speed,
      self.deform_start_height
    )
    
    # Calculate how far wave has traveled from start
    distance_traveled = wave_center - self.deform_start_height

    return {
      'wave_center': wave_center,
      'bulge_length': self.bulge_length,
      'amplitude': self.amplitude,
      'wave_growth_distance': self.wave_growth_distance,
      'distance_traveled': distance_traveled,
      'active': True
    }

  def should_emit_bubble(self) -> bool:
    """Check if bulge has reached top (bubble trigger)."""
    cycle_time = self.time % self.cycle_duration

    if cycle_time >= self.travel_time:
      return False

    wave_center = calculate_wave_position(
      cycle_time,
      self.wave_speed,
      self.deform_start_height
    )

    # Emit when bulge passes 95% of length
    top_threshold = self.length * 0.95

    # Prevent duplicates
    if self.time - self.last_bubble_time < self.cycle_duration * 0.5:
      return False

    if wave_center >= top_threshold:
      self.last_bubble_time = self.time
      return True

    return False

  def reset(self):
    """Reset animation to start."""
    self.time = 0.0
    self.last_bubble_time = -999.0

  def set_parameters(
    self,
    wave_speed: float = None,
    bulge_length_percent: float = None,
    amplitude: float = None,
    cycle_delay: float = None
  ):
    """Update animation parameters at runtime."""
    if wave_speed is not None:
      self.wave_speed = wave_speed
    if bulge_length_percent is not None:
      self.bulge_length_percent = bulge_length_percent
      self.bulge_length = self.length * (bulge_length_percent / 100.0)
      self.wave_growth_distance = self.bulge_length * 0.5
    if amplitude is not None:
      self.amplitude = amplitude
    if cycle_delay is not None:
      self.cycle_delay = cycle_delay

    # Recalculate timing
    travel_distance = (self.length - self.deform_start_height) + self.bulge_length
    self.travel_time = travel_distance / self.wave_speed
    self.cycle_duration = self.travel_time + self.cycle_delay
