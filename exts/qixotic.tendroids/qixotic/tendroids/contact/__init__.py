"""
Contact Handling Package

Provides PhysX contact event subscription, filtering, and repulsion
force calculations for creature-tendroid interactions.

Implements TEND-24: Subscribe to PhysX contact events.
Implements TEND-25: Implement repulsion force along surface normal.
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
]
