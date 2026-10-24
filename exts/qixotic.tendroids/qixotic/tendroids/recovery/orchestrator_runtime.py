"""
Orchestrator Runtime - Runtime methods for RecoveryOrchestrator

Mixin class providing update and event methods.

Implements TEND-130: Integrate recovery system modules into runtime.
"""

from typing import Optional, Tuple

from .recovery_orchestrator_helpers import (
    handle_contact_event,
    update_frame,
    reset_orchestrator_state,
    is_active,
    get_status_summary,
)
from .orchestrator_contact_helpers import (
    extract_force_from_event,
    estimate_creature_position,
    fire_callback_safe,
)


class OrchestratorRuntimeMixin:
    """
    Mixin providing runtime methods for RecoveryOrchestrator.
    
    Requires host class to have:
    - self._state: OrchestratorState
    - self._last_contact_point: Optional tuple
    - self._last_surface_normal: Optional tuple
    - self._on_recovery_complete: Optional callback
    """
    
    def update(
        self,
        creature_pos: Tuple[float, float, float],
        surface_pos: Optional[Tuple[float, float, float]] = None,
        delta_time: float = 0.016,
    ) -> Tuple[float, float, float]:
        """
        Process one frame of recovery.
        
        Returns:
            Position displacement to apply this frame
        """
        if not is_active(self._state):
            return (0.0, 0.0, 0.0)
        
        actual_surface = surface_pos or self._last_contact_point
        if actual_surface is None:
            return (0.0, 0.0, 0.0)
        
        prev_recoveries = self._state.total_recoveries
        
        self._state, displacement = update_frame(
            self._state,
            creature_pos,
            actual_surface,
            delta_time,
            self._last_surface_normal,
        )
        
        if self._state.total_recoveries > prev_recoveries:
            fire_callback_safe(
                self._on_recovery_complete,
                self._state.total_recoveries,
            )
        
        return displacement
    
    def handle_contact(
        self,
        contact_point: Tuple[float, float, float],
        surface_normal: Tuple[float, float, float],
        creature_pos: Tuple[float, float, float],
        repulsion_force: Tuple[float, float, float],
        deflection_amount: float = 0.0,
    ) -> None:
        """Manually trigger a contact event."""
        self._last_contact_point = contact_point
        self._last_surface_normal = surface_normal
        
        self._state = handle_contact_event(
            self._state,
            contact_point,
            surface_normal,
            creature_pos,
            repulsion_force,
            deflection_amount,
        )
    
    def reset(self) -> None:
        """Reset orchestrator to initial state."""
        self._state = reset_orchestrator_state(self._state)
        self._last_contact_point = None
        self._last_surface_normal = None
    
    def get_status(self) -> str:
        """Get human-readable status for debugging."""
        return get_status_summary(self._state)
    
    def _on_contact(self, event) -> None:
        """Handle contact event from ContactHandler."""
        force = extract_force_from_event(event)
        creature_pos = estimate_creature_position(event)
        
        self.handle_contact(
            event.contact_point,
            event.surface_normal,
            creature_pos,
            force,
            abs(event.separation),
        )
