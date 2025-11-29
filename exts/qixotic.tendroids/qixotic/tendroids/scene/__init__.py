"""
V2 Scene - Scene management, factory, and animation control

Provides multi-tendroid spawning, scene orchestration, and animation loop.
"""

from .tendroid_factory import V2TendroidFactory
from .animation_controller import V2AnimationController
from .manager import V2SceneManager
from .tendroid_wrapper import V2TendroidWrapper

__all__ = [
    "V2TendroidFactory",
    "V2AnimationController",
    "V2SceneManager",
    "V2TendroidWrapper",
]
