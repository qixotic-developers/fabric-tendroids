"""
Recovery State Controller - Unified recovery completion detection

Orchestrates all recovery completion conditions and coordinates
input unlock when recovery is fully complete.

Completion requires ALL conditions:
- Creature beyond approach_minimum distance
- Color returned to normal
- Repel velocity faded to zero
- Tendroid back to un-bent (rest) position

Implements TEND-32: Re-enable controls after recovery complete.
Implements TEND-126: Create recovery_state_controller.py module.
Implements TEND-127: Implement recovery completion conditions check.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional

from ..contact.color_effect_helpers import ColorEffectState, ColorEffectStatus
from ..contact.velocity_fade_helpers import VelocityFadeStatus
from ..contact.input_lock_helpers import (
    InputLockStatus,
    InputLockReason,
    lock_input_on_contact,
    update_lock_reason,
    unlock_input_on_recovery_complete,
)
from .recovery_integration_helpers import RecoveryContext


class RecoveryCondition(Enum):
    """Individual recovery completion conditions."""
    DISTANCE_CLEARED = auto()      # Creature beyond approach_minimum
    COLOR_NORMAL = auto()          # Color returned to normal
    VELOCITY_STOPPED = auto()      # Repel velocity faded to zero
    TENDROID_AT_REST = auto()      # Tendroid un-bent


@dataclass
class RecoveryCompletionStatus:
    """
    Status of all recovery completion conditions.
    
    All conditions must be True for recovery to be complete.
    """
    distance_cleared: bool = False
    color_normal: bool = False
    velocity_stopped: bool = True   # Default True (no velocity = stopped)
    tendroid_at_rest: bool = True   # Default True (no deflection = at rest)
    
    # Tolerance for tendroid rest position check
    rest_tolerance: float = 0.01  # Meters
    
    @property
    def is_complete(self) -> bool:
        """Check if all conditions are met for recovery completion."""
        return (
            self.distance_cleared and
            self.color_normal and
            self.velocity_stopped and
            self.tendroid_at_rest
        )
    
    @property
    def pending_conditions(self) -> list:
        """Get list of conditions still pending."""
        pending = []
        if not self.distance_cleared:
            pending.append(RecoveryCondition.DISTANCE_CLEARED)
        if not self.color_normal:
            pending.append(RecoveryCondition.COLOR_NORMAL)
        if not self.velocity_stopped:
            pending.append(RecoveryCondition.VELOCITY_STOPPED)
        if not self.tendroid_at_rest:
            pending.append(RecoveryCondition.TENDROID_AT_REST)
        return pending
    
    @property
    def completion_progress(self) -> float:
        """Get completion progress as 0.0 to 1.0 (count of met conditions)."""
        met = sum([
            self.distance_cleared,
            self.color_normal,
            self.velocity_stopped,
            self.tendroid_at_rest,
        ])
        return met / 4.0


def create_completion_status(
    rest_tolerance: float = 0.01,
) -> RecoveryCompletionStatus:
    """Create initial completion status."""
    return RecoveryCompletionStatus(rest_tolerance=rest_tolerance)


def check_distance_condition(
    recovery_context: RecoveryContext,
) -> bool:
    """
    Check if creature has cleared the approach_minimum distance.
    
    Args:
        recovery_context: Current recovery tracking context
        
    Returns:
        True if creature is beyond threshold
    """
    from .recovery_integration_helpers import is_threshold_crossed
    return is_threshold_crossed(recovery_context)


def check_color_condition(
    color_status: ColorEffectStatus,
) -> bool:
    """
    Check if color has returned to normal.
    
    Args:
        color_status: Current color effect status
        
    Returns:
        True if color is NORMAL
    """
    return color_status.state == ColorEffectState.NORMAL


def check_velocity_condition(
    velocity_status: Optional[VelocityFadeStatus],
) -> bool:
    """
    Check if repel velocity has faded to zero.
    
    Args:
        velocity_status: Current velocity fade status (None = no velocity)
        
    Returns:
        True if velocity is stopped or None
    """
    if velocity_status is None:
        return True
    return velocity_status.is_stopped


def check_tendroid_condition(
    recovery_context: RecoveryContext,
    tolerance: float = 0.01,
) -> bool:
    """
    Check if tendroid has returned to un-bent rest position.
    
    Args:
        recovery_context: Current recovery tracking context
        tolerance: Distance tolerance for "at rest" check
        
    Returns:
        True if tendroid deflection is within tolerance
    """
    from .recovery_integration_helpers import get_surface_deflection
    deflection = get_surface_deflection(recovery_context)
    return abs(deflection) <= tolerance


def update_completion_status(
    status: RecoveryCompletionStatus,
    recovery_context: RecoveryContext,
    color_status: ColorEffectStatus,
    velocity_status: Optional[VelocityFadeStatus] = None,
) -> RecoveryCompletionStatus:
    """
    Update all completion conditions based on current state.
    
    Args:
        status: Current completion status
        recovery_context: Recovery tracking context
        color_status: Color effect status
        velocity_status: Optional velocity fade status
        
    Returns:
        Updated completion status with all conditions checked
    """
    return RecoveryCompletionStatus(
        distance_cleared=check_distance_condition(recovery_context),
        color_normal=check_color_condition(color_status),
        velocity_stopped=check_velocity_condition(velocity_status),
        tendroid_at_rest=check_tendroid_condition(
            recovery_context,
            status.rest_tolerance,
        ),
        rest_tolerance=status.rest_tolerance,
    )


def should_unlock_input(
    completion_status: RecoveryCompletionStatus,
    input_lock_status: InputLockStatus,
) -> bool:
    """
    Determine if input should be unlocked.
    
    Input unlocks when:
    - All recovery conditions are met
    - Input is currently locked
    
    Args:
        completion_status: Current completion status
        input_lock_status: Current input lock status
        
    Returns:
        True if input should be unlocked now
    """
    return (
        completion_status.is_complete and
        input_lock_status.is_locked
    )


def process_recovery_completion(
    completion_status: RecoveryCompletionStatus,
    input_lock_status: InputLockStatus,
    recovery_context: RecoveryContext,
) -> tuple:
    """
    Process recovery completion and update all related state.
    
    Called each frame during recovery. When all conditions are met,
    unlocks input and finalizes recovery.
    
    Args:
        completion_status: Current completion status
        input_lock_status: Current input lock status
        recovery_context: Current recovery context
        
    Returns:
        Tuple of (new_input_lock_status, new_recovery_context, did_complete)
    """
    from .recovery_integration_helpers import finalize_recovery
    
    if should_unlock_input(completion_status, input_lock_status):
        # All conditions met - unlock input and finalize
        new_lock = unlock_input_on_recovery_complete(input_lock_status)
        new_context = finalize_recovery(recovery_context)
        return (new_lock, new_context, True)
    
    # Not complete yet - update lock reason based on phase
    if input_lock_status.is_locked:
        from .recovery_integration_helpers import is_recovery_in_progress
        
        if is_recovery_in_progress(recovery_context):
            new_lock = update_lock_reason(
                input_lock_status,
                InputLockReason.RECOVERING,
            )
        else:
            new_lock = input_lock_status
    else:
        new_lock = input_lock_status
    
    return (new_lock, recovery_context, False)


def start_recovery_lock(
    input_lock_status: InputLockStatus,
) -> InputLockStatus:
    """
    Lock input when recovery begins (on contact).
    
    Args:
        input_lock_status: Current input lock status
        
    Returns:
        Updated status with input locked
    """
    return lock_input_on_contact(input_lock_status)


def get_completion_summary(status: RecoveryCompletionStatus) -> str:
    """
    Get human-readable summary of completion status.
    
    Useful for debugging and UI display.
    """
    conditions = [
        f"Distance: {'✓' if status.distance_cleared else '✗'}",
        f"Color: {'✓' if status.color_normal else '✗'}",
        f"Velocity: {'✓' if status.velocity_stopped else '✗'}",
        f"Tendroid: {'✓' if status.tendroid_at_rest else '✗'}",
    ]
    complete = "COMPLETE" if status.is_complete else "PENDING"
    return f"Recovery {complete} [{', '.join(conditions)}]"


def is_recovery_complete(status: RecoveryCompletionStatus) -> bool:
    """Check if all recovery conditions are met."""
    return status.is_complete


def get_pending_conditions(
    status: RecoveryCompletionStatus,
) -> list:
    """Get list of conditions still pending completion."""
    return status.pending_conditions


def get_blocking_condition(
    status: RecoveryCompletionStatus,
) -> Optional[RecoveryCondition]:
    """
    Get the first condition blocking completion.
    
    Returns None if recovery is complete.
    """
    pending = status.pending_conditions
    return pending[0] if pending else None
