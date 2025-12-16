"""
Recovery Orchestrator - Unified controller for recovery subsystems

Coordinates all recovery-related modules into a single runtime interface.
Manages lifecycle, event handling, and frame updates for the complete
recovery system.

Implements TEND-130: Integrate recovery system modules into runtime.
Implements TEND-32: Re-enable controls after recovery complete.
"""

from typing import Optional, Tuple, Callable

from ..contact.color_effect_helpers import ColorConfig
from ..contact.velocity_fade_helpers import VelocityFadeConfig
from ..contact.contact_handler import ContactHandler, ContactEvent
from ..proximity.proximity_config import ApproachParameters

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

# Type alias for recovery completion callbacks
RecoveryCallback = Callable[[int], None]  # total_recoveries


class RecoveryOrchestrator:
    """
    Unified controller for the complete recovery system.
    
    Wires together:
    - RecoveryContext (tracking)
    - RecoveryCompletionStatus (conditions)
    - ColorEffectStatus (visual feedback)
    - VelocityFadeStatus (movement)
    - InputLockStatus (input control)
    """
    
    def __init__(
        self,
        approach_params: ApproachParameters = None,
        color_config: ColorConfig = None,
        velocity_config: VelocityFadeConfig = None,
        contact_handler: ContactHandler = None,
    ):
        """Initialize the recovery orchestrator."""
        self._state = create_orchestrator_state(
            approach_params=approach_params,
            color_config=color_config,
            velocity_config=velocity_config,
        )
        
        self._contact_handler = contact_handler
        self._owns_handler = contact_handler is None
        self._on_recovery_complete: Optional[RecoveryCallback] = None
        
        # Last contact data for surface tracking
        self._last_contact_point: Optional[Tuple[float, float, float]] = None
        self._last_surface_normal: Optional[Tuple[float, float, float]] = None
        self._is_started = False
    
    def handle_contact(
        self,
        contact_point: Tuple[float, float, float],
        surface_normal: Tuple[float, float, float],
        creature_pos: Tuple[float, float, float],
        repulsion_force: Tuple[float, float, float],
        deflection_amount: float = 0.0,
    ) -> None:
        """Manually trigger contact handling (for testing/direct use)."""
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
    
    def update(
        self,
        creature_pos: Tuple[float, float, float],
        delta_time: float,
        surface_pos: Tuple[float, float, float] = None,
    ) -> Tuple[float, float, float]:
        """
        Process one frame of recovery.
        
        Returns displacement to apply to creature position.
        """
        if surface_pos is None:
            surface_pos = self._last_contact_point or (0.0, 0.0, 0.0)
        
        prev_recoveries = self._state.total_recoveries
        
        self._state, displacement = update_frame(
            self._state,
            creature_pos,
            surface_pos,
            delta_time,
            self._last_surface_normal,
        )
        
        # Fire callback if recovery completed
        if self._state.total_recoveries > prev_recoveries:
            if self._on_recovery_complete:
                self._on_recovery_complete(self._state.total_recoveries)
        
        return displacement
    
    def reset(self) -> None:
        """Reset to initial state."""
        self._state = reset_orchestrator_state(self._state)
        self._last_contact_point = None
        self._last_surface_normal = None
    
    def get_status(self) -> str:
        """Get human-readable status string."""
        return get_status_summary(self._state)
    
    def _on_contact(self, event: ContactEvent) -> None:
        """Internal callback for ContactHandler events."""
        self.handle_contact(
            contact_point=event.contact_point,
            surface_normal=event.surface_normal,
            creature_pos=event.creature_position,
            repulsion_force=event.impulse,
            deflection_amount=getattr(event, 'deflection_amount', 0.0),
        )
    
    @property
    def state(self) -> OrchestratorState:
        """Current orchestrator state (read-only)."""
        return self._state
    
    @property
    def is_recovery_active(self) -> bool:
        """Whether recovery is currently in progress."""
        return is_active(self._state)
    
    @property
    def is_input_locked(self) -> bool:
        """Whether keyboard input should be blocked."""
        return is_input_blocked(self._state)
    
    @property
    def current_color(self) -> Tuple[float, float, float]:
        """Current creature color (RGB 0-1)."""
        return get_current_color(self._state)
    
    @property
    def total_contacts(self) -> int:
        """Total contact events processed."""
        return self._state.total_contacts
    
    @property
    def total_recoveries(self) -> int:
        """Total successful recoveries completed."""
        return self._state.total_recoveries
    
    def set_recovery_callback(self, callback: RecoveryCallback) -> None:
        """Set callback for recovery completion events."""
        self._on_recovery_complete = callback
    
    def start(self) -> bool:
        """Start the orchestrator and subscribe to contacts."""
        if self._is_started:
            return True
        
        if self._owns_handler:
            self._contact_handler = ContactHandler()
        
        if self._contact_handler:
            self._contact_handler.add_listener(self._on_contact)
            if not self._contact_handler.is_subscribed:
                self._contact_handler.subscribe()
        
        self._is_started = True
        return True
    
    def stop(self) -> None:
        """Stop the orchestrator and cleanup."""
        if not self._is_started:
            return
        
        if self._contact_handler:
            self._contact_handler.remove_listener(self._on_contact)
            if self._owns_handler:
                self._contact_handler.shutdown()
                self._contact_handler = None
        
        self._is_started = False
