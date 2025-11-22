"""
POC Module - DEPRECATED, use qixotic.tendroids.v2 instead

This module provides backwards compatibility aliases.
All classes redirect to the v2 module.
"""

import warnings

warnings.warn(
    "qixotic.tendroids.poc is deprecated. Use qixotic.tendroids.v2 instead.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export from v2 for backwards compatibility
from ..v2 import (
    # GPU (primary)
    V2WarpController as WarpController,
    V2WarpTendroid as WarpTendroid,
    V2WarpDeformer as WarpDeformer,
    # Shared
    V2Bubble as POCBubble,
    V2BubbleVisual as POCBubbleVisual,
    apply_material,
    # CPU fallbacks
    V2Controller as POCController,
    V2Tendroid as POCTendroid,
    V2Deformer as POCDeformer,
    V2NumpyController as NumpyController,
    V2NumpyTendroid as NumpyTendroid,
)

__all__ = [
    "WarpController", "WarpTendroid", "WarpDeformer",
    "POCBubble", "POCBubbleVisual", "apply_material",
    "POCController", "POCTendroid", "POCDeformer",
    "NumpyController", "NumpyTendroid",
]
