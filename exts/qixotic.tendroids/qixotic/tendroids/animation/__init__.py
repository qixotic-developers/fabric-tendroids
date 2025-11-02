"""
Tendroid animation systems

Breathing waves, idle motion, and other animation controllers.
"""

from .breathing import BreathingAnimator
from .idle_motion import IdleMotionAnimator

__all__ = ['BreathingAnimator', 'IdleMotionAnimator']
