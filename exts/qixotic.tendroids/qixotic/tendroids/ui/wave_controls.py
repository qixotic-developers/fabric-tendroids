"""
Wave controls section for V2 control panel

Manages wave motion parameters with live updates.
Now includes tidal phase parameters.
"""

import omni.ui as ui
from .slider_row import create_float_slider_row


class WaveControls:
    """Wave motion parameter controls with live binding."""
    
    def __init__(self, wave_controller=None):
        """
        Initialize wave controls.
        
        Args:
            wave_controller: WaveController to bind (can be set later)
        """
        self.wave_controller = wave_controller
        self._enabled_checkbox = None
        self._amplitude_slider = None
        self._frequency_slider = None
        
        # Phase parameter sliders
        self._shore_force_min_slider = None
        self._shore_force_max_slider = None
        self._shore_duration_min_slider = None
        self._shore_duration_max_slider = None
        self._rest_duration_min_slider = None
        self._rest_duration_max_slider = None
    
    def set_wave_controller(self, wave_controller):
        """Bind to a wave controller for live updates."""
        self.wave_controller = wave_controller
    
    def build(self, parent: ui.VStack = None):
        """Build wave controls UI."""
        with ui.CollapsableFrame("Wave Motion", height=0, collapsed=False):
            with ui.VStack(spacing=4, style={"background_color": 0xFF23211F}):
                ui.Spacer(height=4)
                # Enable toggle
                with ui.HStack(height=24, spacing=4):
                    ui.Label("Enable:", width=100, tooltip="Toggle wave motion on/off")
                    enabled = self.wave_controller.enabled if self.wave_controller else True
                    self._enabled_checkbox = ui.CheckBox(
                        width=40,
                        height=20,
                        style={
                            "border_radius": 10,
                            "background_color": 0xFF5FB366 if enabled else 0xFF3C3C3C,
                            "border_width": 1,
                            "border_color": 0xFF555555,
                        }
                    )
                    self._enabled_checkbox.model.set_value(enabled)
                    self._enabled_checkbox.model.add_value_changed_fn(self._on_enabled_changed)
                
                # Amplitude slider
                initial_amp = self.wave_controller.config.amplitude if self.wave_controller else 8.0
                self._amplitude_slider = create_float_slider_row(
                    "Amplitude:", initial_amp, 0.0, 30.0,
                    "Maximum horizontal displacement at tendroid tip",
                    self._on_amplitude_changed,
                    precision=1
                )
                
                # Frequency slider (now affects overall cycle speed)
                initial_freq = self.wave_controller.config.frequency if self.wave_controller else 0.15
                self._frequency_slider = create_float_slider_row(
                    "Frequency:", initial_freq, 0.05, 0.5,
                    "Overall wave cycle speed multiplier",
                    self._on_frequency_changed,
                    precision=2
                )
                
                # Tidal phase parameters
                ui.Label("Shore Surge (strong, quick):", height=20)
                
                cfg = self.wave_controller.config if self.wave_controller else None
                self._shore_force_min_slider = create_float_slider_row(
                    "  Min Force:", cfg.shore_force_min if cfg else 0.8, 0.5, 2.0,
                    "Minimum shore surge force multiplier",
                    self._on_shore_force_min_changed,
                    precision=2
                )
                
                self._shore_force_max_slider = create_float_slider_row(
                    "  Max Force:", cfg.shore_force_max if cfg else 1.2, 0.5, 2.0,
                    "Maximum shore surge force multiplier",
                    self._on_shore_force_max_changed,
                    precision=2
                )
                
                self._shore_duration_min_slider = create_float_slider_row(
                    "  Min Duration:", cfg.shore_duration_min if cfg else 1.0, 0.5, 3.0,
                    "Minimum shore surge duration (seconds)",
                    self._on_shore_duration_min_changed,
                    precision=1
                )
                
                self._shore_duration_max_slider = create_float_slider_row(
                    "  Max Duration:", cfg.shore_duration_max if cfg else 2.0, 0.5, 3.0,
                    "Maximum shore surge duration (seconds)",
                    self._on_shore_duration_max_changed,
                    precision=1
                )
                
                ui.Label("Rest Phase (return to center):", height=20)
                
                self._rest_duration_min_slider = create_float_slider_row(
                    "  Min Duration:", cfg.rest_duration_min if cfg else 0.5, 0.1, 2.0,
                    "Minimum rest duration (seconds)",
                    self._on_rest_duration_min_changed,
                    precision=1
                )
                
                self._rest_duration_max_slider = create_float_slider_row(
                    "  Max Duration:", cfg.rest_duration_max if cfg else 1.5, 0.1, 2.0,
                    "Maximum rest duration (seconds)",
                    self._on_rest_duration_max_changed,
                    precision=1
                )
                
                ui.Label("Ebb: Gentle seaward (force/duration calculated)", height=20)
                ui.Spacer(height=4)
    
    def _on_enabled_changed(self, model):
        """Handle enable/disable toggle."""
        if self.wave_controller:
            self.wave_controller.enabled = model.get_value_as_bool()
    
    def _on_amplitude_changed(self, value: float):
        """Handle amplitude slider change."""
        if self.wave_controller:
            self.wave_controller.config.amplitude = value
    
    def _on_frequency_changed(self, value: float):
        """Handle frequency slider change."""
        if self.wave_controller:
            self.wave_controller.config.frequency = value
    
    def _on_shore_force_min_changed(self, value: float):
        """Handle shore force min change."""
        if self.wave_controller:
            self.wave_controller.config.shore_force_min = value
    
    def _on_shore_force_max_changed(self, value: float):
        """Handle shore force max change."""
        if self.wave_controller:
            self.wave_controller.config.shore_force_max = value
    
    def _on_shore_duration_min_changed(self, value: float):
        """Handle shore duration min change."""
        if self.wave_controller:
            self.wave_controller.config.shore_duration_min = value
    
    def _on_shore_duration_max_changed(self, value: float):
        """Handle shore duration max change."""
        if self.wave_controller:
            self.wave_controller.config.shore_duration_max = value
    
    def _on_rest_duration_min_changed(self, value: float):
        """Handle rest duration min change."""
        if self.wave_controller:
            self.wave_controller.config.rest_duration_min = value
    
    def _on_rest_duration_max_changed(self, value: float):
        """Handle rest duration max change."""
        if self.wave_controller:
            self.wave_controller.config.rest_duration_max = value
