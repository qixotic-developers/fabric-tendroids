"""
Creature Input Helpers - Keyboard input filtering for repel state

Pure functions for filtering keyboard input based on input lock state.
When locked, keyboard input returns all-false (no movement from player),
allowing only repulsion forces to move the creature.

Implements LTEND-28: Disable keyboard controls during repel.
"""

from typing import Dict

from ..contact.input_lock_helpers import InputLockStatus, is_input_locked


# Type alias for keyboard state dictionary
KeyboardState = Dict[str, bool]


def get_null_keyboard_state() -> KeyboardState:
    """
    Return keyboard state with all keys unpressed.
    
    Used when input is locked to prevent player movement.
    """
    return {
        'forward': False,
        'backward': False,
        'left': False,
        'right': False,
        'up': False,
        'down': False,
    }


def filter_keyboard_by_lock(
    keyboard_state: KeyboardState,
    lock_status: InputLockStatus,
) -> KeyboardState:
    """
    Filter keyboard state based on input lock.
    
    When locked, returns null state (no keys pressed).
    When unlocked, returns original keyboard state.
    
    Args:
        keyboard_state: Raw keyboard input state
        lock_status: Current input lock status
    
    Returns:
        Filtered keyboard state (null if locked)
    """
    if is_input_locked(lock_status):
        return get_null_keyboard_state()
    return keyboard_state


def should_process_keyboard(lock_status: InputLockStatus) -> bool:
    """
    Check if keyboard input should be processed.
    
    Args:
        lock_status: Current input lock status
    
    Returns:
        True if keyboard should be processed, False if locked
    """
    return not is_input_locked(lock_status)


def get_movement_from_filtered_keys(
    keyboard_state: KeyboardState,
    acceleration_rate: float,
    dt: float,
) -> tuple:
    """
    Calculate movement acceleration from filtered keyboard state.
    
    Args:
        keyboard_state: Filtered keyboard state
        acceleration_rate: Acceleration in units/sec²
        dt: Delta time in seconds
    
    Returns:
        Tuple of (ax, ay, az) acceleration components
    """
    ax, ay, az = 0.0, 0.0, 0.0
    
    # Horizontal movement (X-axis)
    if keyboard_state.get('left', False):
        ax -= acceleration_rate * dt
    if keyboard_state.get('right', False):
        ax += acceleration_rate * dt
    
    # Forward/backward (Z-axis)
    if keyboard_state.get('forward', False):
        az -= acceleration_rate * dt
    if keyboard_state.get('backward', False):
        az += acceleration_rate * dt
    
    # Vertical (Y-axis)
    if keyboard_state.get('up', False):
        ay += acceleration_rate * dt
    if keyboard_state.get('down', False):
        ay -= acceleration_rate * dt
    
    return (ax, ay, az)
