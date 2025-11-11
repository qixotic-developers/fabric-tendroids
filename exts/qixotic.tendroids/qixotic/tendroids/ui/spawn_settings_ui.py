"""
Spawn settings UI with compact two-column layout and tooltips

Manages all spawn parameter widgets with conditional visibility.
"""

import omni.ui as ui


class SpawnSettingsUI:
  """
  Manages spawn parameter UI with tooltips and two-column layout.
  
  Shows detailed parameters for single Tendroid mode,
  simplified settings for multi-spawn mode.
  """
  
  def __init__(self):
    """Initialize spawn settings UI."""
    # Spawn settings
    self.spawn_count = 1
    self.spawn_width = 200
    self.spawn_depth = 200
    
    # Single tendroid settings
    self.single_diameter = 20.0
    self.single_length = 160.0
    self.bulge_size_percent = 40.0
    self.amplitude = 0.5
    self.wave_speed = 40.0
    self.pause_duration = 2.0
    
    # Multi-tendroid settings
    self.num_segments = 16
    
    # UI references
    self.single_settings_frame = None
    self.multi_settings_frame = None
    
    # Callback for count changes
    self.on_count_changed_callback = None
  
  def create_ui(self, parent_stack: ui.VStack):
    """Create compact two-column spawn settings UI."""
    with ui.CollapsableFrame("Spawn Settings", height=0, collapsed=False):
      with ui.VStack(spacing=3):
        # Count (full width)
        with ui.HStack(spacing=5):
          ui.Label("Count:", width=80)
          count_field = ui.IntDrag(min=1, max=15, step=1, tooltip="Number of Tendroids to spawn")
          count_field.model.set_value(self.spawn_count)
          count_field.model.add_value_changed_fn(
            lambda m: self._on_count_changed(m.get_value_as_int())
          )
    
    # Single Tendroid Settings (conditional)
    self._create_single_settings()
    
    # Multi-Spawn Settings (conditional)
    self._create_multi_settings()
  
  def _create_single_settings(self):
    """Create single tendroid parameter controls in two columns."""
    self.single_settings_frame = ui.CollapsableFrame(
      "Single Tendroid",
      height=0,
      collapsed=False,
      visible=(self.spawn_count == 1)
    )
    with self.single_settings_frame:
      with ui.HStack(spacing=10):
        # Left column
        with ui.VStack(spacing=3, width=ui.Fraction(1)):
          self._create_param("Diameter:", self.single_diameter, 2.0, 100.0, 2.0,
                           "single_diameter", "Initial cylinder diameter")
          self._create_param("Length:", self.single_length, 10.0, 500.0, 10.0,
                           "single_length", "Cylinder height")
          self._create_param("Wave Size %:", self.bulge_size_percent, 5.0, 50.0, 2.0,
                           "bulge_size_percent", "Traveling bulge size as % of length")
        
        # Right column
        with ui.VStack(spacing=3, width=ui.Fraction(1)):
          self._create_param("Amplitude:", self.amplitude, 0.0, 1.0, 0.1,
                           "amplitude", "Maximum radial expansion (0.5 = 50%)")
          self._create_param("Wave Speed:", self.wave_speed, 10.0, 200.0, 10.0,
                           "wave_speed", "Speed of traveling wave")
          self._create_param("Pause (sec):", self.pause_duration, 0.0, 10.0, 1.0,
                           "pause_duration", "Pause between breathing cycles")
  
  def _create_multi_settings(self):
    """Create multi-tendroid spawn controls in two columns."""
    self.multi_settings_frame = ui.CollapsableFrame(
      "Multi-Spawn",
      height=0,
      collapsed=False,
      visible=(self.spawn_count > 1)
    )
    with self.multi_settings_frame:
      with ui.HStack(spacing=10):
        # Left column
        with ui.VStack(spacing=3, width=ui.Fraction(1)):
          self._create_param("Area Width:", self.spawn_width, 50, 1000, 25,
                           "spawn_width", "Spawn area width", is_int=True)
        
        # Right column
        with ui.VStack(spacing=3, width=ui.Fraction(1)):
          self._create_param("Area Depth:", self.spawn_depth, 50, 1000, 25,
                           "spawn_depth", "Spawn area depth", is_int=True)
      
      # Segments (full width below)
      with ui.HStack(spacing=5):
        ui.Label("Segments:", width=80)
        segments_field = ui.IntDrag(min=8, max=32, step=2, 
                                   tooltip="Vertical resolution per Tendroid")
        segments_field.model.set_value(self.num_segments)
        segments_field.model.add_value_changed_fn(
          lambda m: setattr(self, 'num_segments', m.get_value_as_int())
        )
  
  def _create_param(self, label: str, value: float, min_val: float, max_val: float,
                    step: float, attr_name: str, tooltip: str, is_int: bool = False):
    """Helper to create a parameter control with tooltip."""
    with ui.HStack(spacing=3):
      ui.Label(label, width=80)
      if is_int:
        field = ui.IntDrag(min=int(min_val), max=int(max_val), 
                          step=int(step), tooltip=tooltip)
        field.model.set_value(int(value))
        field.model.add_value_changed_fn(
          lambda m: setattr(self, attr_name, m.get_value_as_int())
        )
      else:
        field = ui.FloatDrag(min=min_val, max=max_val, 
                            step=step, tooltip=tooltip)
        field.model.set_value(value)
        field.model.add_value_changed_fn(
          lambda m: setattr(self, attr_name, m.get_value_as_float())
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
