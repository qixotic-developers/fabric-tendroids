"""
Contact Filter Helpers - Filtering logic for creature-tendroid contacts

Pure functions for identifying and filtering PhysX contact events
to isolate creature-tendroid collision pairs.

Implements TEND-93: Create contact event filtering for creature-tendroid pairs.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class ContactInfo:
    """Extracted contact information from PhysX contact data."""
    creature_path: str
    tendroid_path: str
    contact_point: Tuple[float, float, float]
    contact_normal: Tuple[float, float, float]
    impulse: float
    separation: float


def is_creature_prim(prim_path: str, creature_patterns: List[str] = None) -> bool:
    """
    Check if a prim path belongs to a creature.
    
    Args:
        prim_path: USD prim path to check
        creature_patterns: List of path patterns identifying creatures.
                          Defaults to ['/World/Creature']
    
    Returns:
        True if path matches a creature pattern
    """
    if creature_patterns is None:
        creature_patterns = ['/World/Creature']
    
    for pattern in creature_patterns:
        if prim_path.startswith(pattern):
            return True
    return False


def is_tendroid_prim(prim_path: str, tendroid_patterns: List[str] = None) -> bool:
    """
    Check if a prim path belongs to a tendroid.
    
    Args:
        prim_path: USD prim path to check
        tendroid_patterns: List of path patterns identifying tendroids.
                          Defaults to ['/World/Tendroids/', '/World/Tendroid_']
    
    Returns:
        True if path matches a tendroid pattern
    """
    if tendroid_patterns is None:
        tendroid_patterns = ['/World/Tendroids/', '/World/Tendroid_']
    
    for pattern in tendroid_patterns:
        if pattern in prim_path:
            return True
    return False


def extract_contact_info(
    actor0_path: str,
    actor1_path: str,
    contact_point: Tuple[float, float, float],
    contact_normal: Tuple[float, float, float],
    impulse: float = 0.0,
    separation: float = 0.0,
    creature_patterns: List[str] = None,
    tendroid_patterns: List[str] = None,
) -> Optional[ContactInfo]:
    """
    Extract ContactInfo if this is a creature-tendroid contact.
    
    Determines which actor is the creature and which is the tendroid,
    then returns structured contact information.
    
    Args:
        actor0_path: First actor prim path
        actor1_path: Second actor prim path
        contact_point: Contact point in world coordinates (x, y, z)
        contact_normal: Contact normal vector (x, y, z)
        impulse: Contact impulse magnitude
        separation: Separation distance (negative = penetration)
        creature_patterns: Patterns for creature identification
        tendroid_patterns: Patterns for tendroid identification
    
    Returns:
        ContactInfo if creature-tendroid pair, None otherwise
    """
    is_actor0_creature = is_creature_prim(actor0_path, creature_patterns)
    is_actor1_creature = is_creature_prim(actor1_path, creature_patterns)
    is_actor0_tendroid = is_tendroid_prim(actor0_path, tendroid_patterns)
    is_actor1_tendroid = is_tendroid_prim(actor1_path, tendroid_patterns)
    
    # Must be exactly one creature and one tendroid
    if is_actor0_creature and is_actor1_tendroid:
        return ContactInfo(
            creature_path=actor0_path,
            tendroid_path=actor1_path,
            contact_point=contact_point,
            contact_normal=contact_normal,
            impulse=impulse,
            separation=separation,
        )
    elif is_actor1_creature and is_actor0_tendroid:
        # Flip normal to point away from tendroid toward creature
        flipped_normal = (
            -contact_normal[0],
            -contact_normal[1],
            -contact_normal[2],
        )
        return ContactInfo(
            creature_path=actor1_path,
            tendroid_path=actor0_path,
            contact_point=contact_point,
            contact_normal=flipped_normal,
            impulse=impulse,
            separation=separation,
        )
    
    return None


def filter_creature_tendroid_contacts(
    contact_pairs: List[Tuple[str, str, Tuple[float, float, float], Tuple[float, float, float], float, float]],
    creature_patterns: List[str] = None,
    tendroid_patterns: List[str] = None,
) -> List[ContactInfo]:
    """
    Filter a list of contact pairs to only creature-tendroid contacts.
    
    Args:
        contact_pairs: List of tuples:
                       (actor0_path, actor1_path, contact_point,
                        contact_normal, impulse, separation)
        creature_patterns: Patterns for creature identification
        tendroid_patterns: Patterns for tendroid identification
    
    Returns:
        List of ContactInfo for creature-tendroid pairs only
    """
    results = []
    
    for pair in contact_pairs:
        actor0, actor1, point, normal, impulse, separation = pair
        info = extract_contact_info(
            actor0, actor1, point, normal, impulse, separation,
            creature_patterns, tendroid_patterns
        )
        if info is not None:
            results.append(info)
    
    return results
