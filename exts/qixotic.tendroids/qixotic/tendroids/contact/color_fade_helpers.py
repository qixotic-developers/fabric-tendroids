"""
Color Fade Helpers - Recovery fade calculation functions

Provides two fade modes for color recovery after contact:
1. Distance-proportional: Fade based on distance from tendroid
2. Speed-proportional: Fade based on current repel velocity

Implements TEND-27: Implement color fade during recovery.
Implements TEND-104: Create color_fade_helpers.py module.
Implements TEND-105: Implement distance-proportional fade option.
Implements TEND-106: Implement speed-proportional fade option.
"""

from dataclasses import dataclass
from enum import Enum, auto


class FadeMode(Enum):
  """Mode for calculating recovery fade progress."""
  DISTANCE = auto()  # Fade proportional to distance from tendroid
  SPEED = auto()  # Fade proportional to repel speed
  TIME = auto()  # Fade over fixed time duration


@dataclass
class FadeConfig:
  """Configuration for fade behavior."""
  mode: FadeMode = FadeMode.DISTANCE

  # Distance mode settings
  fade_start_distance: float = 6.0  # Distance where fade begins (tendroid radius)
  fade_end_distance: float = 15.0  # Distance where fade completes (approach_minimum)

  # Speed mode settings
  max_speed: float = 50.0  # Speed at which fade is 0% (full shock color)
  min_speed: float = 5.0  # Speed at which fade is 100% (normal color)

  # Time mode settings
  fade_duration: float = 0.5  # Seconds to fade (for time-based mode)


def calculate_distance_fade(
  current_distance: float,
  config: FadeConfig = None,
) -> float:
  """
  Calculate fade progress based on distance from tendroid.

  Fade progresses linearly from 0 at fade_start_distance
  to 1 at fade_end_distance.

  Args:
      current_distance: Current horizontal distance to tendroid
      config: Fade configuration

  Returns:
      Fade progress 0.0 (shock) to 1.0 (normal)
  """
  if config is None:
    config = FadeConfig()

  start = config.fade_start_distance
  end = config.fade_end_distance

  if current_distance <= start:
    return 0.0
  if current_distance >= end:
    return 1.0

  # Linear interpolation
  return (current_distance - start) / (end - start)


def calculate_speed_fade(
  current_speed: float,
  config: FadeConfig = None,
) -> float:
  """
  Calculate fade progress based on repel speed.

  Higher speed = more shock color (creature still being pushed)
  Lower speed = more normal color (creature slowing down)

  Args:
      current_speed: Current repel velocity magnitude
      config: Fade configuration

  Returns:
      Fade progress 0.0 (shock) to 1.0 (normal)
  """
  if config is None:
    config = FadeConfig()

  max_spd = config.max_speed
  min_spd = config.min_speed

  if current_speed >= max_spd:
    return 0.0
  if current_speed <= min_spd:
    return 1.0

  # Inverse linear - higher speed = lower progress
  return 1.0 - (current_speed - min_spd) / (max_spd - min_spd)


def calculate_time_fade(
  elapsed_time: float,
  config: FadeConfig = None,
) -> float:
  """
  Calculate fade progress based on elapsed time.

  Simple linear fade over configured duration.

  Args:
      elapsed_time: Seconds since recovery started
      config: Fade configuration

  Returns:
      Fade progress 0.0 (shock) to 1.0 (normal)
  """
  if config is None:
    config = FadeConfig()

  if elapsed_time <= 0:
    return 0.0
  if elapsed_time >= config.fade_duration:
    return 1.0

  return elapsed_time / config.fade_duration


def calculate_fade_progress(
  config: FadeConfig,
  distance: float = 0.0,
  speed: float = 0.0,
  elapsed_time: float = 0.0,
) -> float:
  """
  Calculate fade progress using configured mode.

  Dispatches to appropriate fade calculation based on mode.

  Args:
      config: Fade configuration with mode selection
      distance: Current distance (for DISTANCE mode)
      speed: Current speed (for SPEED mode)
      elapsed_time: Elapsed time (for TIME mode)

  Returns:
      Fade progress 0.0 (shock) to 1.0 (normal)
  """
  if config.mode == FadeMode.DISTANCE:
    return calculate_distance_fade(distance, config)
  elif config.mode == FadeMode.SPEED:
    return calculate_speed_fade(speed, config)
  elif config.mode == FadeMode.TIME:
    return calculate_time_fade(elapsed_time, config)
  else:
    return 1.0  # Default to normal


def apply_easing(progress: float, easing: str = "linear") -> float:
  """
  Apply easing function to fade progress.

  Args:
      progress: Linear progress 0.0 to 1.0
      easing: Easing type ("linear", "ease_in", "ease_out", "ease_in_out")

  Returns:
      Eased progress value
  """
  progress = max(0.0, min(1.0, progress))

  if easing == "linear":
    return progress
  elif easing == "ease_in":
    # Quadratic ease in
    return progress * progress
  elif easing == "ease_out":
    # Quadratic ease out
    return 1.0 - (1.0 - progress) * (1.0 - progress)
  elif easing == "ease_in_out":
    # Quadratic ease in-out
    if progress < 0.5:
      return 2.0 * progress * progress
    else:
      return 1.0 - 2.0 * (1.0 - progress) * (1.0 - progress)
  else:
    return progress


def blend_fade_modes(
  distance_progress: float,
  speed_progress: float,
  distance_weight: float = 0.5,
) -> float:
  """
  Blend distance and speed fade modes for hybrid effect.

  Allows combining both modes with configurable weighting.

  Args:
      distance_progress: Progress from distance calculation
      speed_progress: Progress from speed calculation
      distance_weight: Weight for distance (0-1), speed gets remainder

  Returns:
      Blended progress value
  """
  distance_weight = max(0.0, min(1.0, distance_weight))
  speed_weight = 1.0 - distance_weight

  return distance_progress * distance_weight + speed_progress * speed_weight
