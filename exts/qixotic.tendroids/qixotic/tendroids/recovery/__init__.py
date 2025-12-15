"""
Recovery Package - Creature recovery after tendroid contact

This package provides helpers for tracking and managing
the creature recovery process after contact with tendroids.

TEND-5: Recovery System epic
TEND-30: Recalculate absolute coordinates (uses relative distances)
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
]
