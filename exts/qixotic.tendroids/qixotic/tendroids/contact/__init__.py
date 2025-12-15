"""
Contact Handling Package

Provides PhysX contact event subscription and filtering for
creature-tendroid interactions.

Implements TEND-24: Subscribe to PhysX contact events.
"""

from .contact_handler import ContactHandler, ContactEvent
from .contact_filter_helpers import (
    filter_creature_tendroid_contacts,
    extract_contact_info,
    is_creature_prim,
    is_tendroid_prim,
)

__all__ = [
    'ContactHandler',
    'ContactEvent',
    'filter_creature_tendroid_contacts',
    'extract_contact_info',
    'is_creature_prim',
    'is_tendroid_prim',
]
