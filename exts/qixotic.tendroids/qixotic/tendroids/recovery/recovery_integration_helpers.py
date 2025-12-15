"""
Recovery Integration Helpers - Bridge approach tracker with proximity system

Provides unified interface for managing recovery state alongside
proximity detection. Bridges the approach_tracker_helpers module
with the proximity state machine.

Implements TEND-30: Recalculate absolute coordinates as tendroid returns.
Implements TEND-120: Integrate with proximity detection system.
"""

from dataclasses import dataclass
from typing import Optional, Tuple

from ..contact.approach_tracker_helpers import (
    ApproachTrackerStatus,
    RecoveryPhase,
    TendroidSurfacePoint,
    calculate_distance_to_surface,
    check_threshold_crossed,
    complete_recovery,
    reset_tracker,
    start_tracking,
    update_distance,
    update_surface_point,
)
from ..proximity.proximity_config import ApproachParameters, DEFAULT_APPROACH_PARAMS
from ..proximity.proximity_state import ProximityState
from ..proximity.state_transitions import determine_next_state


@dataclass
class RecoveryContext:
    """
    Combined context for recovery tracking and proximity detection.
    
    Holds all state needed to track creature recovery while keeping
    the proximity system in sync.
    """
    # Approach tracking state
    tracker_status: ApproachTrackerStatus
    
    # Current tendroid surface point
    surface_point: TendroidSurfacePoint
    
    # Proximity state machine state
    proximity_state: ProximityState
    
    # Last recorded distance (for movement direction)
    previous_distance: Optional[float] = None
    
    # Approach parameters in use
    params: ApproachParameters = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = DEFAULT_APPROACH_PARAMS


def create_recovery_context(
    params: ApproachParameters = DEFAULT_APPROACH_PARAMS,
) -> RecoveryContext:
    """
    Create initial recovery context.
    
    Args:
        params: Approach parameters to use
        
    Returns:
        Fresh recovery context ready for tracking
    """
    return RecoveryContext(
        tracker_status=ApproachTrackerStatus(
            threshold_distance=params.approach_minimum,
        ),
        surface_point=TendroidSurfacePoint(),
        proximity_state=ProximityState.IDLE,
        previous_distance=None,
        params=params,
    )


def start_recovery_tracking(
    context: RecoveryContext,
    contact_point: Tuple[float, float, float],
    surface_normal: Tuple[float, float, float],
    creature_pos: Tuple[float, float, float],
    deflection_amount: float = 0.0,
) -> RecoveryContext:
    """
    Start recovery tracking when contact occurs.
    
    Initializes both the approach tracker and updates proximity state.
    
    Args:
        context: Current recovery context
        contact_point: World position where contact occurred
        surface_normal: Normal pointing away from tendroid at contact
        creature_pos: Current creature position
        deflection_amount: How far tendroid was pushed in
        
    Returns:
        Updated context with tracking active
    """
    # Create surface point from contact
    surface = TendroidSurfacePoint(
        current_x=contact_point[0],
        current_y=contact_point[1],
        current_z=contact_point[2],
        rest_x=contact_point[0] + surface_normal[0] * deflection_amount,
        rest_y=contact_point[1] + surface_normal[1] * deflection_amount,
        rest_z=contact_point[2] + surface_normal[2] * deflection_amount,
        normal_x=surface_normal[0],
        normal_y=surface_normal[1],
        normal_z=surface_normal[2],
    )
    
    # Calculate initial distance
    initial_distance = calculate_distance_to_surface(creature_pos, surface)
    
    # Start approach tracker
    new_status = start_tracking(
        context.tracker_status,
        context.params.approach_minimum,
        initial_distance,
    )
    
    # Update proximity state to RETREATING (just left contact)
    new_proximity, _ = determine_next_state(
        ProximityState.CONTACT,
        initial_distance,
        None,
        context.params,
    )
    
    return RecoveryContext(
        tracker_status=new_status,
        surface_point=surface,
        proximity_state=new_proximity,
        previous_distance=initial_distance,
        params=context.params,
    )


def update_recovery(
    context: RecoveryContext,
    creature_pos: Tuple[float, float, float],
    new_surface_pos: Tuple[float, float, float],
    new_surface_normal: Optional[Tuple[float, float, float]] = None,
) -> RecoveryContext:
    """
    Update recovery tracking with new positions.
    
    Called each frame during recovery to update both the approach
    tracker and proximity state machine.
    
    Args:
        context: Current recovery context
        creature_pos: Current creature world position
        new_surface_pos: Updated tendroid surface position
        new_surface_normal: Optional updated surface normal
        
    Returns:
        Updated recovery context
    """
    # Update surface point (tendroid returning to rest)
    updated_surface = update_surface_point(
        context.surface_point,
        new_surface_pos,
        new_surface_normal,
    )
    
    # Calculate new distance
    current_distance = calculate_distance_to_surface(creature_pos, updated_surface)
    
    # Update approach tracker
    new_status = update_distance(
        context.tracker_status,
        creature_pos,
        updated_surface,
    )
    
    # Update proximity state
    new_proximity, _ = determine_next_state(
        context.proximity_state,
        current_distance,
        context.previous_distance,
        context.params,
    )
    
    return RecoveryContext(
        tracker_status=new_status,
        surface_point=updated_surface,
        proximity_state=new_proximity,
        previous_distance=current_distance,
        params=context.params,
    )


def finalize_recovery(context: RecoveryContext) -> RecoveryContext:
    """
    Finalize recovery when all conditions are met.
    
    Called when threshold is crossed and all effects complete.
    
    Args:
        context: Current recovery context
        
    Returns:
        Context with recovery marked complete
    """
    return RecoveryContext(
        tracker_status=complete_recovery(context.tracker_status),
        surface_point=context.surface_point,
        proximity_state=ProximityState.RECOVERED,
        previous_distance=context.previous_distance,
        params=context.params,
    )


def reset_recovery_context(context: RecoveryContext) -> RecoveryContext:
    """
    Reset context for next contact cycle.
    
    Args:
        context: Current recovery context
        
    Returns:
        Reset context ready for new tracking
    """
    return RecoveryContext(
        tracker_status=reset_tracker(context.tracker_status),
        surface_point=TendroidSurfacePoint(),
        proximity_state=ProximityState.RECOVERED,  # Stay recovered
        previous_distance=None,
        params=context.params,
    )


def is_recovery_in_progress(context: RecoveryContext) -> bool:
    """Check if recovery tracking is currently active."""
    return context.tracker_status.phase == RecoveryPhase.TRACKING


def is_threshold_crossed(context: RecoveryContext) -> bool:
    """Check if creature has crossed the approach_minimum threshold."""
    return check_threshold_crossed(context.tracker_status)


def get_recovery_progress(context: RecoveryContext) -> float:
    """
    Get recovery progress as 0.0 to 1.0.
    
    Useful for fading effects during recovery.
    """
    from ..contact.approach_tracker_helpers import get_recovery_progress as _get_progress
    return _get_progress(context.tracker_status)


def get_current_distance(context: RecoveryContext) -> float:
    """Get current distance from creature to tendroid surface."""
    return context.tracker_status.current_distance


def get_surface_deflection(context: RecoveryContext) -> float:
    """Get remaining tendroid deflection amount."""
    return context.surface_point.deflection_amount()


def map_recovery_phase_to_proximity(phase: RecoveryPhase) -> ProximityState:
    """
    Map approach tracker phase to closest proximity state.
    
    Useful for compatibility when only tracker status is available.
    """
    mapping = {
        RecoveryPhase.INACTIVE: ProximityState.IDLE,
        RecoveryPhase.TRACKING: ProximityState.RETREATING,
        RecoveryPhase.THRESHOLD_CROSSED: ProximityState.RECOVERED,
        RecoveryPhase.COMPLETE: ProximityState.RECOVERED,
    }
    return mapping.get(phase, ProximityState.IDLE)


def map_proximity_to_recovery_phase(state: ProximityState) -> RecoveryPhase:
    """
    Map proximity state to closest recovery phase.
    
    Note: Not all proximity states map cleanly to recovery phases.
    """
    mapping = {
        ProximityState.IDLE: RecoveryPhase.INACTIVE,
        ProximityState.APPROACHING: RecoveryPhase.INACTIVE,
        ProximityState.CONTACT: RecoveryPhase.TRACKING,  # About to start
        ProximityState.RETREATING: RecoveryPhase.TRACKING,
        ProximityState.RECOVERED: RecoveryPhase.COMPLETE,
    }
    return mapping.get(state, RecoveryPhase.INACTIVE)
