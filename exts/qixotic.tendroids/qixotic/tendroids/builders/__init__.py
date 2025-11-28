"""
V2 Builders - Tendroid creation and geometry utilities

Provides flared cylinder generation, terrain conforming, and tendroid building.
"""

from .cylinder_generator import CylinderGenerator
from .terrain_conform import conform_base_to_terrain
from .tendroid_builder import V2TendroidBuilder

__all__ = [
    "CylinderGenerator",
    "conform_base_to_terrain",
    "V2TendroidBuilder",
]
