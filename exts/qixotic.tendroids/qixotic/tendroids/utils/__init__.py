"""
Utility functions and helpers

Mathematical functions, constants, and shared utilities.
"""

from .math_helpers import (
    smooth_step,
    ease_out_quartic,
    calculate_flare_radius,
    calculate_wave_displacement,
    calculate_wave_position
)

from . import profiler

__all__ = [
    'smooth_step',
    'ease_out_quartic',
    'calculate_flare_radius',
    'calculate_wave_displacement',
    'calculate_wave_position',
    'profiler'
]
