"""
Proximity State Transition Logic

TEND-18: Create proximity state manager
TEND-75: Implement state transition logic

Contains the logic for determining state transitions based on
distance measurements and approach parameters.
"""

from typing import Optional, Tuple

from .proximity_config import ApproachParameters, DEFAULT_APPROACH_PARAMS
from .proximity_state import ProximityState


def determine_next_state(
  current_state: ProximityState,
  surface_distance: float,
  previous_distance: Optional[float] = None,
  params: ApproachParameters = DEFAULT_APPROACH_PARAMS,
) -> Tuple[ProximityState, bool]:
  """
  Determine the next state based on current state and distance.

  Args:
      current_state: Current proximity state
      surface_distance: Distance to tendroid surface in meters
      previous_distance: Previous distance (for direction detection)
      params: Approach parameters defining zone thresholds

  Returns:
      Tuple of (next_state, did_transition)
  """
  # Determine movement direction with hysteresis
  # Use small threshold to avoid noise-triggered transitions
  MOVEMENT_THRESHOLD = 0.001  # 1mm

  is_approaching = False
  is_retreating = False

  if previous_distance is not None:
    delta = previous_distance - surface_distance
    if delta > MOVEMENT_THRESHOLD:
      is_approaching = True
    elif delta < -MOVEMENT_THRESHOLD:
      is_retreating = True
    # else: holding steady (neither approaching nor retreating)

  next_state = _compute_next_state(
    current_state, surface_distance, is_approaching, is_retreating, params
  )

  did_transition = next_state != current_state
  return next_state, did_transition


def _compute_next_state(
  current: ProximityState,
  distance: float,
  approaching: bool,
  retreating: bool,
  params: ApproachParameters,
) -> ProximityState:
  """Core state transition logic."""

  # Contact zone - always transition to CONTACT
  if distance <= params.approach_epsilon:
    return ProximityState.CONTACT

  # Outside detection - always IDLE
  if distance > params.detection_radius:
    return ProximityState.IDLE

  # State-specific logic for middle zones
  if current == ProximityState.IDLE:
    return _from_idle(distance, approaching, retreating, params)

  elif current == ProximityState.APPROACHING:
    return _from_approaching(distance, approaching, retreating, params)

  elif current == ProximityState.CONTACT:
    return _from_contact(distance, approaching, retreating, params)

  elif current == ProximityState.RETREATING:
    return _from_retreating(distance, approaching, retreating, params)

  elif current == ProximityState.RECOVERED:
    return _from_recovered(distance, approaching, retreating, params)

  return current


def _from_idle(
  distance: float, approaching: bool, retreating: bool, params: ApproachParameters
) -> ProximityState:
  """Transitions from IDLE state."""
  # Just entered detection range
  return ProximityState.APPROACHING


def _from_approaching(
  distance: float, approaching: bool, retreating: bool, params: ApproachParameters
) -> ProximityState:
  """Transitions from APPROACHING state."""
  # Only transition to RECOVERED if actively retreating (not just holding)
  if retreating and distance > params.approach_minimum:
    return ProximityState.RECOVERED
  return ProximityState.APPROACHING


def _from_contact(
  distance: float, approaching: bool, retreating: bool, params: ApproachParameters
) -> ProximityState:
  """Transitions from CONTACT state."""
  # Only way out is retreating
  if distance > params.approach_epsilon:
    return ProximityState.RETREATING
  return ProximityState.CONTACT


def _from_retreating(
  distance: float, approaching: bool, retreating: bool, params: ApproachParameters
) -> ProximityState:
  """Transitions from RETREATING state."""
  # Check if past minimum threshold
  if distance > params.approach_minimum:
    return ProximityState.RECOVERED

  # Still retreating but in buffer zone
  return ProximityState.RETREATING


def _from_recovered(
  distance: float, approaching: bool, retreating: bool, params: ApproachParameters
) -> ProximityState:
  """Transitions from RECOVERED state."""
  if approaching and distance <= params.warning_distance:
    return ProximityState.APPROACHING
  return ProximityState.RECOVERED


def get_transition_description(
  from_state: ProximityState, to_state: ProximityState
) -> str:
  """Get human-readable description of a transition."""
  descriptions = {
    (ProximityState.IDLE, ProximityState.APPROACHING):
      "Creature entered detection range",
    (ProximityState.APPROACHING, ProximityState.CONTACT):
      "Creature made contact",
    (ProximityState.APPROACHING, ProximityState.RECOVERED):
      "Creature turned away",
    (ProximityState.CONTACT, ProximityState.RETREATING):
      "Creature retreating from contact",
    (ProximityState.RETREATING, ProximityState.RECOVERED):
      "Creature reached safe distance",
    (ProximityState.RETREATING, ProximityState.CONTACT):
      "Creature re-entered contact",
    (ProximityState.RECOVERED, ProximityState.APPROACHING):
      "Creature approaching again",
    (ProximityState.RECOVERED, ProximityState.IDLE):
      "Creature left detection range",
  }
  return descriptions.get((from_state, to_state), "State changed")
