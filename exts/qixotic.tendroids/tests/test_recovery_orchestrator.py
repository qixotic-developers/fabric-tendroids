"""
Tests for RecoveryOrchestrator and helpers

Implements TEND-130: Integrate recovery system modules into runtime.
"""

import sys
from unittest.mock import MagicMock

# Mock warp and carb before imports
sys.modules['warp'] = MagicMock()
sys.modules['carb'] = MagicMock()

from qixotic.tendroids.recovery.recovery_orchestrator_helpers import (
  OrchestratorState,
  create_orchestrator_state,
  handle_contact_event,
  update_frame,
  reset_orchestrator_state,
  is_active,
  is_input_blocked,
  get_current_color,
  get_status_summary,
)
from qixotic.tendroids.recovery.recovery_orchestrator import (
  RecoveryOrchestrator,
)
from qixotic.tendroids.contact.color_effect_helpers import (
  ColorConfig,
  ColorEffectState,
)
from qixotic.tendroids.contact.velocity_fade_helpers import VelocityFadeConfig
from qixotic.tendroids.proximity.proximity_config import ApproachParameters


class TestOrchestratorState:
  """Tests for OrchestratorState creation and queries."""

  def test_create_default_state(self):
    """Default state has all subsystems initialized."""
    state = create_orchestrator_state()

    assert state is not None
    assert state.recovery_context is not None
    assert state.completion_status is not None
    assert state.color_status is not None
    assert state.velocity_status is not None
    assert state.input_lock is not None

  def test_create_with_custom_config(self):
    """State accepts custom configuration."""
    params = ApproachParameters(approach_minimum=20.0)
    colors = ColorConfig(shock_color=(1.0, 0.0, 0.0))
    velocity = VelocityFadeConfig(fade_duration=2.0)

    state = create_orchestrator_state(
      approach_params=params,
      color_config=colors,
      velocity_config=velocity,
    )

    assert state.approach_params.approach_minimum == 20.0
    assert state.color_config.shock_color == (1.0, 0.0, 0.0)
    assert state.velocity_config.fade_duration == 2.0

  def test_initial_state_not_active(self):
    """Fresh state has no active recovery."""
    state = create_orchestrator_state()
    assert not is_active(state)

  def test_initial_input_not_blocked(self):
    """Fresh state allows input."""
    state = create_orchestrator_state()
    assert not is_input_blocked(state)

  def test_initial_color_normal(self):
    """Fresh state has default normal color."""
    state = create_orchestrator_state()
    # Default normal color from ColorEffectStatus
    assert get_current_color(state) == (0.2, 0.8, 0.9)


class TestContactHandling:
  """Tests for contact event processing."""

  def test_contact_starts_recovery(self):
    """Contact event initiates recovery tracking."""
    state = create_orchestrator_state()

    state = handle_contact_event(
      state,
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(1.0, 0.0, 0.0),
      repulsion_force=(10.0, 0.0, 0.0),
      deflection_amount=0.1,
    )

    assert is_active(state)

  def test_contact_locks_input(self):
    """Contact event locks keyboard input."""
    state = create_orchestrator_state()

    state = handle_contact_event(
      state,
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(1.0, 0.0, 0.0),
      repulsion_force=(10.0, 0.0, 0.0),
    )

    assert is_input_blocked(state)

  def test_contact_triggers_shock_color(self):
    """Contact event changes color to shock."""
    colors = ColorConfig(shock_color=(1.0, 0.0, 0.0))
    state = create_orchestrator_state(color_config=colors)

    state = handle_contact_event(
      state,
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(1.0, 0.0, 0.0),
      repulsion_force=(10.0, 0.0, 0.0),
    )

    assert get_current_color(state) == (1.0, 0.0, 0.0)

  def test_contact_increments_counter(self):
    """Contact event increments contact count."""
    state = create_orchestrator_state()
    assert state.total_contacts == 0

    state = handle_contact_event(
      state,
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(1.0, 0.0, 0.0),
      repulsion_force=(10.0, 0.0, 0.0),
    )

    assert state.total_contacts == 1


class TestFrameUpdate:
  """Tests for frame-by-frame recovery updates."""

  def test_update_inactive_returns_zero(self):
    """No displacement when recovery not active."""
    state = create_orchestrator_state()

    new_state, displacement = update_frame(
      state,
      creature_pos=(10.0, 0.0, 0.0),
      surface_pos=(0.0, 0.0, 0.0),
      delta_time=0.016,
    )

    assert displacement == (0.0, 0.0, 0.0)

  def test_update_during_recovery_returns_displacement(self):
    """Active recovery produces velocity displacement."""
    state = create_orchestrator_state()

    # Trigger contact with repulsion
    state = handle_contact_event(
      state,
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(0.1, 0.0, 0.0),
      repulsion_force=(100.0, 0.0, 0.0),
    )

    new_state, displacement = update_frame(
      state,
      creature_pos=(1.0, 0.0, 0.0),
      surface_pos=(0.0, 0.0, 0.0),
      delta_time=0.016,
    )

    # Should have some X displacement from velocity
    assert displacement[0] > 0.0


class TestReset:
  """Tests for state reset."""

  def test_reset_clears_recovery(self):
    """Reset returns to inactive state."""
    state = create_orchestrator_state()
    state = handle_contact_event(
      state,
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(1.0, 0.0, 0.0),
      repulsion_force=(10.0, 0.0, 0.0),
    )

    assert is_active(state)

    state = reset_orchestrator_state(state)

    assert not is_active(state)
    assert not is_input_blocked(state)


class TestStatusSummary:
  """Tests for status reporting."""

  def test_summary_contains_key_info(self):
    """Status summary includes relevant information."""
    state = create_orchestrator_state()
    summary = get_status_summary(state)

    assert "Recovery:" in summary
    assert "Input:" in summary
    assert "Color:" in summary


class TestRecoveryOrchestrator:
  """Tests for RecoveryOrchestrator controller class."""

  def test_create_orchestrator(self):
    """Can create orchestrator instance."""
    orchestrator = RecoveryOrchestrator()
    assert orchestrator is not None

  def test_initial_state_properties(self):
    """Initial properties reflect idle state."""
    orchestrator = RecoveryOrchestrator()

    assert not orchestrator.is_recovery_active
    assert not orchestrator.is_input_locked
    assert orchestrator.total_contacts == 0
    assert orchestrator.total_recoveries == 0

  def test_handle_contact_manual(self):
    """Manual contact handling works."""
    orchestrator = RecoveryOrchestrator()

    orchestrator.handle_contact(
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(1.0, 0.0, 0.0),
      repulsion_force=(50.0, 0.0, 0.0),
    )

    assert orchestrator.is_recovery_active
    assert orchestrator.is_input_locked
    assert orchestrator.total_contacts == 1

  def test_update_returns_displacement(self):
    """Update during recovery returns displacement."""
    orchestrator = RecoveryOrchestrator()

    orchestrator.handle_contact(
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(0.1, 0.0, 0.0),
      repulsion_force=(100.0, 0.0, 0.0),
    )

    displacement = orchestrator.update(
      creature_pos=(1.0, 0.0, 0.0),
      delta_time=0.016,
    )

    assert displacement[0] > 0.0

  def test_reset_clears_state(self):
    """Reset returns to initial state."""
    orchestrator = RecoveryOrchestrator()

    orchestrator.handle_contact(
      contact_point=(0.0, 0.0, 0.0),
      surface_normal=(1.0, 0.0, 0.0),
      creature_pos=(1.0, 0.0, 0.0),
      repulsion_force=(10.0, 0.0, 0.0),
    )

    orchestrator.reset()

    assert not orchestrator.is_recovery_active
    assert not orchestrator.is_input_locked

  def test_status_report(self):
    """Status report returns string."""
    orchestrator = RecoveryOrchestrator()
    status = orchestrator.get_status()

    assert isinstance(status, str)
    assert len(status) > 0

  def test_recovery_callback(self):
    """Recovery callback fires on completion."""
    callback_counts = []

    def on_recovery(count):
      callback_counts.append(count)

    orchestrator = RecoveryOrchestrator()
    orchestrator.set_recovery_callback(on_recovery)

    # Note: Full completion test would require extensive
    # simulation - this tests callback registration
    assert orchestrator._on_recovery_complete is not None
