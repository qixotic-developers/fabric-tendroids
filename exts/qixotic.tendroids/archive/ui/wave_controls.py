"""
Wave controls UI for Tendroid control panel

Provides UI controls for wave motion parameters.
"""

import carb
import omni.ui as ui


class WaveControlsBuilder:
    """
    UI controls for wave motion system.
    
    Provides sliders and controls for:
    - Enable/disable wave motion
    - Amplitude control
    - Frequency control
    - Direction adjustment
    """
    
    def __init__(self, wave_controller):
        """
        Initialize wave controls builder.
        
        Args:
            wave_controller: WaveController instance to control
        """
        self.wave_controller = wave_controller
        self._enabled_checkbox = None
        self._amplitude_slider = None
        self._frequency_slider = None
        
    def build(self):
        """Build wave control UI elements."""
        with ui.VStack(spacing=3):
            # Section header
            with ui.HStack(height=20):
                ui.Label("Wave Motion", 
                        style={"font_size": 14, "color": 0xFF88AAFF})
            
            # Enable/disable checkbox
            with ui.HStack(height=20):
                ui.Label("Enable Wave", width=100)
                self._enabled_checkbox = ui.CheckBox(
                    width=20,
                    height=20
                )
                self._enabled_checkbox.model.set_value(self.wave_controller.enabled)
                self._enabled_checkbox.model.add_value_changed_fn(
                    self._on_enabled_changed
                )
            
            # Amplitude slider
            with ui.HStack(height=20):
                ui.Label("Amplitude", width=100)
                self._amplitude_slider = ui.FloatSlider(
                    min=0.0,
                    max=50.0,
                    step=1.0
                )
                self._amplitude_slider.model.set_value(
                    self.wave_controller.config.amplitude
                )
                amplitude_label = ui.Label(
                    f"{self.wave_controller.config.amplitude:.1f}",
                    width=40
                )
                self._amplitude_slider.model.add_value_changed_fn(
                    lambda m: self._on_amplitude_changed(m, amplitude_label)
                )
            
            # Frequency slider
            with ui.HStack(height=20):
                ui.Label("Frequency", width=100)
                self._frequency_slider = ui.FloatSlider(
                    min=0.05,
                    max=1.0,
                    step=0.05
                )
                self._frequency_slider.model.set_value(
                    self.wave_controller.config.frequency
                )
                frequency_label = ui.Label(
                    f"{self.wave_controller.config.frequency:.2f}",
                    width=40
                )
                self._frequency_slider.model.add_value_changed_fn(
                    lambda m: self._on_frequency_changed(m, frequency_label)
                )
            
            # Direction info (read-only for now)
            with ui.HStack(height=20):
                ui.Label("Direction", width=100)
                dir_x, dir_y, dir_z = self.wave_controller.config.direction
                ui.Label(f"({dir_x:.1f}, {dir_y:.1f}, {dir_z:.1f})",
                        style={"color": 0xFF888888})
            
            # Reset button
            with ui.HStack(height=25):
                ui.Button(
                    "Reset Wave Settings",
                    clicked_fn=self._on_reset_clicked,
                    height=25
                )
    
    def _on_enabled_changed(self, model):
        """Handle wave enable/disable toggle."""
        enabled = model.get_value_as_bool()
        self.wave_controller.enabled = enabled
        
        status = "enabled" if enabled else "disabled"
        carb.log_info(f"[WaveControls] Wave motion {status}")
    
    def _on_amplitude_changed(self, model, label):
        """Handle amplitude slider change."""
        value = model.get_value_as_float()
        self.wave_controller.config.amplitude = value
        label.text = f"{value:.1f}"
        
        if value > 30:
            carb.log_warn("[WaveControls] High amplitude may cause extreme motion")
    
    def _on_frequency_changed(self, model, label):
        """Handle frequency slider change."""
        value = model.get_value_as_float()
        self.wave_controller.config.frequency = value
        label.text = f"{value:.2f}"
    
    def _on_reset_clicked(self):
        """Reset wave settings to defaults."""
        # Reset controller
        self.wave_controller.config.amplitude = 8.0
        self.wave_controller.config.frequency = 0.15
        self.wave_controller.enabled = True
        
        # Update UI
        if self._amplitude_slider:
            self._amplitude_slider.model.set_value(8.0)
        if self._frequency_slider:
            self._frequency_slider.model.set_value(0.15)
        if self._enabled_checkbox:
            self._enabled_checkbox.model.set_value(True)
        
        carb.log_info("[WaveControls] Wave settings reset to defaults")
