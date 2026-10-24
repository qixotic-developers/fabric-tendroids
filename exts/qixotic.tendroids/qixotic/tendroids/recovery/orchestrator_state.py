"""
Orchestrator State - State container for recovery subsystems

Defines the OrchestratorState dataclass and query functions.

Implements TEND-130: Integrate recovery system modules into runtime.
"""

from dataclasses import dataclass
from typing import Tuple

from ..contact.color_effect_helpers import (
    ColorConfig,
    ColorEffectStatus,
)
from ..contact.velocity_fade_helpers import (
    VelocityFadeConfig,
    VelocityFadeStatus,
)
from ..contact.input_lock_helpers import InputLockStatus
from .recovery_integration_helpers import (
    RecoveryContext,
    create_recovery_context,
    is_recovery_in_progress,
)
from .recovery_state_controller import (
    RecoveryCompletionStatus,
    create_completion_status,
    get_completion_summary,
)
from ..proximity.proximity_config import ApproachParameters, DEFAULT_APPROACH_PARAMS


@dataclass
class OrchestratorState:
    """
    Combined state for all recovery subsystems.
    
    Single container holding all state needed for recovery coordination.
    """
    # Recovery tracking
    recovery_context: RecoveryContext
    completion_status: RecoveryCompletionStatus
    
    # Effect states
    color_status: ColorEffectStatus
    velocity_status: VelocityFadeStatus
    input_lock: InputLockStatus
    
    # Configuration
    color_config: ColorConfig
    velocity_config: VelocityFadeConfig
    approach_params: ApproachParameters
    
    # Metrics
    total_contacts: int = 0
    total_recoveries: int = 0


def create_orchestrator_state(
    approach_params: ApproachParameters = None,
    color_config: ColorConfig = None,
    velocity_config: VelocityFadeConfig = None,
) -> OrchestratorState:
    """
    Create initial orchestrator state with all subsystems.
    
    Args:
        approach_params: Proximity/recovery parameters
        color_config: Color effect configuration
        velocity_config: Velocity fade configuration
        
    Returns:
        Fresh orchestrator state ready for runtime
    """
    params = approach_params or DEFAULT_APPROACH_PARAMS
    colors = color_config or ColorConfig()
    velocity = velocity_config or VelocityFadeConfig()
    
    return OrchestratorState(
        recovery_context=create_recovery_context(params),
        completion_status=create_completion_status(),
        color_status=ColorEffectStatus(),
        velocity_status=VelocityFadeStatus(),
        input_lock=InputLockStatus(),
        color_config=colors,
        velocity_config=velocity,
        approach_params=params,
        total_contacts=0,
        total_recoveries=0,
    )


def reset_orchestrator_state(
    state: OrchestratorState,
) -> OrchestratorState:
    """Reset all subsystems to initial state."""
    return create_orchestrator_state(
        approach_params=state.approach_params,
        color_config=state.color_config,
        velocity_config=state.velocity_config,
    )


def is_active(state: OrchestratorState) -> bool:
    """Check if recovery is currently in progress."""
    return is_recovery_in_progress(state.recovery_context)


def is_input_blocked(state: OrchestratorState) -> bool:
    """Check if keyboard input should be blocked."""
    return state.input_lock.is_locked


def get_current_color(state: OrchestratorState) -> Tuple[float, float, float]:
    """Get current creature color."""
    return state.color_status.current_color


def get_status_summary(state: OrchestratorState) -> str:
    """Get human-readable status for debugging."""
    lines = [
        f"Recovery: {'ACTIVE' if is_active(state) else 'IDLE'}",
        f"Input: {'LOCKED' if is_input_blocked(state) else 'UNLOCKED'}",
        f"Color: {state.color_status.state.name}",
        f"Velocity: {state.velocity_status.speed:.3f} m/s",
        get_completion_summary(state.completion_status),
        f"Stats: {state.total_contacts} contacts, {state.total_recoveries} recoveries",
    ]
    return " | ".join(lines)
