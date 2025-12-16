"""
Debug controls section for V2 control panel

Toggle debug visualizations like envelope display.
"""

import omni.ui as ui

from ..scene.manager import V2SceneManager


class DebugControls:
    """Debug visualization controls."""
    
    def __init__(self, scene_manager: V2SceneManager):
        """
        Initialize with scene manager.
        
        Args:
            scene_manager: Scene manager instance for debug toggles
        """
        self.scene_manager = scene_manager
        self._envelope_checkbox = None
        self._envelope_enabled = True  # Start enabled
    
    def build(self, parent: ui.VStack = None):
        """Build debug controls UI."""
        with ui.CollapsableFrame("Debug Visualization", height=0, collapsed=True):
            with ui.VStack(spacing=4, style={"background_color": 0xFF23211F}):
                ui.Spacer(height=4)
                
                # Envelope visualization toggle
                with ui.HStack(height=24, spacing=8):
                    ui.Spacer(width=8)
                    ui.Label("Show Envelope:", width=120)
                    self._envelope_checkbox = ui.CheckBox(
                        width=40,
                        height=20,
                        style={
                            "border_radius": 10,
                            "background_color": 0xFF5FB366 if self._envelope_enabled else 0xFF3C3C3C,
                            "border_width": 1,
                            "border_color": 0xFF555555,
                        }
                    )
                    self._envelope_checkbox.model.set_value(self._envelope_enabled)
                    self._envelope_checkbox.model.add_value_changed_fn(self._on_envelope_toggle)
                    ui.Spacer()
                
                # Legend for envelope zones
                self._build_zone_legend()
                
                ui.Spacer(height=4)
    
    def _on_envelope_toggle(self, model):
        """Handle envelope toggle checkbox."""
        self._envelope_enabled = model.get_value_as_bool()
        
        # Update checkbox style
        if self._envelope_checkbox:
            self._envelope_checkbox.style = {
                "border_radius": 10,
                "background_color": 0xFF5FB366 if self._envelope_enabled else 0xFF3C3C3C,
                "border_width": 1,
                "border_color": 0xFF555555,
            }
        
        # Toggle in scene manager
        if self.scene_manager:
            self.scene_manager.set_envelope_debug(self._envelope_enabled)
    
    def _build_zone_legend(self):
        """Build color legend for envelope zones."""
        zones = [
            ("Detection", 0xFF33FF33, "Outer awareness"),
            ("Warning", 0xFF33FFFF, "Attention zone"),
            ("Recovery", 0xFF33AAFF, "Safe clearance"),
            ("Contact", 0xFF3333FF, "Danger zone"),
            ("Envelope", 0xFFFFCC33, "Physical boundary"),
        ]
        
        with ui.HStack(height=0):
            ui.Spacer(width=8)
            with ui.VStack(spacing=2):
                ui.Spacer(height=4)
                ui.Label(
                    "Zone Colors:",
                    style={"color": 0xFFAAAAAA, "font_size": 11}
                )
                for name, color, desc in zones:
                    with ui.HStack(height=14, spacing=4):
                        # Color swatch
                        ui.Rectangle(
                            width=12, height=12,
                            style={"background_color": color, "border_radius": 2}
                        )
                        ui.Label(
                            f"{name}",
                            width=70,
                            style={"color": 0xFF808080, "font_size": 11}
                        )
                        ui.Label(
                            f"- {desc}",
                            style={"color": 0xFF606060, "font_size": 10}
                        )
                ui.Spacer(height=4)
