"""
Input Lock Helpers - Pure logic for disabling keyboard controls during repel

Provides input lock state tracking during creature-tendroid contact response.
Input is locked on contact, remains locked during repel and recovery,
and unlocks only when recovery completes.

Implements LTEND-28: Disable keyboard controls during repel.
"""

from dataclasses import dataclass
from enum import Enum, auto

from .color_effect_helpers import ColorEffectState, ColorEffectStatus


class InputLockReason(Enum):
  """Reason why input is locked."""
  NONE = auto()  # Input not locked
  CONTACT = auto()  # Initial contact with tendroid
  REPELLING = auto()  # Being pushed away by repulsion force
  RECOVERING = auto()  # Fading back to normal


@dataclass
class InputLockStatus:
  """
  Current status of input lock system.

  Tracks whether keyboard input should be ignored and why.
  """
  is_locked: bool = False
  reason: InputLockReason = InputLockReason.NONE
  lock_count: int = 0  # Total times input was locked


def lock_input_on_contact(
  status: InputLockStatus,
) -> InputLockStatus:
  """
  Lock input when contact occurs.

  Called when creature touches a tendroid. Input remains locked
  until recovery completes.

  Args:
      status: Current input lock status

  Returns:
      Updated status with input locked
  """
  return InputLockStatus(
    is_locked=True,
    reason=InputLockReason.CONTACT,
    lock_count=status.lock_count + 1,
  )


def update_lock_reason(
  status: InputLockStatus,
  reason: InputLockReason,
) -> InputLockStatus:
  """
  Update the reason for input lock.

  Used to transition between CONTACT -> REPELLING -> RECOVERING.

  Args:
      status: Current status
      reason: New lock reason

  Returns:
      Updated status with new reason
  """
  if not status.is_locked:
    return status

  return InputLockStatus(
    is_locked=True,
    reason=reason,
    lock_count=status.lock_count,
  )


def unlock_input_on_recovery_complete(
  status: InputLockStatus,
) -> InputLockStatus:
  """
  Unlock input when recovery completes.

  Called when creature returns to NORMAL state after recovery fade.

  Args:
      status: Current input lock status

  Returns:
      Updated status with input unlocked
  """
  return InputLockStatus(
    is_locked=False,
    reason=InputLockReason.NONE,
    lock_count=status.lock_count,
  )


def sync_lock_from_color_state(
  lock_status: InputLockStatus,
  color_status: ColorEffectStatus,
) -> InputLockStatus:
  """
  Synchronize input lock state from color effect state.

  Provides integration between color system and input lock:
  - SHOCKED -> Input locked (CONTACT or REPELLING)
  - RECOVERING -> Input locked (RECOVERING)
  - NORMAL -> Input unlocked

  Args:
      lock_status: Current input lock status
      color_status: Current color effect status

  Returns:
      Updated input lock status synchronized with color state
  """
  color_state = color_status.state

  if color_state == ColorEffectState.NORMAL:
    # Recovery complete - unlock input
    if lock_status.is_locked:
      return unlock_input_on_recovery_complete(lock_status)
    return lock_status

  elif color_state == ColorEffectState.SHOCKED:
    # Contact occurred - lock input
    if not lock_status.is_locked:
      return lock_input_on_contact(lock_status)
    # Already locked, update reason to REPELLING
    return update_lock_reason(lock_status, InputLockReason.REPELLING)

  elif color_state == ColorEffectState.RECOVERING:
    # In recovery - keep locked with RECOVERING reason
    if not lock_status.is_locked:
      # Shouldn't happen, but handle gracefully
      return InputLockStatus(
        is_locked=True,
        reason=InputLockReason.RECOVERING,
        lock_count=lock_status.lock_count + 1,
      )
    return update_lock_reason(lock_status, InputLockReason.RECOVERING)

  return lock_status


def is_input_locked(status: InputLockStatus) -> bool:
  """Check if keyboard input is currently locked."""
  return status.is_locked


def should_apply_keyboard(status: InputLockStatus) -> bool:
  """Check if keyboard input should be applied to movement."""
  return not status.is_locked


def get_lock_reason_name(status: InputLockStatus) -> str:
  """Get human-readable name of current lock reason."""
  return status.reason.name if status.is_locked else "NONE"
