"""
Animation system for Tendroids

Provides breathing animation controllers and mode configuration.
"""

from .breathing import BreathingAnimator
from .animation_mode import AnimationMode


__all__ = [
  'BreathingAnimator',
  'AnimationMode',
]
