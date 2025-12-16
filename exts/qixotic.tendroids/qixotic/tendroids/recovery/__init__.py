"""
Recovery Package - Creature recovery after tendroid contact

This package provides helpers for tracking and managing
the creature recovery process after contact with tendroids.

TEND-5: Recovery System epic
TEND-30: Recalculate absolute coordinates (uses relative distances)
TEND-32: Re-enable controls after recovery complete
TEND-130: Integrate recovery system modules into runtime
"""

from .recovery_integration_helpers import (
    RecoveryContext,
    create_recovery_context,
    start_recovery_tracking,
    update_recovery,
    finalize_recovery,
    reset_recovery_context,
    is_recovery_in_progress,
    is_threshold_crossed,
    get_recovery_progress,
    get_current_distance,
    get_surface_deflection,
    map_recovery_phase_to_proximity,
    map_proximity_to_recovery_phase,
)
from .recovery_state_controller import (
    RecoveryCondition,
    RecoveryCompletionStatus,
    create_completion_status,
    check_distance_condition,
    check_color_condition,
    check_velocity_condition,
    check_tendroid_condition,
    update_completion_status,
    should_unlock_input,
    process_recovery_completion,
    start_recovery_lock,
    get_completion_summary,
    is_recovery_complete,
    get_pending_conditions,
    get_blocking_condition,
)
from .recovery_orchestrator_helpers import (
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
from .recovery_orchestrator import (
    RecoveryOrchestrator,
    RecoveryCallback,
)

__all__ = [
    # Context
    "RecoveryContext",
    "create_recovery_context",
    # Lifecycle
    "start_recovery_tracking",
    "update_recovery",
    "finalize_recovery",
    "reset_recovery_context",
    # Queries
    "is_recovery_in_progress",
    "is_threshold_crossed",
    "get_recovery_progress",
    "get_current_distance",
    "get_surface_deflection",
    # Mapping
    "map_recovery_phase_to_proximity",
    "map_proximity_to_recovery_phase",
    # Completion (TEND-32)
    "RecoveryCondition",
    "RecoveryCompletionStatus",
    "create_completion_status",
    "check_distance_condition",
    "check_color_condition",
    "check_velocity_condition",
    "check_tendroid_condition",
    "update_completion_status",
    "should_unlock_input",
    "process_recovery_completion",
    "start_recovery_lock",
    "get_completion_summary",
    "is_recovery_complete",
    "get_pending_conditions",
    "get_blocking_condition",
    # Orchestrator State (TEND-130)
    "OrchestratorState",
    "create_orchestrator_state",
    "handle_contact_event",
    "update_frame",
    "reset_orchestrator_state",
    "is_active",
    "is_input_blocked",
    "get_current_color",
    "get_status_summary",
    # Orchestrator Controller (TEND-130)
    "RecoveryOrchestrator",
    "RecoveryCallback",
]
