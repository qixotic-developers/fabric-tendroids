"""
V2 UI Package - Control panel and UI components

Provides compact, slider-based controls for tendroid management.
"""

from .control_panel import V2ControlPanel
from .slider_row import create_int_slider_row, create_float_slider_row
from .bubble_controls import BubbleControls

__all__ = [
    "V2ControlPanel",
    "create_int_slider_row",
    "create_float_slider_row",
    "BubbleControls",
]
