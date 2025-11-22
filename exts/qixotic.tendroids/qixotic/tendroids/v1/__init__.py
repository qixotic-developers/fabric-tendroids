"""
V1 Module - DEPRECATED

This module contains the original Tendroids implementation.
New development should use qixotic.tendroids.v2 instead.

The V1 system uses transform-based animation (SetLocalScale).
V2 uses bubble-guided vertex deformation with Warp GPU acceleration.
"""

import warnings

warnings.warn(
    "qixotic.tendroids.v1 is deprecated. Use qixotic.tendroids.v2 for new development.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export submodules for backwards compatibility
from . import animation
from . import bubbles
from . import config
from . import core
from . import scene
from . import sea_floor
from . import ui
from . import utils

__all__ = [
    "animation",
    "bubbles",
    "config",
    "core",
    "scene",
    "sea_floor",
    "ui",
    "utils",
]
