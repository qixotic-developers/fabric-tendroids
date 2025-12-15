"""
Contact Handling Package

Provides PhysX contact event subscription, filtering, repulsion
force calculations, and color effects for creature-tendroid interactions.

Implements TEND-24: Subscribe to PhysX contact events.
Implements TEND-25: Implement repulsion force along surface normal.
Implements TEND-26: Implement shock color change effect.
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
    check_shock_exit,
    reset_to_normal,
    interpolate_color,
    is_shocked,
    is_normal,
)
from .color_effect_controller import ColorEffectController

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
    'check_shock_exit',
    'reset_to_normal',
    'interpolate_color',
    'is_shocked',
    'is_normal',
]
