"""
Proximity State Manager

TEND-18: Create proximity state manager
TEND-76: Create event callbacks for state changes

Main controller for tracking creature-tendroid proximity state over time.
Provides event callbacks for state transitions.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Tuple

from .proximity_config import ApproachParameters, DEFAULT_APPROACH_PARAMS
from .proximity_state import ProximityState
from .state_transitions import determine_next_state, get_transition_description

# Type alias for callback functions
StateCallback = Callable[['StateChangeEvent'], None]


@dataclass
class StateChangeEvent:
  """Event data for state transitions."""

  creature_idx: int
  tendroid_idx: int
  previous_state: ProximityState
  new_state: ProximityState
  surface_distance: float
  timestamp: float = 0.0

  @property
  def description(self) -> str:
    """Human-readable transition description."""
    return get_transition_description(self.previous_state, self.new_state)

  @property
  def is_contact_enter(self) -> bool:
    """True if transitioning INTO contact."""
    return (
      self.previous_state != ProximityState.CONTACT and
      self.new_state == ProximityState.CONTACT
    )

  @property
  def is_contact_exit(self) -> bool:
    """True if transitioning OUT OF contact."""
    return (
      self.previous_state == ProximityState.CONTACT and
      self.new_state != ProximityState.CONTACT
    )

  @property
  def is_detection_enter(self) -> bool:
    """True if entering detection range."""
    return (
      self.previous_state == ProximityState.IDLE and
      self.new_state != ProximityState.IDLE
    )

  @property
  def is_detection_exit(self) -> bool:
    """True if leaving detection range."""
    return (
      self.previous_state != ProximityState.IDLE and
      self.new_state == ProximityState.IDLE
    )


@dataclass
class TrackedEntity:
  """State tracking for a single creature-tendroid pair."""

  creature_idx: int
  tendroid_idx: int
  state: ProximityState = ProximityState.IDLE
  previous_distance: Optional[float] = None
  frames_in_state: int = 0
  total_contact_frames: int = 0


class ProximityStateManager:
  """
  Manages proximity state for multiple creature-tendroid pairs.

  Usage:
      manager = ProximityStateManager()
      manager.on_contact_enter(my_callback)

      # Each frame:
      events = manager.update(creature_idx, tendroid_idx, distance)
      for event in events:
          print(event.description)
  """

  def __init__(self, params: ApproachParameters = None):
    """Initialize state manager."""
    self._params = params or DEFAULT_APPROACH_PARAMS
    self._entities: Dict[Tuple[int, int], TrackedEntity] = { }

    # Callback registrations
    self._on_any_change: List[StateCallback] = []
    self._on_contact_enter: List[StateCallback] = []
    self._on_contact_exit: List[StateCallback] = []
    self._on_detection_enter: List[StateCallback] = []
    self._on_detection_exit: List[StateCallback] = []
    self._on_recovered: List[StateCallback] = []

  def _get_key(self, creature_idx: int, tendroid_idx: int) -> Tuple[int, int]:
    """Get dictionary key for entity pair."""
    return (creature_idx, tendroid_idx)

  def _get_or_create_entity(
    self, creature_idx: int, tendroid_idx: int
  ) -> TrackedEntity:
    """Get existing entity or create new one."""
    key = self._get_key(creature_idx, tendroid_idx)
    if key not in self._entities:
      self._entities[key] = TrackedEntity(creature_idx, tendroid_idx)
    return self._entities[key]

  def get_state(
    self, creature_idx: int, tendroid_idx: int
  ) -> ProximityState:
    """Get current state for a creature-tendroid pair."""
    entity = self._get_or_create_entity(creature_idx, tendroid_idx)
    return entity.state

  def update(
    self,
    creature_idx: int,
    tendroid_idx: int,
    surface_distance: float,
    timestamp: float = 0.0,
  ) -> Optional[StateChangeEvent]:
    """
    Update state based on new distance measurement.

    Args:
        creature_idx: Index of the creature
        tendroid_idx: Index of the tendroid
        surface_distance: Distance to tendroid surface in meters
        timestamp: Optional timestamp for event

    Returns:
        StateChangeEvent if state changed, None otherwise
    """
    entity = self._get_or_create_entity(creature_idx, tendroid_idx)

    # Compute next state
    next_state, did_change = determine_next_state(
      entity.state,
      surface_distance,
      entity.previous_distance,
      self._params,
    )

    # Update entity tracking
    entity.previous_distance = surface_distance

    if did_change:
      event = self._handle_transition(entity, next_state,
                                      surface_distance, timestamp)
      return event
    else:
      entity.frames_in_state += 1
      if entity.state == ProximityState.CONTACT:
        entity.total_contact_frames += 1
      return None

  def _handle_transition(
    self,
    entity: TrackedEntity,
    next_state: ProximityState,
    distance: float,
    timestamp: float,
  ) -> StateChangeEvent:
    """Process a state transition and fire callbacks."""
    event = StateChangeEvent(
      creature_idx=entity.creature_idx,
      tendroid_idx=entity.tendroid_idx,
      previous_state=entity.state,
      new_state=next_state,
      surface_distance=distance,
      timestamp=timestamp,
    )

    # Update entity
    entity.state = next_state
    entity.frames_in_state = 0

    # Fire callbacks
    self._fire_callbacks(event)

    return event

  def _fire_callbacks(self, event: StateChangeEvent) -> None:
    """Fire appropriate callbacks for a state change event."""
    # Always fire on_any_change
    for cb in self._on_any_change:
      cb(event)

    # Fire specific callbacks
    if event.is_contact_enter:
      for cb in self._on_contact_enter:
        cb(event)

    if event.is_contact_exit:
      for cb in self._on_contact_exit:
        cb(event)

    if event.is_detection_enter:
      for cb in self._on_detection_enter:
        cb(event)

    if event.is_detection_exit:
      for cb in self._on_detection_exit:
        cb(event)

    if event.new_state == ProximityState.RECOVERED:
      for cb in self._on_recovered:
        cb(event)

  # =========================================================================
  # Callback Registration Methods
  # =========================================================================

  def on_any_change(self, callback: StateCallback) -> None:
    """Register callback for any state change."""
    self._on_any_change.append(callback)

  def on_contact_enter(self, callback: StateCallback) -> None:
    """Register callback for entering contact state."""
    self._on_contact_enter.append(callback)

  def on_contact_exit(self, callback: StateCallback) -> None:
    """Register callback for exiting contact state."""
    self._on_contact_exit.append(callback)

  def on_detection_enter(self, callback: StateCallback) -> None:
    """Register callback for entering detection range."""
    self._on_detection_enter.append(callback)

  def on_detection_exit(self, callback: StateCallback) -> None:
    """Register callback for leaving detection range."""
    self._on_detection_exit.append(callback)

  def on_recovered(self, callback: StateCallback) -> None:
    """Register callback for recovery (past approach_minimum)."""
    self._on_recovered.append(callback)

  def clear_callbacks(self) -> None:
    """Remove all registered callbacks."""
    self._on_any_change.clear()
    self._on_contact_enter.clear()
    self._on_contact_exit.clear()
    self._on_detection_enter.clear()
    self._on_detection_exit.clear()
    self._on_recovered.clear()

  def reset(self) -> None:
    """Reset all tracked entities to IDLE."""
    self._entities.clear()
