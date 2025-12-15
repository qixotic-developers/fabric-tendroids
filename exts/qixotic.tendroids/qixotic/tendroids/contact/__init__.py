"""
Contact Handling Package

Provides PhysX contact event subscription, filtering, repulsion
force calculations, color effects, input lock management,
and approach tracking for creature-tendroid interactions.

Implements TEND-24: Subscribe to PhysX contact events.
Implements TEND-25: Implement repulsion force along surface normal.
Implements TEND-26: Implement shock color change effect.
Implements TEND-27: Implement color fade during recovery.
Implements LTEND-28: Disable keyboard controls during repel.
Implements TEND-29: Track approach_minimum during creature movement.
"""

from .contact_handler import ContactHandler, ContactEvent
from .contact_filter_helpers import (
    filter_creature_tendroid_contacts,
    extract_contact_info,
    is_creature_prim,
    is_tendroid_prim,
)
from .repulsion_helpers import (
    RepulsionConfig,
    RepulsionResult,
    calculate_cylinder_surface_normal,
    calculate_surface_normal_from_contact,
    compute_repulsion_force,
    compute_corrected_position,
    calculate_repulsion,
)
from .color_effect_helpers import (
    ColorConfig,
    ColorEffectState,
    ColorEffectStatus,
    trigger_shock,
    start_recovery,
    update_recovery,
    check_shock_exit,
    reset_to_normal,
    interpolate_color,
    is_shocked,
    is_normal,
    is_recovering,
)
from .color_fade_helpers import (
    FadeMode,
    FadeConfig,
    calculate_distance_fade,
    calculate_speed_fade,
    calculate_time_fade,
    calculate_fade_progress,
    apply_easing,
    blend_fade_modes,
)
from .color_effect_controller import ColorEffectController
from .input_lock_helpers import (
    InputLockReason,
    InputLockStatus,
    lock_input_on_contact,
    update_lock_reason,
    unlock_input_on_recovery_complete,
    sync_lock_from_color_state,
    is_input_locked,
    should_apply_keyboard,
    get_lock_reason_name,
)
from .approach_tracker_helpers import (
    RecoveryPhase,
    TendroidSurfacePoint,
    ApproachTrackerStatus,
    calculate_distance_to_surface,
    calculate_signed_distance_to_surface,
    start_tracking,
    update_distance,
    check_threshold_crossed,
    complete_recovery,
    reset_tracker,
    update_surface_point,
    create_surface_point_from_contact,
    get_recovery_progress,
    is_tracking_active,
    is_recovery_complete,
    get_phase_name,
)

__all__ = [
    # Contact handler
    'ContactHandler',
    'ContactEvent',
    # Filtering
    'filter_creature_tendroid_contacts',
    'extract_contact_info',
    'is_creature_prim',
    'is_tendroid_prim',
    # Repulsion
    'RepulsionConfig',
    'RepulsionResult',
    'calculate_cylinder_surface_normal',
    'calculate_surface_normal_from_contact',
    'compute_repulsion_force',
    'compute_corrected_position',
    'calculate_repulsion',
    # Color effects
    'ColorConfig',
    'ColorEffectState',
    'ColorEffectStatus',
    'ColorEffectController',
    'trigger_shock',
    'start_recovery',
    'update_recovery',
    'check_shock_exit',
    'reset_to_normal',
    'interpolate_color',
    'is_shocked',
    'is_normal',
    'is_recovering',
    # Fade
    'FadeMode',
    'FadeConfig',
    'calculate_distance_fade',
    'calculate_speed_fade',
    'calculate_time_fade',
    'calculate_fade_progress',
    'apply_easing',
    'blend_fade_modes',
    # Input lock (LTEND-28)
    'InputLockReason',
    'InputLockStatus',
    'lock_input_on_contact',
    'update_lock_reason',
    'unlock_input_on_recovery_complete',
    'sync_lock_from_color_state',
    'is_input_locked',
    'should_apply_keyboard',
    'get_lock_reason_name',
    # Approach tracking (TEND-29)
    'RecoveryPhase',
    'TendroidSurfacePoint',
    'ApproachTrackerStatus',
    'calculate_distance_to_surface',
    'calculate_signed_distance_to_surface',
    'start_tracking',
    'update_distance',
    'check_threshold_crossed',
    'complete_recovery',
    'reset_tracker',
    'update_surface_point',
    'create_surface_point_from_contact',
    'get_recovery_progress',
    'is_tracking_active',
    'is_recovery_complete',
    'get_phase_name',
]
