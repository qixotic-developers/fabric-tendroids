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

# Controllers (scene orchestration - original demos)
from .controllers import V2Controller, V2NumpyController, V2WarpController

# Core (tendroids and deformers)
from .core import (
    V2Tendroid,
    V2NumpyTendroid,
    V2WarpTendroid,
    V2Deformer,
    V2WarpDeformer,
)

# Bubbles
from .bubbles import V2Bubble, V2BubbleVisual

# Utils
from .utils import apply_material

# Config
from .config import ConfigLoader, get_config_value

# Environment
from .environment import (
    SeaFloorConfig,
    SeaFloorController,
    EnvironmentConfig,
    EnvironmentSetup,
    get_height_at,
)

# Builders (NEW - flared geometry, terrain conform)
from .builders import (
    CylinderGenerator,
    conform_base_to_terrain,
    V2TendroidBuilder,
)

# Scene (NEW - multi-spawn, animation, orchestration)
from .scene import (
    V2TendroidFactory,
    V2AnimationController,
    V2SceneManager,
)

# Animation (NEW - wave effects)
from .animation import (
    WaveController,
    WaveConfig,
)

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
    # Controllers (demos)
    "V2Controller",
    "V2NumpyController",
    "V2WarpController",
    # Core
    "V2Tendroid",
    "V2NumpyTendroid",
    "V2WarpTendroid",
    "V2Deformer",
    "V2WarpDeformer",
    # Bubbles
    "V2Bubble",
    "V2BubbleVisual",
    # Utils
    "apply_material",
    # Config
    "ConfigLoader",
    "get_config_value",
    # Environment
    "SeaFloorConfig",
    "SeaFloorController",
    "EnvironmentConfig",
    "EnvironmentSetup",
    "get_height_at",
    # Builders (NEW)
    "CylinderGenerator",
    "conform_base_to_terrain",
    "V2TendroidBuilder",
    # Scene (NEW)
    "V2TendroidFactory",
    "V2AnimationController",
    "V2SceneManager",
    # Animation (NEW)
    "WaveController",
    "WaveConfig",
    # Backwards compatibility
    "WarpController",
    "WarpTendroid",
    "WarpDeformer",
    "POCBubble",
    "POCBubbleVisual",
    "POCController",
    "POCTendroid",
    "POCDeformer",
    "NumpyController",
    "NumpyTendroid",
]
