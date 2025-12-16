"""
Repulsion Helpers - Force calculations for creature-tendroid contact response

Pure functions for calculating repulsion forces when a creature contacts
a tendroid. Uses surface normals and configurable force parameters.

Implements TEND-25: Implement repulsion force along surface normal.
Implements TEND-95: Create repulsion_helpers.py module.
Implements TEND-96: Implement surface normal calculation at contact point.
Implements TEND-97: Implement repulsion force vector computation.
"""

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class RepulsionConfig:
    """Configuration for repulsion force behavior."""
    base_force: float = 100.0  # Base repulsion force magnitude
    max_force: float = 500.0   # Maximum force clamp
    min_force: float = 10.0    # Minimum force threshold
    
    # Force scaling based on penetration depth
    penetration_multiplier: float = 2.0  # Force multiplier per unit penetration
    
    # Force scaling based on approach velocity
    velocity_multiplier: float = 0.5  # Additional force based on incoming speed


@dataclass
class RepulsionResult:
    """Result of repulsion force calculation."""
    force_vector: Tuple[float, float, float]  # Force direction and magnitude
    force_magnitude: float                     # Scalar magnitude
    surface_normal: Tuple[float, float, float] # Unit normal at contact
    corrected_position: Tuple[float, float, float]  # Position outside surface
    penetration_depth: float                   # How far inside surface


def calculate_cylinder_surface_normal(
    contact_point: Tuple[float, float, float],
    cylinder_center: Tuple[float, float, float],
    cylinder_axis: Tuple[float, float, float] = (0.0, 1.0, 0.0),
) -> Tuple[float, float, float]:
    """
    Calculate surface normal for a cylindrical tendroid at contact point.
    
    For vertical cylinders (Y-axis), the normal is radial in the XZ plane.
    Uses horizontal distance only (ignores Y) per project conventions.
    
    Args:
        contact_point: World position of contact (x, y, z)
        cylinder_center: Center position of cylinder (x, y, z)
        cylinder_axis: Unit vector along cylinder axis, default Y-up
    
    Returns:
        Unit normal vector pointing outward from cylinder surface
    """
    cx, cy, cz = contact_point
    ax, ay, az = cylinder_center
    
    # For Y-axis cylinders, calculate radial direction in XZ plane
    dx = cx - ax
    dz = cz - az
    
    # Horizontal distance (XZ plane)
    horizontal_dist = math.sqrt(dx * dx + dz * dz)
    
    if horizontal_dist < 1e-8:
        # Contact at cylinder axis - return arbitrary horizontal normal
        return (1.0, 0.0, 0.0)
    
    # Normalize to get unit radial direction
    nx = dx / horizontal_dist
    nz = dz / horizontal_dist
    
    # Normal has no Y component for vertical cylinder sides
    return (nx, 0.0, nz)


def calculate_surface_normal_from_contact(
    creature_position: Tuple[float, float, float],
    tendroid_position: Tuple[float, float, float],
    tendroid_radius: float = 6.0,
) -> Tuple[Tuple[float, float, float], float]:
    """
    Calculate surface normal and penetration from creature/tendroid positions.
    
    Uses horizontal (XZ plane) distance per project conventions.
    
    Args:
        creature_position: Creature world position
        tendroid_position: Tendroid center world position
        tendroid_radius: Radius of tendroid cylinder
    
    Returns:
        Tuple of (surface_normal, penetration_depth)
        penetration_depth > 0 means creature is inside tendroid
    """
    cx, cy, cz = creature_position
    tx, ty, tz = tendroid_position
    
    # Horizontal offset from tendroid to creature
    dx = cx - tx
    dz = cz - tz
    horizontal_dist = math.sqrt(dx * dx + dz * dz)
    
    if horizontal_dist < 1e-8:
        # Creature at tendroid center
        return ((1.0, 0.0, 0.0), tendroid_radius)
    
    # Surface normal points from tendroid toward creature
    nx = dx / horizontal_dist
    nz = dz / horizontal_dist
    
    # Penetration depth (positive = inside)
    penetration = tendroid_radius - horizontal_dist
    
    return ((nx, 0.0, nz), penetration)


def compute_repulsion_force(
    surface_normal: Tuple[float, float, float],
    penetration_depth: float = 0.0,
    approach_velocity: float = 0.0,
    config: RepulsionConfig = None,
) -> Tuple[float, float, float]:
    """
    Compute repulsion force vector from surface normal and penetration.
    
    Force magnitude scales with:
    - Base force (always applied on contact)
    - Penetration depth (deeper = stronger push)
    - Approach velocity (faster approach = stronger response)
    
    Args:
        surface_normal: Unit vector pointing away from tendroid
        penetration_depth: How far creature is inside surface (positive)
        approach_velocity: Speed toward tendroid at contact (positive)
        config: Force configuration parameters
    
    Returns:
        Force vector (fx, fy, fz) in world space
    """
    if config is None:
        config = RepulsionConfig()
    
    nx, ny, nz = surface_normal
    
    # Base force
    magnitude = config.base_force
    
    # Add penetration-based force
    if penetration_depth > 0:
        magnitude += penetration_depth * config.penetration_multiplier
    
    # Add velocity-based force
    if approach_velocity > 0:
        magnitude += approach_velocity * config.velocity_multiplier
    
    # Clamp to valid range
    magnitude = max(config.min_force, min(config.max_force, magnitude))
    
    # Apply magnitude to normal direction
    return (nx * magnitude, ny * magnitude, nz * magnitude)


def compute_corrected_position(
    creature_position: Tuple[float, float, float],
    tendroid_position: Tuple[float, float, float],
    tendroid_radius: float,
    safety_margin: float = 0.01,
) -> Tuple[float, float, float]:
    """
    Compute position that places creature just outside tendroid surface.
    
    Used for collision prevention to ensure creature never passes through.
    
    Args:
        creature_position: Current creature position
        tendroid_position: Tendroid center position
        tendroid_radius: Tendroid collision radius
        safety_margin: Extra distance outside surface
    
    Returns:
        Corrected position just outside tendroid surface
    """
    cx, cy, cz = creature_position
    tx, ty, tz = tendroid_position
    
    dx = cx - tx
    dz = cz - tz
    horizontal_dist = math.sqrt(dx * dx + dz * dz)
    
    if horizontal_dist < 1e-8:
        # At center - push in +X direction
        return (tx + tendroid_radius + safety_margin, cy, tz)
    
    # Normalize direction
    nx = dx / horizontal_dist
    nz = dz / horizontal_dist
    
    # Target distance from tendroid center
    target_dist = tendroid_radius + safety_margin
    
    # New position along radial direction
    new_x = tx + nx * target_dist
    new_z = tz + nz * target_dist
    
    return (new_x, cy, new_z)


def calculate_repulsion(
    creature_position: Tuple[float, float, float],
    tendroid_position: Tuple[float, float, float],
    tendroid_radius: float = 6.0,
    approach_velocity: float = 0.0,
    config: RepulsionConfig = None,
) -> RepulsionResult:
    """
    Full repulsion calculation from positions.
    
    Combines normal calculation, force computation, and position correction.
    
    Args:
        creature_position: Creature world position
        tendroid_position: Tendroid center position
        tendroid_radius: Tendroid collision radius
        approach_velocity: Speed toward tendroid (positive = approaching)
        config: Force configuration
    
    Returns:
        RepulsionResult with all computed values
    """
    if config is None:
        config = RepulsionConfig()
    
    # Get surface normal and penetration
    surface_normal, penetration = calculate_surface_normal_from_contact(
        creature_position, tendroid_position, tendroid_radius
    )
    
    # Compute force
    force_vector = compute_repulsion_force(
        surface_normal, penetration, approach_velocity, config
    )
    
    # Calculate force magnitude
    fx, fy, fz = force_vector
    magnitude = math.sqrt(fx*fx + fy*fy + fz*fz)
    
    # Get corrected position
    corrected = compute_corrected_position(
        creature_position, tendroid_position, tendroid_radius
    )
    
    return RepulsionResult(
        force_vector=force_vector,
        force_magnitude=magnitude,
        surface_normal=surface_normal,
        corrected_position=corrected,
        penetration_depth=max(0.0, penetration),
    )
