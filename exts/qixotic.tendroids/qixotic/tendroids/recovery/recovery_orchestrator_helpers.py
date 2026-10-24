"""
Recovery Orchestrator Helpers - Wiring logic for recovery subsystems

Re-exports state and event handling from split modules for
backward compatibility.

Implements TEND-130: Integrate recovery system modules into runtime.
"""

# Re-export state management
from .orchestrator_state import (
    OrchestratorState,
    create_orchestrator_state,
    reset_orchestrator_state,
    is_active,
    is_input_blocked,
    get_current_color,
    get_status_summary,
)

# Re-export event handling
from .orchestrator_events import (
    handle_contact_event,
    update_frame,
)

__all__ = [
    # State
    "OrchestratorState",
    "create_orchestrator_state",
    "reset_orchestrator_state",
    "is_active",
    "is_input_blocked",
    "get_current_color",
    "get_status_summary",
    # Events
    "handle_contact_event",
    "update_frame",
]
