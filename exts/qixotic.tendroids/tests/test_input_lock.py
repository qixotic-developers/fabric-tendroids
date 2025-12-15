"""
Tests for Input Lock Helpers (LTEND-28)

Tests keyboard input disabling during repel state.
"""

from qixotic.tendroids.contact.color_effect_helpers import (
  ColorEffectState,
  ColorEffectStatus,
)
from qixotic.tendroids.contact.input_lock_helpers import (InputLockReason, InputLockStatus, get_lock_reason_name,
                                                          is_input_locked, lock_input_on_contact, should_apply_keyboard,
                                                          sync_lock_from_color_state, unlock_input_on_recovery_complete,
                                                          update_lock_reason)


class TestInputLockStatus:
  """Tests for InputLockStatus dataclass."""

  def test_default_status_is_unlocked(self):
    """Default status should be unlocked."""
    status = InputLockStatus()
    assert status.is_locked is False
    assert status.reason == InputLockReason.NONE
    assert status.lock_count == 0

  def test_locked_status_preserves_count(self):
    """Locked status should preserve lock count."""
    status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.CONTACT,
      lock_count=5
    )
    assert status.is_locked is True
    assert status.lock_count == 5


class TestLockOnContact:
  """Tests for lock_input_on_contact."""

  def test_locks_on_first_contact(self):
    """First contact should lock input."""
    status = InputLockStatus()
    result = lock_input_on_contact(status)

    assert result.is_locked is True
    assert result.reason == InputLockReason.CONTACT
    assert result.lock_count == 1

  def test_increments_lock_count(self):
    """Each contact should increment lock count."""
    status = InputLockStatus(lock_count=2)
    result = lock_input_on_contact(status)

    assert result.lock_count == 3

  def test_relocks_if_already_locked(self):
    """Contact while already locked should increment count."""
    status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.RECOVERING,
      lock_count=1
    )
    result = lock_input_on_contact(status)

    assert result.is_locked is True
    assert result.reason == InputLockReason.CONTACT
    assert result.lock_count == 2


class TestUnlockOnRecoveryComplete:
  """Tests for unlock_input_on_recovery_complete."""

  def test_unlocks_when_locked(self):
    """Should unlock when recovery completes."""
    status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.RECOVERING,
      lock_count=3
    )
    result = unlock_input_on_recovery_complete(status)

    assert result.is_locked is False
    assert result.reason == InputLockReason.NONE
    assert result.lock_count == 3  # Count preserved

  def test_preserves_unlocked_state(self):
    """Already unlocked should stay unlocked."""
    status = InputLockStatus()
    result = unlock_input_on_recovery_complete(status)

    assert result.is_locked is False


class TestUpdateLockReason:
  """Tests for update_lock_reason."""

  def test_updates_reason_when_locked(self):
    """Should update reason when locked."""
    status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.CONTACT,
      lock_count=1
    )
    result = update_lock_reason(status, InputLockReason.REPELLING)

    assert result.is_locked is True
    assert result.reason == InputLockReason.REPELLING

  def test_no_change_when_unlocked(self):
    """Should not change reason when unlocked."""
    status = InputLockStatus()
    result = update_lock_reason(status, InputLockReason.REPELLING)

    assert result.is_locked is False
    assert result.reason == InputLockReason.NONE


class TestSyncFromColorState:
  """Tests for sync_lock_from_color_state."""

  def test_locks_on_shocked_state(self):
    """SHOCKED color state should lock input."""
    lock_status = InputLockStatus()
    color_status = ColorEffectStatus(state=ColorEffectState.SHOCKED)

    result = sync_lock_from_color_state(lock_status, color_status)

    assert result.is_locked is True

  def test_stays_locked_on_recovering(self):
    """RECOVERING should keep input locked."""
    lock_status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.REPELLING,
      lock_count=1
    )
    color_status = ColorEffectStatus(state=ColorEffectState.RECOVERING)

    result = sync_lock_from_color_state(lock_status, color_status)

    assert result.is_locked is True
    assert result.reason == InputLockReason.RECOVERING

  def test_unlocks_on_normal(self):
    """NORMAL color state should unlock input."""
    lock_status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.RECOVERING,
      lock_count=1
    )
    color_status = ColorEffectStatus(state=ColorEffectState.NORMAL)

    result = sync_lock_from_color_state(lock_status, color_status)

    assert result.is_locked is False

  def test_normal_stays_unlocked(self):
    """Already unlocked stays unlocked on NORMAL."""
    lock_status = InputLockStatus()
    color_status = ColorEffectStatus(state=ColorEffectState.NORMAL)

    result = sync_lock_from_color_state(lock_status, color_status)

    assert result.is_locked is False


class TestHelperFunctions:
  """Tests for utility functions."""

  def test_is_input_locked(self):
    """is_input_locked should return lock state."""
    locked = InputLockStatus(is_locked=True, reason=InputLockReason.CONTACT)
    unlocked = InputLockStatus()

    assert is_input_locked(locked) is True
    assert is_input_locked(unlocked) is False

  def test_should_apply_keyboard(self):
    """should_apply_keyboard is inverse of is_locked."""
    locked = InputLockStatus(is_locked=True, reason=InputLockReason.CONTACT)
    unlocked = InputLockStatus()

    assert should_apply_keyboard(locked) is False
    assert should_apply_keyboard(unlocked) is True

  def test_get_lock_reason_name(self):
    """get_lock_reason_name returns readable string."""
    status = InputLockStatus(is_locked=True, reason=InputLockReason.REPELLING)
    assert get_lock_reason_name(status) == "REPELLING"

    unlocked = InputLockStatus()
    assert get_lock_reason_name(unlocked) == "NONE"
