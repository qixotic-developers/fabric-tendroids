"""
Core Tendroid components

Geometry generation, deformation, and creature management.
"""

from .cylinder_generator import CylinderGenerator
from .warp_deformer import WarpDeformer
from .tendroid import Tendroid
from .terrain_conform import conform_base_to_terrain

__all__ = ['CylinderGenerator', 'WarpDeformer', 'Tendroid', 'conform_base_to_terrain']
