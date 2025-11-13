"""
Animation mode enumeration for Tendroid

Defines available animation techniques for breathing effects.
"""

from enum import Enum, auto


class AnimationMode(Enum):
  """
  Tendroid animation modes.
  
  TRANSFORM: Scale individual segment cylinders (current Phase 1 method)
  VERTEX_DEFORM: GPU-accelerated vertex deformation (Phase 2A)
  """
  TRANSFORM = auto()
  VERTEX_DEFORM = auto()
  
  def __str__(self) -> str:
    return self.name.replace('_', ' ').title()
