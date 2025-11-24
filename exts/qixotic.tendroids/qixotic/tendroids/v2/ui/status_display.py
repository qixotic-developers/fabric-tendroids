"""
Status display section for V2 control panel

Shows tendroid count, animation state, and performance info.
"""

import omni.ui as ui


class StatusDisplay:
    """Status display with count, animation state, and FPS."""
    
    def __init__(self):
        """Initialize status display."""
        self._status_label = None
        self._count_label = None
        self._anim_label = None
        self._fps_label = None
    
    def build(self, parent: ui.VStack = None):
        """Build status display UI."""
        with ui.CollapsableFrame("Status", height=0, collapsed=False):
            with ui.VStack(spacing=2):
                # Count and animation state row
                with ui.HStack(height=20, spacing=10):
                    ui.Label("Tendroids:", width=70)
                    self._count_label = ui.Label("0", width=40)
                    ui.Label("Animation:", width=70)
                    self._anim_label = ui.Label("Stopped", width=60)
                
                # Status message row
                with ui.HStack(height=20, spacing=4):
                    ui.Label("Status:", width=50)
                    self._status_label = ui.Label("Ready", style={"color": 0xFF888888})
    
    def update_status(self, message: str):
        """Update status message."""
        if self._status_label:
            self._status_label.text = message
    
    def update_count(self, count: int):
        """Update tendroid count."""
        if self._count_label:
            self._count_label.text = str(count)
    
    def update_animation_state(self, running: bool):
        """Update animation state display."""
        if self._anim_label:
            self._anim_label.text = "Running" if running else "Stopped"
            self._anim_label.style = {"color": 0xFF88FF88 if running else 0xFFFF8888}
