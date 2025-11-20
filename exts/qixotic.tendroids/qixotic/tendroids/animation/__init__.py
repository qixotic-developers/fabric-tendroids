"""
Animation system for Tendroids

Provides breathing animation controllers, wave effects, and mode configuration.
"""

from .breathing import BreathingAnimator
from .animation_mode import AnimationMode
from .wave_controller import WaveController, WaveConfig


__all__ = [
  'BreathingAnimator',
  'AnimationMode',
  'WaveController',
  'WaveConfig',
]
