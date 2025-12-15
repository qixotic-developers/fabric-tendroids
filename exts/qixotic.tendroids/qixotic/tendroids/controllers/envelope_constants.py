"""
Creature Envelope Constants - PhysX capsule collider parameters

Defines the envelope geometry for creature collision detection.
Based on design document: docs/creature-envelope-design.adoc
"""

# =============================================================================
# ENVELOPE GEOMETRY (from TEND-11 design)
# =============================================================================

# Capsule radius - matches visual creature_radius
ENVELOPE_RADIUS = 6.0

# Half the cylindrical section height (PhysX convention)
# Full cylinder height = 12.0, so half = 6.0
ENVELOPE_HALF_HEIGHT = 6.0

# Total capsule length = 2 * half_height + 2 * radius = 24.0
ENVELOPE_TOTAL_LENGTH = 2 * ENVELOPE_HALF_HEIGHT + 2 * ENVELOPE_RADIUS

# Capsule axis - aligned with creature forward direction
ENVELOPE_AXIS = "Z"


# =============================================================================
# PHYSX CONTACT PARAMETERS
# =============================================================================

# Contact offset - generate contacts before surfaces touch
# 4cm early detection buffer for smooth response
CONTACT_OFFSET = 0.04

# Rest offset - natural separation distance after contact resolution
# 1cm separation for stable resting
REST_OFFSET = 0.01


# =============================================================================
# COLLISION FILTERING
# =============================================================================

# Collision group for creature (can be used with PhysX filtering)
CREATURE_COLLISION_GROUP = 1

# Tendroids collision group
TENDROID_COLLISION_GROUP = 2


# =============================================================================
# DEBUG VISUALIZATION
# =============================================================================

# Whether to create visible debug geometry for the collider
DEBUG_SHOW_COLLIDER = False

# Debug collider color (semi-transparent green)
DEBUG_COLLIDER_COLOR = (0.2, 0.8, 0.2)
DEBUG_COLLIDER_OPACITY = 0.3
