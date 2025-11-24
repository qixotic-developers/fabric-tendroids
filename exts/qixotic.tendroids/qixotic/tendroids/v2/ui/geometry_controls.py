"""
Geometry controls section for V2 control panel

Manages tendroid mesh resolution and flare settings.
"""

import omni.ui as ui
from .slider_row import create_int_slider_row, create_float_slider_row


class GeometryControls:
    """Tendroid geometry parameter controls."""
    
    def __init__(self):
        """Initialize with defaults from config."""
        self.radial_segments = 24
        self.height_segments = 48
        self.flare_height_pct = 15.0
        self.flare_radius_mult = 2.0
    
    def build(self, parent: ui.VStack = None):
        """Build geometry controls UI."""
        with ui.CollapsableFrame("Tendroid Geometry", height=0, collapsed=True):
            with ui.VStack(spacing=2):
                create_int_slider_row(
                    "Radial Segs:", self.radial_segments, 8, 48,
                    "Circumference resolution (more = smoother)",
                    lambda v: setattr(self, 'radial_segments', v)
                )
                create_int_slider_row(
                    "Height Segs:", self.height_segments, 16, 96,
                    "Vertical resolution (more = smoother deformation)",
                    lambda v: setattr(self, 'height_segments', v)
                )
                create_float_slider_row(
                    "Flare Height %:", self.flare_height_pct, 5.0, 30.0,
                    "Height of flared base as % of total length",
                    lambda v: setattr(self, 'flare_height_pct', v),
                    precision=1
                )
                create_float_slider_row(
                    "Flare Radius:", self.flare_radius_mult, 1.0, 3.0,
                    "Base flare radius multiplier",
                    lambda v: setattr(self, 'flare_radius_mult', v),
                    precision=1
                )
