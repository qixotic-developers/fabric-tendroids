"""
Proof of Concept: Bubble-Guided Deformation

This module contains a simplified single-tendroid implementation where
the bubble drives the cylinder deformation rather than trying to fit
inside a pre-deformed shape.

Key insight: The breathing bulge follows the bubble as it rises,
ensuring the bubble is always contained within the deformed envelope.
"""

from .poc_tendroid import POCTendroid
from .poc_bubble import POCBubble
from .poc_deformer import POCDeformer
from .poc_controller import POCController

__all__ = [
    "POCTendroid",
    "POCBubble",
    "POCDeformer",
    "POCController",
]
