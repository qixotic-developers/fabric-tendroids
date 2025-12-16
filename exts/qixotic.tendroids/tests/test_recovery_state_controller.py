"""
Tests for Recovery State Controller

Tests the unified recovery completion detection and input unlock.

TEND-32: Re-enable controls after recovery complete.
TEND-129: Add unit tests for recovery completion.
"""

import pytest
import sys
from unittest.mock import MagicMock

# Mock warp and carb before imports
sys.modules['warp'] = MagicMock()
sys.modules['carb'] = MagicMock()

from qixotic.tendroids.recovery.recovery_state_controller import (
    RecoveryCondition,
    RecoveryCompletionStatus,
    create_completion_status,
    check_color_condition,
    check_velocity_condition,
    should_unlock_input,
    process_recovery_completion,
    start_recovery_lock,
    get_completion_summary,
    is_recovery_complete,
    get_pending_conditions,
    get_blocking_condition,
)
from qixotic.tendroids.contact.color_effect_helpers import (
    ColorEffectState,
    ColorEffectStatus,
)
from qixotic.tendroids.contact.velocity_fade_helpers import (
    VelocityFadeStatus,
)
from qixotic.tendroids.contact.input_lock_helpers import (
    InputLockStatus,
    InputLockReason,
)


class TestRecoveryCompletionStatus:
    """Tests for RecoveryCompletionStatus dataclass."""
    
    def test_default_status_not_complete(self):
        """Default status is not complete (distance not cleared)."""
        status = RecoveryCompletionStatus()
        assert not status.is_complete
    
    def test_all_true_is_complete(self):
        """Status with all conditions True is complete."""
        status = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        assert status.is_complete
    
    def test_one_false_not_complete(self):
        """Status with any condition False is not complete."""
        # Distance not cleared
        status = RecoveryCompletionStatus(
            distance_cleared=False,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        assert not status.is_complete
        
        # Color not normal
        status = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=False,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        assert not status.is_complete
    
    def test_pending_conditions(self):
        """Pending conditions list is accurate."""
        status = RecoveryCompletionStatus(
            distance_cleared=False,
            color_normal=True,
            velocity_stopped=False,
            tendroid_at_rest=True,
        )
        pending = status.pending_conditions
        
        assert RecoveryCondition.DISTANCE_CLEARED in pending
        assert RecoveryCondition.VELOCITY_STOPPED in pending
        assert RecoveryCondition.COLOR_NORMAL not in pending
        assert RecoveryCondition.TENDROID_AT_REST not in pending
    
    def test_completion_progress(self):
        """Completion progress reflects met conditions."""
        # No conditions met (but velocity/tendroid default True)
        status = RecoveryCompletionStatus(
            distance_cleared=False,
            color_normal=False,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        assert status.completion_progress == 0.5  # 2/4
        
        # All conditions met
        status = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        assert status.completion_progress == 1.0


class TestCreateCompletionStatus:
    """Tests for creating completion status."""
    
    def test_default_rest_tolerance(self):
        """Default rest tolerance is set."""
        status = create_completion_status()
        assert status.rest_tolerance == 0.01
    
    def test_custom_rest_tolerance(self):
        """Custom rest tolerance is applied."""
        status = create_completion_status(rest_tolerance=0.05)
        assert status.rest_tolerance == 0.05


class TestCheckColorCondition:
    """Tests for color condition checking."""
    
    def test_normal_state_is_true(self):
        """NORMAL color state returns True."""
        color_status = ColorEffectStatus(state=ColorEffectState.NORMAL)
        assert check_color_condition(color_status) is True
    
    def test_shocked_state_is_false(self):
        """SHOCKED color state returns False."""
        color_status = ColorEffectStatus(state=ColorEffectState.SHOCKED)
        assert check_color_condition(color_status) is False
    
    def test_recovering_state_is_false(self):
        """RECOVERING color state returns False."""
        color_status = ColorEffectStatus(state=ColorEffectState.RECOVERING)
        assert check_color_condition(color_status) is False


class TestCheckVelocityCondition:
    """Tests for velocity condition checking."""
    
    def test_none_velocity_is_true(self):
        """None velocity status returns True."""
        assert check_velocity_condition(None) is True
    
    def test_stopped_velocity_is_true(self):
        """Stopped velocity returns True."""
        velocity_status = VelocityFadeStatus(is_stopped=True, is_active=False)
        assert check_velocity_condition(velocity_status) is True
    
    def test_active_velocity_is_false(self):
        """Active velocity returns False."""
        velocity_status = VelocityFadeStatus(
            velocity_x=1.0,
            is_stopped=False,
            is_active=True,
        )
        assert check_velocity_condition(velocity_status) is False


class TestShouldUnlockInput:
    """Tests for input unlock decision."""
    
    def test_complete_and_locked_should_unlock(self):
        """Complete recovery with locked input should unlock."""
        completion = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        lock_status = InputLockStatus(
            is_locked=True,
            reason=InputLockReason.RECOVERING,
        )
        
        assert should_unlock_input(completion, lock_status) is True
    
    def test_incomplete_should_not_unlock(self):
        """Incomplete recovery should not unlock."""
        completion = RecoveryCompletionStatus(
            distance_cleared=False,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        lock_status = InputLockStatus(is_locked=True)
        
        assert should_unlock_input(completion, lock_status) is False
    
    def test_already_unlocked_should_not_unlock(self):
        """Already unlocked input should not trigger unlock."""
        completion = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        lock_status = InputLockStatus(is_locked=False)
        
        assert should_unlock_input(completion, lock_status) is False


class TestStartRecoveryLock:
    """Tests for starting recovery lock."""
    
    def test_locks_input(self):
        """Start recovery lock locks input."""
        status = InputLockStatus(is_locked=False)
        new_status = start_recovery_lock(status)
        
        assert new_status.is_locked
        assert new_status.reason == InputLockReason.CONTACT
    
    def test_increments_lock_count(self):
        """Lock count is incremented."""
        status = InputLockStatus(is_locked=False, lock_count=5)
        new_status = start_recovery_lock(status)
        
        assert new_status.lock_count == 6


class TestGetCompletionSummary:
    """Tests for completion summary string."""
    
    def test_complete_summary(self):
        """Complete status shows COMPLETE."""
        status = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        summary = get_completion_summary(status)
        
        assert "COMPLETE" in summary
        assert "✓" in summary
    
    def test_pending_summary(self):
        """Pending status shows PENDING and crosses."""
        status = RecoveryCompletionStatus(
            distance_cleared=False,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        summary = get_completion_summary(status)
        
        assert "PENDING" in summary
        assert "✗" in summary


class TestQueryFunctions:
    """Tests for query helper functions."""
    
    def test_is_recovery_complete(self):
        """is_recovery_complete matches is_complete property."""
        complete = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        incomplete = RecoveryCompletionStatus(
            distance_cleared=False,
        )
        
        assert is_recovery_complete(complete) is True
        assert is_recovery_complete(incomplete) is False
    
    def test_get_pending_conditions(self):
        """get_pending_conditions returns pending list."""
        status = RecoveryCompletionStatus(
            distance_cleared=False,
            color_normal=False,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        pending = get_pending_conditions(status)
        
        assert len(pending) == 2
    
    def test_get_blocking_condition_returns_first(self):
        """get_blocking_condition returns first pending."""
        status = RecoveryCompletionStatus(
            distance_cleared=False,
            color_normal=False,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        blocking = get_blocking_condition(status)
        
        assert blocking == RecoveryCondition.DISTANCE_CLEARED
    
    def test_get_blocking_condition_none_when_complete(self):
        """get_blocking_condition returns None when complete."""
        status = RecoveryCompletionStatus(
            distance_cleared=True,
            color_normal=True,
            velocity_stopped=True,
            tendroid_at_rest=True,
        )
        blocking = get_blocking_condition(status)
        
        assert blocking is None


class TestRecoveryConditionEnum:
    """Tests for RecoveryCondition enum."""
    
    def test_all_conditions_defined(self):
        """All four conditions are defined."""
        conditions = list(RecoveryCondition)
        assert len(conditions) == 4
        
        assert RecoveryCondition.DISTANCE_CLEARED in conditions
        assert RecoveryCondition.COLOR_NORMAL in conditions
        assert RecoveryCondition.VELOCITY_STOPPED in conditions
        assert RecoveryCondition.TENDROID_AT_REST in conditions
