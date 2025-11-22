"""
Bubble Controls UI Builder

Creates UI controls for bubble system parameters with real-time updates.
Compact design with essential controls only.
"""

import omni.ui as ui
import carb


class BubbleControlsBuilder:
    """Builds bubble parameter controls for UI panel."""
    
    def __init__(self, bubble_manager):
        """
        Initialize bubble controls builder.
        
        Args:
            bubble_manager: BubbleManager instance to control
        """
        self.bubble_manager = bubble_manager
        self.config = bubble_manager.config
        carb.log_info("[BubbleControls] Initialized with diameter_multiplier: {:.2f}".format(
            self.config.diameter_multiplier
        ))
        
    def build(self):
        """Build bubble controls UI section."""
        with ui.CollapsableFrame("Bubble Controls", height=0, collapsed=False):
            with ui.VStack(spacing=5):
                self._build_visibility_controls()  # Add visibility controls first
                self._build_geometry_controls()
                self._build_timing_controls()
                self._build_physics_controls()
    
    def _build_visibility_controls(self):
        """Build bubble visibility controls including Hide Until Clear toggle."""
        with ui.VStack(spacing=3):
            ui.Label("Visibility", height=20, style={"font_size": 14})
            
            # Hide Until Clear checkbox
            with ui.HStack(height=25):
                ui.Label("Hide Until Clear:", width=100)
                
                # Get current setting, default to True
                current_value = getattr(self.config, 'hide_until_clear', True)
                
                checkbox = ui.CheckBox(default=current_value)
                checkbox.model.add_value_changed_fn(
                    lambda model: self._on_hide_until_clear_changed(model.as_bool)
                )
                
                ui.Label("(Prevents clipping)", width=100, style={"color": 0xFF888888})
            
            # Add a separator
            ui.Spacer(height=3)
    
    def _on_hide_until_clear_changed(self, value: bool):
        """Handle Hide Until Clear checkbox change."""
        if hasattr(self.config, 'hide_until_clear'):
            self.config.hide_until_clear = value
        else:
            # Add the attribute if it doesn't exist
            setattr(self.config, 'hide_until_clear', value)
        
        status = "ENABLED" if value else "DISABLED"
        carb.log_info(f"[BubbleControls] Hide Until Clear: {status}")
        carb.log_warn(f"Bubble visibility fix: {status}")
    
    def _build_geometry_controls(self):
        """Build bubble geometry controls."""
        carb.log_info("[BubbleControls] Building geometry controls...")
        
        with ui.VStack(spacing=3):
            ui.Label("Geometry", height=20, style={"font_size": 14})
            
            # Diameter multiplier
            with ui.HStack(height=20):
                ui.Label("Diameter:", width=80)
                slider = ui.FloatSlider(
                    min=0.1,
                    max=2.0,
                    height=20
                )
                slider.model.set_value(self.config.diameter_multiplier)
                slider.model.add_value_changed_fn(
                    lambda m: self._on_diameter_changed(m.get_value_as_float())
                )
                value_label = ui.Label(
                    f"{self.config.diameter_multiplier:.2f}",
                    width=40
                )
                slider.model.add_value_changed_fn(
                    lambda m: value_label.set_text(f"{m.get_value_as_float():.2f}")
                )
        
        carb.log_info("[BubbleControls] Geometry controls built")
    
    def _build_timing_controls(self):
        """Build bubble pop timing controls."""
        carb.log_info("[BubbleControls] Building timing controls...")
        
        with ui.VStack(spacing=3):
            ui.Spacer(height=5)
            ui.Label("Pop Timing", height=20, style={"font_size": 14})
            
            # Min pop time
            with ui.HStack(height=20):
                ui.Label("Min Time:", width=80)
                slider = ui.FloatSlider(
                    min=5.0,
                    max=30.0,
                    height=20
                )
                slider.model.set_value(self.config.min_pop_time)
                slider.model.add_value_changed_fn(
                    lambda m: self._on_min_pop_time_changed(m.get_value_as_float())
                )
                value_label = ui.Label(
                    f"{self.config.min_pop_time:.1f}s",
                    width=40
                )
                slider.model.add_value_changed_fn(
                    lambda m: value_label.set_text(f"{m.get_value_as_float():.1f}s")
                )
            
            # Max pop time
            with ui.HStack(height=20):
                ui.Label("Max Time:", width=80)
                slider = ui.FloatSlider(
                    min=5.0,
                    max=40.0,
                    height=20
                )
                slider.model.set_value(self.config.max_pop_time)
                slider.model.add_value_changed_fn(
                    lambda m: self._on_max_pop_time_changed(m.get_value_as_float())
                )
                value_label = ui.Label(
                    f"{self.config.max_pop_time:.1f}s",
                    width=40
                )
                slider.model.add_value_changed_fn(
                    lambda m: value_label.set_text(f"{m.get_value_as_float():.1f}s")
                )
        
        carb.log_info("[BubbleControls] Timing controls built")
    
    def _build_physics_controls(self):
        """Build bubble physics controls."""
        carb.log_info("[BubbleControls] Building physics controls...")
        
        with ui.VStack(spacing=3):
            ui.Spacer(height=5)
            ui.Label("Physics", height=20, style={"font_size": 14})
            
            # Rise speed
            with ui.HStack(height=20):
                ui.Label("Rise Speed:", width=80)
                slider = ui.FloatSlider(
                    min=10.0,
                    max=50.0,
                    height=20
                )
                slider.model.set_value(self.config.rise_speed)
                slider.model.add_value_changed_fn(
                    lambda m: self._on_rise_speed_changed(m.get_value_as_float())
                )
                value_label = ui.Label(
                    f"{self.config.rise_speed:.1f}",
                    width=40
                )
                slider.model.add_value_changed_fn(
                    lambda m: value_label.set_text(f"{m.get_value_as_float():.1f}")
                )
        
        carb.log_info("[BubbleControls] Physics controls built")
    
    def _on_diameter_changed(self, value: float):
        """Handle diameter multiplier change."""
        self.config.diameter_multiplier = value
        carb.log_info(f"[BubbleControls] Diameter multiplier changed to: {value:.2f}")
    
    def _on_min_pop_time_changed(self, value: float):
        """Handle min pop time change."""
        # Ensure min < max
        if value >= self.config.max_pop_time:
            value = self.config.max_pop_time - 1.0
        
        self.config.min_pop_time = value
        self.bubble_manager.set_pop_time_range(value, self.config.max_pop_time)
        carb.log_info(f"[BubbleControls] Min pop time: {value:.1f}s")
    
    def _on_max_pop_time_changed(self, value: float):
        """Handle max pop time change."""
        # Ensure max > min
        if value <= self.config.min_pop_time:
            value = self.config.min_pop_time + 1.0
        
        self.config.max_pop_time = value
        self.bubble_manager.set_pop_time_range(self.config.min_pop_time, value)
        carb.log_info(f"[BubbleControls] Max pop time: {value:.1f}s")
    
    def _on_rise_speed_changed(self, value: float):
        """Handle rise speed change."""
        self.config.rise_speed = value
        carb.log_info(f"[BubbleControls] Rise speed: {value:.1f}")
