"""
Spawn settings UI components for Tendroid control panel

Manages all spawn parameter widgets with conditional visibility.
"""

import omni.ui as ui


class SpawnSettingsUI:
  """
  Manages spawn parameter UI elements with single/multi mode switching.
  
  Shows detailed parameters for single Tendroid mode,
  simplified settings for multi-spawn mode.
  """
  
  def __init__(self):
    """Initialize spawn settings UI."""
    # Spawn settings
    self.spawn_count = 1  # Start with single mode
    self.spawn_width = 200
    self.spawn_depth = 200
    
    # Single tendroid settings (only used when count == 1)
    self.single_diameter = 20.0
    self.single_length = 160.0  # 8:1 aspect ratio default
    self.bulge_size_percent = 40.0
    self.amplitude = 0.5  # Updated default
    self.wave_speed = 40.0
    self.pause_duration = 2.0
    
    # Multi-tendroid settings
    self.num_segments = 16
    
    # UI references for conditional visibility
    self.single_settings_frame = None
    self.multi_settings_frame = None
    
    # Callback for count changes
    self.on_count_changed_callback = None
  
  def create_ui(self, parent_stack: ui.VStack):
    """
    Create spawn settings UI elements.
    
    Args:
        parent_stack: Parent VStack to add settings to
    """
    # === SPAWN SETTINGS ===
    with ui.CollapsableFrame("Spawn Settings", height=0, collapsed=False):
      with ui.VStack(spacing=5):
        # Count slider
        with ui.HStack():
          ui.Label("Count:", width=100)
          count_field = ui.IntDrag(min=1, max=15, step=1)
          count_field.model.set_value(self.spawn_count)
          count_field.model.add_value_changed_fn(
            lambda m: self._on_count_changed(m.get_value_as_int())
          )
        ui.Label(
          "Number of tendroids to spawn",
          style={"font_size": 14, "color": 0xFF888888}
        )
    
    ui.Spacer(height=5)
    
    # === SINGLE TENDROID SETTINGS (conditional) ===
    self._create_single_settings()
    
    ui.Spacer(height=5)
    
    # === MULTI-TENDROID SETTINGS (conditional) ===
    self._create_multi_settings()
  
  def _create_single_settings(self):
    """Create single tendroid parameter controls."""
    self.single_settings_frame = ui.CollapsableFrame(
      "Single Tendroid Settings",
      height=0,
      collapsed=False,
      visible=(self.spawn_count == 1)
    )
    with self.single_settings_frame:
      with ui.VStack(spacing=5):
        # Diameter - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Diameter:", width=100)
          diameter_field = ui.FloatDrag(min=2.0, max=100.0, step=2.0)
          diameter_field.model.set_value(self.single_diameter)
          diameter_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'single_diameter', m.get_value_as_float())
          )
        ui.Label(
          "Initial diameter of cylinder",
          style={"font_size": 14, "color": 0xFF888888}
        )
        
        # Length - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Length:", width=100)
          length_field = ui.FloatDrag(min=10.0, max=500.0, step=10.0)
          length_field.model.set_value(self.single_length)
          length_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'single_length', m.get_value_as_float())
          )
        ui.Label(
          "Height of cylinder",
          style={"font_size": 14, "color": 0xFF888888}
        )
        
        # Wave Size - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Wave Size (%):", width=100)
          wave_size_field = ui.FloatDrag(min=5.0, max=50.0, step=2.0)
          wave_size_field.model.set_value(self.bulge_size_percent)
          wave_size_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'bulge_size_percent', m.get_value_as_float())
          )
        ui.Label(
          "Size of traveling bulge as % of length",
          style={"font_size": 14, "color": 0xFF888888}
        )
        
        # Amplitude - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Amplitude:", width=100)
          amplitude_field = ui.FloatDrag(min=0.0, max=1.0, step=0.1)
          amplitude_field.model.set_value(self.amplitude)
          amplitude_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'amplitude', m.get_value_as_float())
          )
        ui.Label(
          "Maximum radial expansion (0.5 = 50%)",
          style={"font_size": 14, "color": 0xFF888888}
        )
        
        # Wave Speed - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Wave Speed:", width=100)
          speed_field = ui.FloatDrag(min=10.0, max=200.0, step=10.0)
          speed_field.model.set_value(self.wave_speed)
          speed_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'wave_speed', m.get_value_as_float())
          )
        ui.Label(
          "Speed of traveling wave",
          style={"font_size": 14, "color": 0xFF888888}
        )
        
        # Pause Duration - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Pause (sec):", width=100)
          pause_field = ui.FloatDrag(min=0.0, max=10.0, step=1.0)
          pause_field.model.set_value(self.pause_duration)
          pause_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'pause_duration', m.get_value_as_float())
          )
        ui.Label(
          "Pause between breathing cycles",
          style={"font_size": 14, "color": 0xFF888888}
        )
  
  def _create_multi_settings(self):
    """Create multi-tendroid spawn controls."""
    self.multi_settings_frame = ui.CollapsableFrame(
      "Multi-Spawn Settings",
      height=0,
      collapsed=False,
      visible=(self.spawn_count > 1)
    )
    with self.multi_settings_frame:
      with ui.VStack(spacing=5):
        # Spawn area width - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Area Width:", width=100)
          width_field = ui.IntDrag(min=50, max=1000, step=25)
          width_field.model.set_value(self.spawn_width)
          width_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'spawn_width', m.get_value_as_int())
          )
        
        # Spawn area depth - step increased for less sensitivity
        with ui.HStack():
          ui.Label("Area Depth:", width=100)
          depth_field = ui.IntDrag(min=50, max=1000, step=25)
          depth_field.model.set_value(self.spawn_depth)
          depth_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'spawn_depth', m.get_value_as_int())
          )
        
        # Segments per Tendroid - step unchanged (already 1)
        with ui.HStack():
          ui.Label("Segments:", width=100)
          segments_field = ui.IntDrag(min=8, max=32, step=2)
          segments_field.model.set_value(self.num_segments)
          segments_field.model.add_value_changed_fn(
            lambda m: setattr(self, 'num_segments', m.get_value_as_int())
          )
  
  def _on_count_changed(self, value: int):
    """Handle spawn count changes - show/hide conditional sections."""
    self.spawn_count = value
    
    # Show/hide conditional frames
    if self.single_settings_frame:
      self.single_settings_frame.visible = (value == 1)
    if self.multi_settings_frame:
      self.multi_settings_frame.visible = (value > 1)
    
    # Notify parent if callback registered
    if self.on_count_changed_callback:
      self.on_count_changed_callback(value)
