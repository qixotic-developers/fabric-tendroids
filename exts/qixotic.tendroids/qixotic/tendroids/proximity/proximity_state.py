"""
Proximity State Definitions

TEND-18: Create proximity state manager
TEND-74: Define ProximityState enum with all states

Defines the states and transitions for creature-tendroid proximity tracking.
"""

from enum import Enum, auto
from typing import Dict, Set


class ProximityState(Enum):
  """
  States for creature-tendroid proximity relationship.

  State Diagram:

      ┌─────────────────────────────────────────────────┐
      │                                                 │
      ▼                                                 │
    IDLE ──────► APPROACHING ──────► CONTACT           │
      ▲              │                  │              │
      │              │                  ▼              │
      │              │             RETREATING          │
      │              │                  │              │
      │              ▼                  ▼              │
      └────────── RECOVERED ◄───────────┘              │
                     │                                 │
                     └─────────────────────────────────┘
  """

  IDLE = auto()  # No proximity detected (> detection_radius)
  APPROACHING = auto()  # Within detection, moving closer
  CONTACT = auto()  # At or below approach_epsilon
  RETREATING = auto()  # Moving away after contact
  RECOVERED = auto()  # Beyond approach_minimum, safe


# Valid state transitions
VALID_TRANSITIONS: Dict[ProximityState, Set[ProximityState]] = {
  ProximityState.IDLE: {
    ProximityState.APPROACHING,  # Entered detection range
    ProximityState.CONTACT,  # Instant contact (fast movement)
  },
  ProximityState.APPROACHING: {
    ProximityState.CONTACT,  # Reached contact threshold
    ProximityState.RECOVERED,  # Turned away before contact
    ProximityState.IDLE,  # Left detection range
  },
  ProximityState.CONTACT: {
    ProximityState.RETREATING,  # Started moving away
  },
  ProximityState.RETREATING: {
    ProximityState.CONTACT,  # Re-entered contact zone
    ProximityState.RECOVERED,  # Passed approach_minimum
  },
  ProximityState.RECOVERED: {
    ProximityState.APPROACHING,  # Coming back
    ProximityState.IDLE,  # Left detection range
    ProximityState.CONTACT,  # Instant re-contact
  },
}


def is_valid_transition(from_state: ProximityState, to_state: ProximityState) -> bool:
  """Check if a state transition is valid."""
  if from_state == to_state:
    return True  # Staying in same state is always valid
  return to_state in VALID_TRANSITIONS.get(from_state, set())


def get_zone_for_state(state: ProximityState) -> str:
  """Map state to approximate zone name for compatibility."""
  mapping = {
    ProximityState.IDLE: "idle",
    ProximityState.APPROACHING: "detected",
    ProximityState.CONTACT: "contact",
    ProximityState.RETREATING: "recovering",
    ProximityState.RECOVERED: "approaching",
  }
  return mapping.get(state, "idle")


def get_state_priority(state: ProximityState) -> int:
  """Get priority for state (higher = more urgent)."""
  priorities = {
    ProximityState.IDLE: 0,
    ProximityState.RECOVERED: 1,
    ProximityState.APPROACHING: 2,
    ProximityState.RETREATING: 3,
    ProximityState.CONTACT: 4,
  }
  return priorities.get(state, 0)
