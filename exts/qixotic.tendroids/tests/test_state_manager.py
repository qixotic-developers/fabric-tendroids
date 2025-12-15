"""
Tests for Proximity State Manager (TEND-18)

Verifies state machine transitions, event callbacks, and entity tracking.

Run with: python -m pytest tests/test_state_manager.py -v
"""

import pytest
from unittest.mock import MagicMock


class TestProximityState:
    """TEND-74: Test ProximityState enum."""
    
    def test_all_states_defined(self):
        """Verify all expected states exist."""
        from qixotic.tendroids.proximity import ProximityState
        
        assert hasattr(ProximityState, 'IDLE')
        assert hasattr(ProximityState, 'APPROACHING')
        assert hasattr(ProximityState, 'CONTACT')
        assert hasattr(ProximityState, 'RETREATING')
        assert hasattr(ProximityState, 'RECOVERED')
    
    def test_states_are_distinct(self):
        """Verify each state has unique value."""
        from qixotic.tendroids.proximity import ProximityState
        
        states = [s.value for s in ProximityState]
        assert len(states) == len(set(states))
    
    def test_valid_transition_same_state(self):
        """Staying in same state is always valid."""
        from qixotic.tendroids.proximity import ProximityState, is_valid_transition
        
        for state in ProximityState:
            assert is_valid_transition(state, state) is True
    
    def test_valid_transition_idle_to_approaching(self):
        """IDLE -> APPROACHING is valid."""
        from qixotic.tendroids.proximity import ProximityState, is_valid_transition
        
        assert is_valid_transition(
            ProximityState.IDLE, ProximityState.APPROACHING
        ) is True
    
    def test_invalid_transition_idle_to_retreating(self):
        """IDLE -> RETREATING is invalid (must go through contact)."""
        from qixotic.tendroids.proximity import ProximityState, is_valid_transition
        
        assert is_valid_transition(
            ProximityState.IDLE, ProximityState.RETREATING
        ) is False
    
    def test_get_state_priority(self):
        """Contact should have highest priority."""
        from qixotic.tendroids.proximity import ProximityState, get_state_priority
        
        assert get_state_priority(ProximityState.CONTACT) > \
               get_state_priority(ProximityState.IDLE)


class TestStateTransitions:
    """TEND-75: Test state transition logic."""
    
    def test_idle_to_approaching(self):
        """Entering detection range transitions to APPROACHING."""
        from qixotic.tendroids.proximity import (
            ProximityState, determine_next_state, ApproachParameters
        )
        
        params = ApproachParameters()
        next_state, changed = determine_next_state(
            ProximityState.IDLE,
            surface_distance=0.5,  # Within detection (1.0)
            params=params,
        )
        
        assert next_state == ProximityState.APPROACHING
        assert changed is True
    
    def test_approaching_to_contact(self):
        """Reaching epsilon triggers CONTACT."""
        from qixotic.tendroids.proximity import (
            ProximityState, determine_next_state, ApproachParameters
        )
        
        params = ApproachParameters()
        next_state, changed = determine_next_state(
            ProximityState.APPROACHING,
            surface_distance=0.03,  # Below epsilon (0.04)
            params=params,
        )
        
        assert next_state == ProximityState.CONTACT
        assert changed is True
    
    def test_contact_to_retreating(self):
        """Moving past epsilon triggers RETREATING."""
        from qixotic.tendroids.proximity import (
            ProximityState, determine_next_state, ApproachParameters
        )
        
        params = ApproachParameters()
        next_state, changed = determine_next_state(
            ProximityState.CONTACT,
            surface_distance=0.05,  # Past epsilon (0.04)
            params=params,
        )
        
        assert next_state == ProximityState.RETREATING
        assert changed is True
    
    def test_retreating_to_recovered(self):
        """Passing approach_minimum triggers RECOVERED."""
        from qixotic.tendroids.proximity import (
            ProximityState, determine_next_state, ApproachParameters
        )
        
        params = ApproachParameters()
        next_state, changed = determine_next_state(
            ProximityState.RETREATING,
            surface_distance=0.20,  # Past minimum (0.15)
            params=params,
        )
        
        assert next_state == ProximityState.RECOVERED
        assert changed is True
    
    def test_outside_detection_always_idle(self):
        """Any state goes to IDLE when outside detection range."""
        from qixotic.tendroids.proximity import (
            ProximityState, determine_next_state, ApproachParameters
        )
        
        params = ApproachParameters()
        
        for state in [ProximityState.APPROACHING, ProximityState.RECOVERED]:
            next_state, _ = determine_next_state(
                state,
                surface_distance=2.0,  # Beyond detection (1.0)
                params=params,
            )
            assert next_state == ProximityState.IDLE


class TestStateChangeEvent:
    """Test StateChangeEvent dataclass."""
    
    def test_is_contact_enter(self):
        """Verify is_contact_enter property."""
        from qixotic.tendroids.proximity import ProximityState, StateChangeEvent
        
        event = StateChangeEvent(
            creature_idx=0,
            tendroid_idx=0,
            previous_state=ProximityState.APPROACHING,
            new_state=ProximityState.CONTACT,
            surface_distance=0.02,
        )
        
        assert event.is_contact_enter is True
        assert event.is_contact_exit is False
    
    def test_is_contact_exit(self):
        """Verify is_contact_exit property."""
        from qixotic.tendroids.proximity import ProximityState, StateChangeEvent
        
        event = StateChangeEvent(
            creature_idx=0,
            tendroid_idx=0,
            previous_state=ProximityState.CONTACT,
            new_state=ProximityState.RETREATING,
            surface_distance=0.05,
        )
        
        assert event.is_contact_exit is True
        assert event.is_contact_enter is False
    
    def test_is_detection_enter(self):
        """Verify is_detection_enter property."""
        from qixotic.tendroids.proximity import ProximityState, StateChangeEvent
        
        event = StateChangeEvent(
            creature_idx=0,
            tendroid_idx=0,
            previous_state=ProximityState.IDLE,
            new_state=ProximityState.APPROACHING,
            surface_distance=0.8,
        )
        
        assert event.is_detection_enter is True


class TestProximityStateManager:
    """TEND-76: Test ProximityStateManager with callbacks."""
    
    @pytest.fixture
    def manager(self):
        """Create fresh state manager."""
        from qixotic.tendroids.proximity import ProximityStateManager
        return ProximityStateManager()
    
    def test_initial_state_is_idle(self, manager):
        """New entities start in IDLE state."""
        from qixotic.tendroids.proximity import ProximityState
        
        state = manager.get_state(creature_idx=0, tendroid_idx=0)
        assert state == ProximityState.IDLE
    
    def test_update_returns_event_on_change(self, manager):
        """Update returns event when state changes."""
        event = manager.update(
            creature_idx=0,
            tendroid_idx=0,
            surface_distance=0.5,  # Within detection
        )
        
        assert event is not None
        assert event.new_state.name == "APPROACHING"
    
    def test_update_returns_none_when_no_change(self, manager):
        """Update returns None when state unchanged."""
        # First update - causes transition
        manager.update(0, 0, surface_distance=0.5)
        
        # Second update - same zone, no transition
        event = manager.update(0, 0, surface_distance=0.5)
        assert event is None
    
    def test_callback_on_contact_enter(self, manager):
        """on_contact_enter callback fires on contact."""
        callback = MagicMock()
        manager.on_contact_enter(callback)
        
        # Move into contact
        manager.update(0, 0, surface_distance=0.5)   # APPROACHING
        manager.update(0, 0, surface_distance=0.02)  # CONTACT
        
        assert callback.called
        event = callback.call_args[0][0]
        assert event.is_contact_enter is True
    
    def test_callback_on_contact_exit(self, manager):
        """on_contact_exit callback fires when leaving contact."""
        callback = MagicMock()
        manager.on_contact_exit(callback)
        
        # Enter then exit contact
        manager.update(0, 0, surface_distance=0.02)  # CONTACT
        manager.update(0, 0, surface_distance=0.10)  # RETREATING
        
        assert callback.called
        event = callback.call_args[0][0]
        assert event.is_contact_exit is True
    
    def test_callback_on_recovered(self, manager):
        """on_recovered callback fires when past minimum."""
        callback = MagicMock()
        manager.on_recovered(callback)
        
        # Full cycle: contact -> retreat -> recover
        manager.update(0, 0, surface_distance=0.02)  # CONTACT
        manager.update(0, 0, surface_distance=0.10)  # RETREATING
        manager.update(0, 0, surface_distance=0.20)  # RECOVERED
        
        assert callback.called
    
    def test_multiple_entities_tracked_independently(self, manager):
        """Different creature-tendroid pairs have independent state."""
        from qixotic.tendroids.proximity import ProximityState
        
        # Entity 0,0 enters contact
        manager.update(0, 0, surface_distance=0.02)
        
        # Entity 1,0 stays idle (never updated with close distance)
        state_0_0 = manager.get_state(0, 0)
        state_1_0 = manager.get_state(1, 0)
        
        assert state_0_0 == ProximityState.CONTACT
        assert state_1_0 == ProximityState.IDLE
    
    def test_reset_clears_all_entities(self, manager):
        """Reset removes all tracked entities."""
        from qixotic.tendroids.proximity import ProximityState
        
        manager.update(0, 0, surface_distance=0.02)  # CONTACT
        manager.reset()
        
        # After reset, entity starts fresh as IDLE
        state = manager.get_state(0, 0)
        assert state == ProximityState.IDLE
    
    def test_clear_callbacks(self, manager):
        """clear_callbacks removes all registered callbacks."""
        callback = MagicMock()
        manager.on_contact_enter(callback)
        manager.clear_callbacks()
        
        manager.update(0, 0, surface_distance=0.02)  # Would trigger
        
        assert not callback.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
