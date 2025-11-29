"""
Spawn controls section for V2 control panel

Simplified to show only tendroid count.
"""

import omni.ui as ui
from .slider_row import create_int_slider_row


class SpawnControls:
    """Spawn parameter controls - simplified to count only."""
    
    def __init__(self):
        """Initialize with default count."""
        self.count = 15
    
    def build(self, parent: ui.VStack = None):
        """Build spawn controls UI."""
        with ui.CollapsableFrame("Spawn Settings", height=0, collapsed=False):
            with ui.VStack(spacing=4, style={"background_color": 0xFF23211F}):
                ui.Spacer(height=4)
                create_int_slider_row(
                    "Count:", self.count, 1, 30,
                    "Number of tendroids to spawn",
                    lambda v: setattr(self, 'count', v)
                )
                ui.Spacer(height=4)
