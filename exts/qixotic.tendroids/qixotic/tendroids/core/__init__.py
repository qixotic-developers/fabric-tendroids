"""
Core Tendroid components

Geometry generation, deformation, and creature management.
"""

from .cylinder_generator import CylinderGenerator
from .warp_deformer import WarpDeformer
from .tendroid import Tendroid

__all__ = ['CylinderGenerator', 'WarpDeformer', 'Tendroid']
