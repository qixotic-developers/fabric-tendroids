"""
Spawn controls section for V2 control panel

Manages tendroid count, spawn area, and radius range settings.
"""

import omni.ui as ui
from .slider_row import create_int_slider_row, create_float_slider_row


class SpawnControls:
    """Spawn parameter controls with slider-based UI."""
    
    def __init__(self):
        """Initialize with defaults from config."""
        self.count = 15
        self.area_width = 400
        self.area_depth = 400
        self.radius_min = 8.0
        self.radius_max = 12.0
    
    def build(self, parent: ui.VStack = None):
        """Build spawn controls UI."""
        with ui.CollapsableFrame("Spawn Settings", height=0, collapsed=False):
            with ui.VStack(spacing=2):
                create_int_slider_row(
                    "Count:", self.count, 1, 30,
                    "Number of tendroids to spawn",
                    lambda v: setattr(self, 'count', v)
                )
                create_int_slider_row(
                    "Area Width:", self.area_width, 100, 800,
                    "Width of spawn area in scene units",
                    lambda v: setattr(self, 'area_width', v)
                )
                create_int_slider_row(
                    "Area Depth:", self.area_depth, 100, 800,
                    "Depth of spawn area in scene units",
                    lambda v: setattr(self, 'area_depth', v)
                )
                create_float_slider_row(
                    "Radius Min:", self.radius_min, 4.0, 20.0,
                    "Minimum tendroid radius",
                    lambda v: setattr(self, 'radius_min', v),
                    precision=1
                )
                create_float_slider_row(
                    "Radius Max:", self.radius_max, 4.0, 20.0,
                    "Maximum tendroid radius",
                    lambda v: setattr(self, 'radius_max', v),
                    precision=1
                )
