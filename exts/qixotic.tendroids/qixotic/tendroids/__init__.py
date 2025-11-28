"""
Tendroids - Interactive underwater creatures with bubble-guided deformation

This module provides the core functionality for creating and animating
Tendroids using Warp GPU acceleration for optimal performance.

Primary API:
    from qixotic.tendroids.v2 import V2WarpController, V2WarpTendroid
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
)

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
]
