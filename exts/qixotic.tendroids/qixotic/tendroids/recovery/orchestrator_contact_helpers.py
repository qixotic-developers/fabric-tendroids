"""
Orchestrator Contact Helpers - Contact event processing for controller

Helper functions for processing contact events in RecoveryOrchestrator.

Implements TEND-130: Integrate recovery system modules into runtime.
"""

from typing import Tuple

from ..contact.contact_handler import ContactEvent


def extract_force_from_event(
    event: ContactEvent,
) -> Tuple[float, float, float]:
    """
    Calculate repulsion force from contact event.
    
    Args:
        event: PhysX contact event
        
    Returns:
        Force vector (fx, fy, fz)
    """
    impulse = event.impulse
    return (
        event.surface_normal[0] * impulse,
        event.surface_normal[1] * impulse,
        event.surface_normal[2] * impulse,
    )


def estimate_creature_position(
    event: ContactEvent,
    offset: float = 0.1,
) -> Tuple[float, float, float]:
    """
    Estimate creature position from contact event.
    
    Args:
        event: PhysX contact event
        offset: Distance along normal from contact point
        
    Returns:
        Estimated creature position
    """
    return (
        event.contact_point[0] + event.surface_normal[0] * offset,
        event.contact_point[1] + event.surface_normal[1] * offset,
        event.contact_point[2] + event.surface_normal[2] * offset,
    )


def fire_callback_safe(callback, *args) -> None:
    """
    Fire callback with error handling.
    
    Args:
        callback: Callback function to invoke
        *args: Arguments to pass to callback
    """
    if callback is None:
        return
    
    try:
        callback(*args)
    except Exception as e:
        try:
            import carb
            carb.log_error(f"[RecoveryOrchestrator] Callback error: {e}")
        except ImportError:
            pass  # Running outside Omniverse
