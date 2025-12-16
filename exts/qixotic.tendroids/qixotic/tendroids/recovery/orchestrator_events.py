"""
Orchestrator Events - Contact and frame update handling

Event processing functions for the recovery orchestrator.

Implements TEND-130: Integrate recovery system modules into runtime.
"""

from typing import Optional, Tuple

from ..contact.color_effect_helpers import (
    ColorEffectState,
    trigger_shock,
    start_recovery as start_color_recovery,
    update_recovery as update_color_recovery,
)
from ..contact.velocity_fade_helpers import (
    apply_initial_velocity,
    update_velocity,
    velocity_from_force,
    get_displacement,
)
from ..contact.input_lock_helpers import (
    InputLockReason,
    lock_input_on_contact,
    update_lock_reason,
    unlock_input_on_recovery_complete,
)
from .recovery_integration_helpers import (
    start_recovery_tracking,
    update_recovery,
    finalize_recovery,
    is_recovery_in_progress,
    is_threshold_crossed,
    get_recovery_progress,
)
from .recovery_state_controller import (
    create_completion_status,
    update_completion_status,
    should_unlock_input,
)
from .orchestrator_state import OrchestratorState


def handle_contact_event(
    state: OrchestratorState,
    contact_point: Tuple[float, float, float],
    surface_normal: Tuple[float, float, float],
    creature_pos: Tuple[float, float, float],
    repulsion_force: Tuple[float, float, float],
    deflection_amount: float = 0.0,
) -> OrchestratorState:
    """
    Process contact event and initialize recovery.
    
    Triggers all subsystems in response to creature-tendroid contact:
    - Starts recovery tracking
    - Applies shock color
    - Applies repulsion velocity
    - Locks input
    """
    # Start recovery tracking
    new_context = start_recovery_tracking(
        state.recovery_context,
        contact_point,
        surface_normal,
        creature_pos,
        deflection_amount,
    )
    
    # Trigger shock color
    new_color = trigger_shock(state.color_status, state.color_config)
    
    # Apply repulsion velocity
    velocity = velocity_from_force(repulsion_force)
    new_velocity = apply_initial_velocity(state.velocity_status, velocity)
    
    # Lock input
    new_lock = lock_input_on_contact(state.input_lock)
    
    # Reset completion status
    new_completion = create_completion_status(
        rest_tolerance=state.completion_status.rest_tolerance,
    )
    
    return OrchestratorState(
        recovery_context=new_context,
        completion_status=new_completion,
        color_status=new_color,
        velocity_status=new_velocity,
        input_lock=new_lock,
        color_config=state.color_config,
        velocity_config=state.velocity_config,
        approach_params=state.approach_params,
        total_contacts=state.total_contacts + 1,
        total_recoveries=state.total_recoveries,
    )


def update_frame(
    state: OrchestratorState,
    creature_pos: Tuple[float, float, float],
    surface_pos: Tuple[float, float, float],
    delta_time: float,
    surface_normal: Optional[Tuple[float, float, float]] = None,
) -> Tuple[OrchestratorState, Tuple[float, float, float]]:
    """
    Process one frame of recovery.
    
    Updates all subsystems and checks for completion.
    
    Returns:
        Tuple of (updated_state, displacement)
    """
    if not is_recovery_in_progress(state.recovery_context):
        return (state, (0.0, 0.0, 0.0))
    
    # Update recovery tracking
    new_context = update_recovery(
        state.recovery_context,
        creature_pos,
        surface_pos,
        surface_normal,
    )
    
    # Get recovery progress for color fade
    progress = get_recovery_progress(new_context)
    
    # Update color based on state
    new_color = _update_color_state(state, new_context, progress)
    
    # Update velocity fade
    new_velocity = update_velocity(
        state.velocity_status,
        delta_time,
        state.velocity_config,
    )
    
    # Get displacement for this frame
    displacement = get_displacement(state.velocity_status, delta_time)
    
    # Update completion status
    new_completion = update_completion_status(
        state.completion_status,
        new_context,
        new_color,
        new_velocity,
    )
    
    # Check for completion
    new_lock, new_context, new_recoveries = _check_completion(
        state, new_context, new_completion
    )
    
    return (
        OrchestratorState(
            recovery_context=new_context,
            completion_status=new_completion,
            color_status=new_color,
            velocity_status=new_velocity,
            input_lock=new_lock,
            color_config=state.color_config,
            velocity_config=state.velocity_config,
            approach_params=state.approach_params,
            total_contacts=state.total_contacts,
            total_recoveries=new_recoveries,
        ),
        displacement,
    )


def _update_color_state(state, new_context, progress):
    """Update color based on recovery state."""
    if state.color_status.state == ColorEffectState.SHOCKED:
        if is_threshold_crossed(new_context):
            return start_color_recovery(state.color_status, state.color_config)
    elif state.color_status.state == ColorEffectState.RECOVERING:
        return update_color_recovery(
            state.color_status,
            progress,
            state.color_config,
        )
    return state.color_status


def _check_completion(state, new_context, new_completion):
    """Check and handle recovery completion."""
    new_lock = state.input_lock
    new_recoveries = state.total_recoveries
    
    if should_unlock_input(new_completion, state.input_lock):
        new_context = finalize_recovery(new_context)
        new_lock = unlock_input_on_recovery_complete(state.input_lock)
        new_recoveries += 1
    elif state.input_lock.is_locked:
        new_lock = update_lock_reason(
            state.input_lock,
            InputLockReason.RECOVERING,
        )
    
    return new_lock, new_context, new_recoveries
