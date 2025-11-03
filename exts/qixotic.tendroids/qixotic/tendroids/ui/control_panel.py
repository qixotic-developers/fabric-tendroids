"""
UI control panel for Tendroid management

Provides spawn settings and conditional single tendroid controls.
"""

import carb
import omni.ui as ui
from ..scene.manager import TendroidSceneManager


class TendroidControlPanel:
  """
  Control panel with spawn settings and conditional single tendroid controls.

  When Count == 1: Shows detailed single tendroid parameters
  When Count > 1: Hides single settings, uses defaults for batch spawn
  """

  def __init__(self, scene_manager: TendroidSceneManager):
    """
    Initialize control panel.

    Args:
        scene_manager: TendroidSceneManager instance to control
    """
    self.animation_label = None
    self.count_label = None
    self.status_label = None
    self.multi_settings_frame = None
    self.scene_manager = scene_manager
    self.window = None

    # Spawn settings
    self.spawn_count = 1  # Start with single mode
    self.spawn_width = 200
    self.spawn_depth = 200

    # Single tendroid settings (only used when count == 1)
    self.single_diameter = 20.0
    self.single_length = 100.0
    self.bulge_size_percent = 40.0  # Updated default: 40%
    self.amplitude = 0.35  # Updated default: 35%
    self.wave_speed = 40.0
    self.pause_duration = 2.0

    # Multi-tendroid settings
    self.num_segments = 16

    # UI references for conditional visibility
    self.single_settings_frame = None

    carb.log_info("[TendroidControlPanel] Initialized")

  def create_window(self):
    """Create the UI window with conditional sections."""
    if self.window:
      return

    self.window = ui.Window(
      "Tendroid Controls",
      width=320,
      height=650
    )

    with self.window.frame:
      with ui.ScrollingFrame(
        horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
        vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED
      ):
        with ui.VStack(spacing=10, height=0):
          # Header
          ui.Label(
            "Tendroid Manager",
            alignment=ui.Alignment.CENTER,
            style={ "font_size": 18 }
          )

          ui.Spacer(height=5)

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
                style={ "font_size": 14, "color": 0xFF888888 }
              )

          ui.Spacer(height=5)

          # === SINGLE TENDROID SETTINGS (conditional) ===
          self.single_settings_frame = ui.CollapsableFrame(
            "Single Tendroid Settings",
            height=0,
            collapsed=False,
            visible=(self.spawn_count == 1)
          )
          with self.single_settings_frame:
            with ui.VStack(spacing=5):
              # Initial Diameter
              with ui.HStack():
                ui.Label("Diameter:", width=100)
                diameter_field = ui.FloatDrag(min=2.0, max=100.0, step=1.0)
                diameter_field.model.set_value(self.single_diameter)
                diameter_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'single_diameter', m.get_value_as_float())
                )
              ui.Label(
                "Initial diameter of cylinder",
                style={ "font_size": 14, "color": 0xFF888888 }
              )

              # Length
              with ui.HStack():
                ui.Label("Length:", width=100)
                length_field = ui.FloatDrag(min=10.0, max=300.0, step=5.0)
                length_field.model.set_value(self.single_length)
                length_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'single_length', m.get_value_as_float())
                )
              ui.Label(
                "Height of cylinder",
                style={ "font_size": 14, "color": 0xFF888888 }
              )

              # Wave Size (% of length)
              with ui.HStack():
                ui.Label("Wave Size (%):", width=100)
                wave_size_field = ui.FloatDrag(min=5.0, max=50.0, step=1.0)
                wave_size_field.model.set_value(self.bulge_size_percent)
                wave_size_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'bulge_size_percent', m.get_value_as_float())
                )
              ui.Label(
                "Size of traveling bulge as % of length",
                style={ "font_size": 14, "color": 0xFF888888 }
              )

              # Amplitude (NEW)
              with ui.HStack():
                ui.Label("Amplitude:", width=100)
                amplitude_field = ui.FloatDrag(min=0.0, max=1.0, step=0.05)
                amplitude_field.model.set_value(self.amplitude)
                amplitude_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'amplitude', m.get_value_as_float())
                )
              ui.Label(
                "Maximum radial expansion (0.35 = 35%)",
                style={ "font_size": 14, "color": 0xFF888888 }
              )

              # Wave Speed
              with ui.HStack():
                ui.Label("Wave Speed:", width=100)
                speed_field = ui.FloatDrag(min=10.0, max=200.0, step=5.0)
                speed_field.model.set_value(self.wave_speed)
                speed_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'wave_speed', m.get_value_as_float())
                )
              ui.Label(
                "Speed of traveling wave",
                style={ "font_size": 14, "color": 0xFF888888 }
              )

              # Pause Duration
              with ui.HStack():
                ui.Label("Pause (sec):", width=100)
                pause_field = ui.FloatDrag(min=0.0, max=10.0, step=0.5)
                pause_field.model.set_value(self.pause_duration)
                pause_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'pause_duration', m.get_value_as_float())
                )
              ui.Label(
                "Pause between breathing cycles",
                style={ "font_size": 14, "color": 0xFF888888 }
              )

          ui.Spacer(height=5)

          # === MULTI-TENDROID SETTINGS (visible when count > 1) ===
          self.multi_settings_frame = ui.CollapsableFrame(
            "Multi-Spawn Settings",
            height=0,
            collapsed=False,
            visible=(self.spawn_count > 1)
          )
          with self.multi_settings_frame:
            with ui.VStack(spacing=5):
              # Spawn area width
              with ui.HStack():
                ui.Label("Area Width:", width=100)
                width_field = ui.IntDrag(min=50, max=1000, step=10)
                width_field.model.set_value(self.spawn_width)
                width_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'spawn_width', m.get_value_as_int())
                )

              # Spawn area depth
              with ui.HStack():
                ui.Label("Area Depth:", width=100)
                depth_field = ui.IntDrag(min=50, max=1000, step=10)
                depth_field.model.set_value(self.spawn_depth)
                depth_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'spawn_depth', m.get_value_as_int())
                )

              # Segments per Tendroid
              with ui.HStack():
                ui.Label("Segments:", width=100)
                segments_field = ui.IntDrag(min=8, max=32, step=1)
                segments_field.model.set_value(self.num_segments)
                segments_field.model.add_value_changed_fn(
                  lambda m: setattr(self, 'num_segments', m.get_value_as_int())
                )

          ui.Spacer(height=10)

          # === ACTION BUTTONS ===
          with ui.VStack(spacing=5):
            # Spawn button
            spawn_button = ui.Button(
              "Spawn Tendroids",
              height=30,
              clicked_fn=self._on_spawn_clicked
            )

            # Start/Stop animation
            with ui.HStack(spacing=5):
              start_button = ui.Button(
                "Start Animation",
                clicked_fn=self._on_start_clicked
              )
              stop_button = ui.Button(
                "Stop Animation",
                clicked_fn=self._on_stop_clicked
              )

            # Clear button
            clear_button = ui.Button(
              "Clear All",
              height=30,
              clicked_fn=self._on_clear_clicked,
              style={ "background_color": 0xFF664444 }
            )

          ui.Spacer(height=10)

          # === STATUS ===
          with ui.CollapsableFrame("Status", height=0, collapsed=False):
            with ui.VStack(spacing=5):
              self.status_label = ui.Label(
                "Ready",
                word_wrap=True
              )

              self.count_label = ui.Label(
                "Tendroids: 0",
                word_wrap=True
              )

              self.animation_label = ui.Label(
                "Animation: Stopped",
                word_wrap=True
              )

    carb.log_info("[TendroidControlPanel] Window created")

  def _on_count_changed(self, value: int):
    """Handle spawn count changes - show/hide conditional sections."""
    self.spawn_count = value

    # Show/hide conditional frames
    if self.single_settings_frame:
      self.single_settings_frame.visible = (value == 1)
    if self.multi_settings_frame:
      self.multi_settings_frame.visible = (value > 1)

    self._update_status(f"Spawn count: {value}")

  def _on_spawn_clicked(self):
    """Handle spawn button - single or multi mode."""
    try:
      if self.spawn_count == 1:
        # Single tendroid mode with custom parameters
        self._spawn_single_tendroid()
      else:
        # Multi-tendroid mode with defaults
        self._spawn_multiple_tendroids()

    except Exception as e:
      self._update_status(f"Error: {e}")
      carb.log_error(f"[TendroidControlPanel] Spawn error: {e}")

  def _spawn_single_tendroid(self):
    """Spawn a single tendroid with custom parameters."""
    self._update_status("Spawning single tendroid...")

    radius = self.single_diameter / 2.0

    # Create single tendroid with custom settings
    success = self.scene_manager.create_single_tendroid(
      position=(0, 0, 0),
      radius=radius,
      length=self.single_length,
      bulge_length_percent=self.bulge_size_percent,
      amplitude=self.amplitude,
      wave_speed=self.wave_speed,
      cycle_delay=self.pause_duration
    )

    if success:
      self._update_status(
        f"Created: D={self.single_diameter:.0f}, "
        f"L={self.single_length:.0f}, "
        f"Wave={self.bulge_size_percent:.0f}%, "
        f"Amp={self.amplitude:.2f}"
      )
      self._update_count(1)
    else:
      self._update_status("Failed to spawn tendroid")

  def _spawn_multiple_tendroids(self):
    """Spawn multiple tendroids with default settings."""
    self._update_status(f"Spawning {self.spawn_count} tendroids...")

    success = self.scene_manager.create_tendroids(
      count=self.spawn_count,
      spawn_area=(self.spawn_width, self.spawn_depth),
      num_segments=self.num_segments
    )

    if success:
      count = self.scene_manager.get_tendroid_count()
      self._update_status(f"Spawned {count} tendroids")
      self._update_count(count)
    else:
      self._update_status("Failed to spawn tendroids")

  def _on_start_clicked(self):
    """Handle start animation button."""
    try:
      self.scene_manager.start_animation()
      self._update_animation_status("Running")
      self._update_status("Animation started")
    except Exception as e:
      self._update_status(f"Error: {e}")
      carb.log_error(f"[TendroidControlPanel] Start error: {e}")

  def _on_stop_clicked(self):
    """Handle stop animation button."""
    try:
      self.scene_manager.stop_animation()
      self._update_animation_status("Stopped")
      self._update_status("Animation stopped")
    except Exception as e:
      self._update_status(f"Error: {e}")
      carb.log_error(f"[TendroidControlPanel] Stop error: {e}")

  def _on_clear_clicked(self):
    """Handle clear button."""
    try:
      self.scene_manager.stop_animation()
      self.scene_manager.clear_tendroids()
      self._update_status("Cleared all tendroids")
      self._update_count(0)
      self._update_animation_status("Stopped")
    except Exception as e:
      self._update_status(f"Error: {e}")
      carb.log_error(f"[TendroidControlPanel] Clear error: {e}")

  def _update_status(self, message: str):
    """Update status label."""
    if self.status_label:
      self.status_label.text = message

  def _update_count(self, count: int):
    """Update tendroid count label."""
    if self.count_label:
      self.count_label.text = f"Tendroids: {count}"

  def _update_animation_status(self, status: str):
    """Update animation status label."""
    if self.animation_label:
      self.animation_label.text = f"Animation: {status}"

  def destroy(self):
    """Destroy the window."""
    if self.window:
      self.window.destroy()
      self.window = None

    carb.log_info("[TendroidControlPanel] Window destroyed")
