"""
Tendroids - Interactive cylinder-based wormlike sea creatures
This module provides the core functionality for creating and animating
Tendroids using Fabric/USDRT for optimal performance.
"""
from .extension import TendroidsExtension

# Import C++ extension if available
try:
    from . import fast_mesh_updater
    __all__ = ["TendroidsExtension", "fast_mesh_updater"]
except ImportError:
    __all__ = ["TendroidsExtension"]