"""
Tests for Creature Input Helpers (LTEND-28)

Tests keyboard filtering and movement calculation.
"""

from qixotic.tendroids.contact.input_lock_helpers import (
  InputLockReason,
  InputLockStatus,
)
from qixotic.tendroids.controllers.creature_input_helpers import (filter_keyboard_by_lock,
                                                                  get_movement_from_filtered_keys,
                                                                  get_null_keyboard_state, should_process_keyboard)


class TestGetNullKeyboardState:
  """Tests for get_null_keyboard_state."""

  def test_returns_all_false(self):
    """Null state should have all keys unpressed."""
    result = get_null_keyboard_state()

    assert result['forward'] is False
    assert result['backward'] is False
    assert result['left'] is False
    assert result['right'] is False
    assert result['up'] is False
    assert result['down'] is False

  def test_has_all_required_keys(self):
    """Should have all six direction keys."""
    result = get_null_keyboard_state()

    expected_keys = { 'forward', 'backward', 'left', 'right', 'up', 'down' }
    assert set(result.keys()) == expected_keys


class TestFilterKeyboardByLock:
  """Tests for filter_keyboard_by_lock."""

  def test_returns_null_when_locked(self):
    """Locked state should return null keyboard."""
    keyboard = {
      'forward': True, 'backward': False,
      'left': True, 'right': False,
      'up': True, 'down': False
    }
    lock_status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.CONTACT
    )

    result = filter_keyboard_by_lock(keyboard, lock_status)

    assert result['forward'] is False
    assert result['left'] is False
    assert result['up'] is False

  def test_returns_original_when_unlocked(self):
    """Unlocked state should return original keyboard."""
    keyboard = {
      'forward': True, 'backward': False,
      'left': True, 'right': False,
      'up': True, 'down': False
    }
    lock_status = InputLockStatus()  # Unlocked

    result = filter_keyboard_by_lock(keyboard, lock_status)

    assert result['forward'] is True
    assert result['left'] is True
    assert result['up'] is True
    assert result['backward'] is False


class TestShouldProcessKeyboard:
  """Tests for should_process_keyboard."""

  def test_true_when_unlocked(self):
    """Should return True when unlocked."""
    lock_status = InputLockStatus()
    assert should_process_keyboard(lock_status) is True

  def test_false_when_locked(self):
    """Should return False when locked."""
    lock_status = InputLockStatus(
      is_locked=True,
      reason=InputLockReason.REPELLING
    )
    assert should_process_keyboard(lock_status) is False


class TestGetMovementFromFilteredKeys:
  """Tests for get_movement_from_filtered_keys."""

  def test_no_movement_with_null_keys(self):
    """Null keys should produce zero movement."""
    keys = get_null_keyboard_state()
    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 0.016)

    assert ax == 0.0
    assert ay == 0.0
    assert az == 0.0

  def test_forward_produces_negative_z(self):
    """Forward key should produce negative Z acceleration."""
    keys = get_null_keyboard_state()
    keys['forward'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 1.0)

    assert ax == 0.0
    assert ay == 0.0
    assert az < 0.0
    assert az == -100.0

  def test_backward_produces_positive_z(self):
    """Backward key should produce positive Z acceleration."""
    keys = get_null_keyboard_state()
    keys['backward'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 1.0)

    assert az > 0.0
    assert az == 100.0

  def test_left_produces_negative_x(self):
    """Left key should produce negative X acceleration."""
    keys = get_null_keyboard_state()
    keys['left'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 1.0)

    assert ax < 0.0
    assert ax == -100.0

  def test_right_produces_positive_x(self):
    """Right key should produce positive X acceleration."""
    keys = get_null_keyboard_state()
    keys['right'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 1.0)

    assert ax > 0.0
    assert ax == 100.0

  def test_up_produces_positive_y(self):
    """Up key should produce positive Y acceleration."""
    keys = get_null_keyboard_state()
    keys['up'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 1.0)

    assert ay > 0.0
    assert ay == 100.0

  def test_down_produces_negative_y(self):
    """Down key should produce negative Y acceleration."""
    keys = get_null_keyboard_state()
    keys['down'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 1.0)

    assert ay < 0.0
    assert ay == -100.0

  def test_dt_scales_acceleration(self):
    """Delta time should scale acceleration."""
    keys = get_null_keyboard_state()
    keys['forward'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 0.5)

    assert az == -50.0  # 100 * 0.5

  def test_multiple_keys(self):
    """Multiple keys should combine."""
    keys = get_null_keyboard_state()
    keys['forward'] = True
    keys['right'] = True
    keys['up'] = True

    ax, ay, az = get_movement_from_filtered_keys(keys, 100.0, 1.0)

    assert ax == 100.0
    assert ay == 100.0
    assert az == -100.0
