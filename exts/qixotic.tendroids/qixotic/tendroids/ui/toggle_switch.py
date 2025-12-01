"""
Custom toggle switch widget for omni.ui

Creates a visual toggle switch similar to the extension enable/disable switch.
"""

import omni.ui as ui


class ToggleSwitch:
    """
    Custom toggle switch widget that looks like extension on/off toggles.
    
    Provides a more polished visual than plain checkboxes.
    """
    
    def __init__(self, initial_value: bool = True, width: int = 40, height: int = 20,
                 on_value_changed=None, tooltip: str = ""):
        """
        Create a toggle switch.
        
        Args:
            initial_value: Starting on/off state
            width: Widget width in pixels
            height: Widget height in pixels  
            on_value_changed: Callback function(bool) when value changes
            tooltip: Tooltip text
        """
        self._value = initial_value
        self._callback = on_value_changed
        self._container = None
        self._build(width, height, tooltip)
    
    def _build(self, width: int, height: int, tooltip: str):
        """Build the toggle switch UI."""
        # Use a styled checkbox that looks like a toggle
        with ui.ZStack(width=width, height=height, tooltip=tooltip):
            # Background container
            with ui.Rectangle(
                style={
                    "background_color": 0xFF3C3C3C if not self._value else 0xFF5FB366,
                    "border_radius": height // 2,
                    "border_width": 1,
                    "border_color": 0xFF555555,
                }
            ):
                pass
            
            # Toggle knob
            with ui.HStack():
                if not self._value:
                    ui.Spacer(width=2)
                    with ui.Circle(
                        width=height - 4,
                        height=height - 4,
                        style={"background_color": 0xFFE0E0E0}
                    ):
                        pass
                    ui.Spacer()
                else:
                    ui.Spacer()
                    with ui.Circle(
                        width=height - 4,
                        height=height - 4,
                        style={"background_color": 0xFFFFFFFF}
                    ):
                        pass
                    ui.Spacer(width=2)
            
            # Invisible clickable overlay
            self._button = ui.Button(
                "",
                width=width,
                height=height,
                clicked_fn=self._on_clicked,
                style={
                    "background_color": 0x00000000,
                    "border_width": 0,
                }
            )
    
    def _on_clicked(self):
        """Handle toggle click."""
        self._value = not self._value
        if self._callback:
            self._callback(self._value)
        # Force UI rebuild to update visual state
        # Note: In production, should use dynamic styling instead
    
    def get_value(self) -> bool:
        """Get current toggle state."""
        return self._value
    
    def set_value(self, value: bool):
        """Set toggle state programmatically."""
        if self._value != value:
            self._value = value
            # Force UI rebuild
