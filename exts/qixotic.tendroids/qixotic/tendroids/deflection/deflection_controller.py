"""
Deflection Controller - Main controller for tendroid deflection behavior

TEND-3: Tendroid Deflection System - Epic implementation

Coordinates approach detection, deflection calculation, and state management
for creature-tendroid deflection interactions.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .approach_calculators import (ApproachResult, TendroidGeometry, detect_approach_type)
from .deflection_config import (ApproachType, DeflectionConfig, get_deflection_config)
from .deflection_helpers import (
  calculate_deflection, smooth_deflection_transition
)


@dataclass
class TendroidDeflectionState:
  """Per-tendroid deflection state tracking."""
  tendroid_id: int
  current_angle: float = 0.0
  target_angle: float = 0.0
  deflection_direction: Tuple[float, float, float] = (0.0, 0.0, 0.0)
  deflection_axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)
  last_approach_type: ApproachType = ApproachType.NONE
  is_deflecting: bool = False
  # Axis latching - prevents flip when creature crosses tendroid
  axis_latched: bool = False
  latched_axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)
  latched_direction: Tuple[float, float, float] = (0.0, 0.0, 0.0)


class DeflectionController:
  """
  Main controller for tendroid deflection behavior.

  Manages deflection state for multiple tendroids and coordinates
  updates based on creature position and movement.

  Usage:
      controller = DeflectionController()
      controller.register_tendroid(tendroid_id, geometry)

      # Each frame:
      controller.update(creature_pos, creature_vel, dt)

      # Apply results:
      for tendroid_id, state in controller.get_all_states().items():
          apply_bend(tendroid_id, state.current_angle, state.deflection_axis)
  """

  def __init__(self, config: Optional[DeflectionConfig] = None):
    """
    Initialize deflection controller.

    Args:
        config: Deflection configuration (uses default if None)
    """
    self.config = config or get_deflection_config()
    self._tendroids: Dict[int, TendroidGeometry] = { }
    self._states: Dict[int, TendroidDeflectionState] = { }
    self._enabled = True

  @property
  def enabled(self) -> bool:
    """Check if deflection system is enabled."""
    return self._enabled

  @enabled.setter
  def enabled(self, value: bool):
    """Enable or disable deflection system."""
    self._enabled = value
    if not value:
      self._reset_all_deflections()

  def register_tendroid(
    self,
    tendroid_id: int,
    geometry: TendroidGeometry
  ) -> None:
    """
    Register a tendroid for deflection tracking.

    Args:
        tendroid_id: Unique identifier
        geometry: Tendroid cylinder geometry
    """
    self._tendroids[tendroid_id] = geometry
    self._states[tendroid_id] = TendroidDeflectionState(tendroid_id=tendroid_id)

  def unregister_tendroid(self, tendroid_id: int) -> None:
    """Remove a tendroid from tracking."""
    self._tendroids.pop(tendroid_id, None)
    self._states.pop(tendroid_id, None)

  def update_tendroid_geometry(
    self,
    tendroid_id: int,
    geometry: TendroidGeometry
  ) -> None:
    """Update geometry for an existing tendroid."""
    if tendroid_id in self._tendroids:
      self._tendroids[tendroid_id] = geometry

  def update(
    self,
    creature_pos: Tuple[float, float, float],
    creature_velocity: Tuple[float, float, float],
    dt: float
  ) -> Dict[int, TendroidDeflectionState]:
    """
    Update deflection for all registered tendroids.

    Args:
        creature_pos: Current creature position (x, y, z)
        creature_velocity: Current creature velocity (vx, vy, vz)
        dt: Delta time in seconds

    Returns:
        Dict mapping tendroid_id to updated state
    """
    if not self._enabled:
      return self._states

    for tendroid_id, geometry in self._tendroids.items():
      state = self._states[tendroid_id]
      self._update_single_tendroid(
        state, geometry, creature_pos, creature_velocity, dt
      )

    return self._states

  def _update_single_tendroid(
    self,
    state: TendroidDeflectionState,
    geometry: TendroidGeometry,
    creature_pos: Tuple[float, float, float],
    creature_velocity: Tuple[float, float, float],
    dt: float
  ) -> None:
    """Update deflection state for a single tendroid."""
    # Detect approach type
    approach = detect_approach_type(
      creature_pos, creature_velocity, geometry, self.config.zones
    )

    # Filter by enabled approach types
    if not self._is_approach_enabled(approach.approach_type):
      approach = ApproachResult(
        approach_type=ApproachType.NONE,
        distance=float('inf'),
        height_ratio=0.0,
        contact_y=geometry.base_y,
        contact_normal=(0.0, 0.0, 0.0),
        is_within_range=False
      )

    # Calculate deflection
    deflection = calculate_deflection(
      approach, geometry, self.config.limits, self.config.zones.detection_range
    )

    # Update target
    state.target_angle = deflection.deflection_angle
    state.last_approach_type = approach.approach_type

    if deflection.apply_deflection:
      # AXIS LATCHING: Lock direction when deflection starts
      if not state.axis_latched:
        # First frame of deflection - latch the axis
        state.latched_axis = deflection.deflection_axis
        state.latched_direction = deflection.deflection_direction
        state.axis_latched = True

      # Always use latched axis while deflecting (prevents flip)
      state.deflection_direction = state.latched_direction
      state.deflection_axis = state.latched_axis
      state.is_deflecting = True

    # Smooth transition
    state.current_angle = smooth_deflection_transition(
      state.current_angle,
      state.target_angle,
      dt,
      self.config.limits.deflection_rate,
      self.config.limits.recovery_rate
    )

    # Check if deflection complete - unlatch when fully recovered
    if state.current_angle < 0.001 and state.target_angle < 0.001:
      state.is_deflecting = False
      state.axis_latched = False  # Release latch for next deflection

  def _is_approach_enabled(self, approach_type: ApproachType) -> bool:
    """Check if approach type is enabled in config."""
    if approach_type == ApproachType.VERTICAL:
      return self.config.enable_vertical
    elif approach_type == ApproachType.HEAD_ON:
      return self.config.enable_head_on
    elif approach_type == ApproachType.PASS_BY:
      return self.config.enable_pass_by
    return False

  def _reset_all_deflections(self) -> None:
    """Reset all tendroid deflections to neutral."""
    for state in self._states.values():
      state.target_angle = 0.0
      state.is_deflecting = False
      state.axis_latched = False

  def get_state(self, tendroid_id: int) -> Optional[TendroidDeflectionState]:
    """Get deflection state for a specific tendroid."""
    return self._states.get(tendroid_id)

  def get_all_states(self) -> Dict[int, TendroidDeflectionState]:
    """Get all tendroid deflection states."""
    return self._states

  def get_deflecting_tendroids(self) -> List[int]:
    """Get list of tendroid IDs currently deflecting."""
    return [
      tid for tid, state in self._states.items()
      if state.is_deflecting
    ]

  def get_debug_info(self) -> Dict:
    """Get debugging information."""
    return {
      'enabled': self._enabled,
      'tendroid_count': len(self._tendroids),
      'deflecting_count': len(self.get_deflecting_tendroids()),
      'config': {
        'min_deflection_deg': math.degrees(self.config.limits.minimum_deflection),
        'max_deflection_deg': math.degrees(self.config.limits.maximum_deflection),
        'detection_range': self.config.zones.detection_range,
      }
    }
