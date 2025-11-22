"""
Tendroids - Interactive underwater creatures with bubble-guided deformation

This module provides the core functionality for creating and animating
Tendroids using Warp GPU acceleration for optimal performance.

Primary API (V2 - Recommended):
    from qixotic.tendroids.v2 import V2WarpController, V2WarpTendroid

Legacy API (V1 - Deprecated):
    from qixotic.tendroids.v1 import scene, animation, bubbles
"""

from .extension import TendroidsExtension

# Primary exports from V2 (GPU-accelerated bubble-guided deformation)
from .v2 import (
    # GPU (default)
    V2WarpController,
    V2WarpTendroid,
    V2WarpDeformer,
    # Shared
    V2Bubble,
    V2BubbleVisual,
    apply_material,
    # CPU fallbacks
    V2Controller,
    V2Tendroid,
    V2Deformer,
    V2NumpyController,
    V2NumpyTendroid,
    # Backwards compatibility aliases
    WarpController,
    WarpTendroid,
    WarpDeformer,
    POCBubble,
    POCBubbleVisual,
)

# Import C++ extension if available
try:
    from . import fast_mesh_updater
    _has_cpp = True
except ImportError:
    _has_cpp = False

__all__ = [
    # Extension
    "TendroidsExtension",
    # V2 GPU (primary)
    "V2WarpController",
    "V2WarpTendroid",
    "V2WarpDeformer",
    # V2 Shared
    "V2Bubble",
    "V2BubbleVisual",
    "apply_material",
    # V2 CPU fallbacks
    "V2Controller",
    "V2Tendroid",
    "V2Deformer",
    "V2NumpyController",
    "V2NumpyTendroid",
    # Backwards compatibility
    "WarpController",
    "WarpTendroid",
    "WarpDeformer",
    "POCBubble",
    "POCBubbleVisual",
]

if _has_cpp:
    __all__.append("fast_mesh_updater")
