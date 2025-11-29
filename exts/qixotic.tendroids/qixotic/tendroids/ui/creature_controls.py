"""
Creature controls section for V2 control panel

Controls for the interactive player creature.
"""

import omni.ui as ui


class CreatureControls:
    """Creature control settings - spawn and control player creature."""
    
    def __init__(self):
        """Initialize with default settings."""
        self.enabled = True  # Spawn creature by default
        self._checkbox = None
    
    def build(self, parent: ui.VStack = None):
        """Build creature controls UI."""
        with ui.CollapsableFrame("Creature Settings", height=0, collapsed=False):
            with ui.VStack(spacing=4, style={"background_color": 0xFF23211F}):
                ui.Spacer(height=4)
                
                # Spawn creature checkbox
                with ui.HStack(height=20, spacing=8):
                    ui.Spacer(width=8)
                    ui.Label("Spawn Creature:", width=120)
                    self._checkbox = ui.CheckBox(width=20)
                    self._checkbox.model.set_value(self.enabled)
                    self._checkbox.model.add_value_changed_fn(
                        lambda m: setattr(self, 'enabled', m.get_value_as_bool())
                    )
                    ui.Spacer()
                
                # Info text about controls
                with ui.HStack(height=0):
                    ui.Spacer(width=8)
                    with ui.VStack(spacing=2):
                        ui.Spacer(height=4)
                        ui.Label(
                            "WASD/Arrows: Move",
                            style={"color": 0xFF808080, "font_size": 12}
                        )
                        ui.Label(
                            "Space/Shift: Up/Down",
                            style={"color": 0xFF808080, "font_size": 12}
                        )
                        ui.Spacer(height=4)
                
                ui.Spacer(height=4)
