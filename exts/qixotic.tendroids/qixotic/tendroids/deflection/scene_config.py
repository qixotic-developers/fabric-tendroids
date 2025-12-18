"""
Scene-Unit Deflection Configuration

Provides deflection configuration scaled to match scene units
rather than real-world meters.

Scene units in this project:
- Tendroid radius: ~10 units
- Tendroid length: ~160 units
- Creature radius: ~6 units
- Creature speed: ~50 units/second
"""

import math
from .deflection_config import (
    DeflectionConfig,
    DeflectionLimits,
    DetectionZones,
)


def create_scene_unit_zones(
    tendroid_radius: float = 10.0,
    creature_radius: float = 6.0,
) -> DetectionZones:
    """
    Create DetectionZones scaled to scene units.
    
    Args:
        tendroid_radius: Tendroid cylinder radius in scene units
        creature_radius: Creature collision radius in scene units
        
    Returns:
        DetectionZones configured for scene scale
    """
    return DetectionZones(
        # Actual tendroid radius
        tendroid_radius=tendroid_radius,
        
        # Buffer = creature radius + margin for early detection
        approach_buffer=creature_radius + 10.0,
        
        # Minimum distance (surface contact)
        approach_minimum=1.0,
        
        # Maximum detection range from tendroid surface
        detection_range=creature_radius + 25.0,
    )


def create_scene_unit_limits() -> DeflectionLimits:
    """
    Create DeflectionLimits tuned for visual effect.
    
    Returns:
        DeflectionLimits with appropriate angles and rates
    """
    return DeflectionLimits(
        # Minimum bend at base (subtle)
        minimum_deflection=math.radians(2.0),
        
        # Maximum bend at tip (noticeable but not extreme)
        maximum_deflection=math.radians(25.0),
        
        # Recovery speed - how fast tendroid returns to neutral
        recovery_rate=1.2,
        
        # Deflection speed - how fast tendroid bends away
        deflection_rate=2.5,
    )


def create_scene_unit_config(
    tendroid_radius: float = 10.0,
    creature_radius: float = 6.0,
) -> DeflectionConfig:
    """
    Create complete DeflectionConfig for scene units.
    
    Args:
        tendroid_radius: Tendroid cylinder radius
        creature_radius: Creature collision radius
        
    Returns:
        DeflectionConfig properly scaled
    """
    return DeflectionConfig(
        limits=create_scene_unit_limits(),
        zones=create_scene_unit_zones(tendroid_radius, creature_radius),
        enable_vertical=True,
        enable_head_on=True,
        enable_pass_by=True,
        debug_logging=False,
    )


# Default scene-unit config
SCENE_UNIT_CONFIG = create_scene_unit_config()
