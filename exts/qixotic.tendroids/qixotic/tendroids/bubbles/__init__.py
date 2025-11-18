"""
Bubble system for Tendroids

Provides deformation-synchronized bubble emission with two-phase physics:
1. Locked phase: Bubbles rise with deformation wave
2. Released phase: Bubbles break free with squeeze-out acceleration
"""

from .bubble import Bubble
from .bubble_manager import BubbleManager
from .bubble_config import BubbleConfig, DEFAULT_BUBBLE_CONFIG
from .bubble_physics import BubblePhysics
from .deformation_tracker import DeformationWaveTracker
from .bubble_helpers import create_bubble_sphere

__all__ = [
  'Bubble',
  'BubbleManager',
  'BubbleConfig',
  'DEFAULT_BUBBLE_CONFIG',
  'BubblePhysics',
  'DeformationWaveTracker',
  'create_bubble_sphere'
]
