"""
V2: Official Bubble-Guided Deformation System

Default implementation uses Warp GPU acceleration (10x faster).
CPU fallbacks available for testing/comparison.

Performance (RTX 4090, 60Hz monitor):
- 15 Tendroids: 60 fps
- 30 Tendroids: 40 fps
- Warp GPU: 0.68 ms/frame (1480 theoretical fps) 
- NumPy:    2.55 ms/frame (392 theoretical fps)
- Python:   6.67 ms/frame (150 theoretical fps)
"""

# Primary exports (Warp GPU - default)
from .v2_warp_controller import V2WarpController
from .v2_warp_tendroid import V2WarpTendroid
from .v2_warp_deformer import V2WarpDeformer

# Shared components
from .v2_bubble import V2Bubble
from .v2_bubble_visual import V2BubbleVisual
from .v2_material_helper import apply_material

# CPU fallbacks
from .v2_controller import V2Controller
from .v2_tendroid import V2Tendroid
from .v2_deformer import V2Deformer
from .v2_numpy_controller import V2NumpyController
from .v2_numpy_tendroid import V2NumpyTendroid

# Backwards compatibility aliases
WarpController = V2WarpController
WarpTendroid = V2WarpTendroid
WarpDeformer = V2WarpDeformer
POCBubble = V2Bubble
POCBubbleVisual = V2BubbleVisual
POCController = V2Controller
POCTendroid = V2Tendroid
POCDeformer = V2Deformer
NumpyController = V2NumpyController
NumpyTendroid = V2NumpyTendroid

__all__ = [
    # GPU (default)
    "V2WarpController", "V2WarpTendroid", "V2WarpDeformer",
    # Shared
    "V2Bubble", "V2BubbleVisual", "apply_material",
    # CPU fallbacks
    "V2Controller", "V2Tendroid", "V2Deformer",
    "V2NumpyController", "V2NumpyTendroid",
    # Backwards compatibility
    "WarpController", "WarpTendroid", "WarpDeformer",
    "POCBubble", "POCBubbleVisual",
    "POCController", "POCTendroid", "POCDeformer",
    "NumpyController", "NumpyTendroid",
]
