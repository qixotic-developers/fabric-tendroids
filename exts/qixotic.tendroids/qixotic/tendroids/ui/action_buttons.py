"""
Action button management for Tendroid control panel

Handles button creation and event handlers for spawn, animation, and clear actions.
"""

import carb
import omni.ui as ui

from ..scene.manager import TendroidSceneManager


class ActionButtons:
  """
  Manages action buttons and their event handlers.

  Coordinates spawn, start/stop animation, clear operations,
  and stress testing with the scene manager and status display.
  """

  def __init__(self, scene_manager: TendroidSceneManager):
    """
    Initialize action buttons.

    Args:
        scene_manager: TendroidSceneManager instance to control
    """
    self.scene_manager = scene_manager

    # References to external components
    self.spawn_settings = None
    self.status_display = None

    # Single tendroid test state
    self._single_test_active = False
    self._test_button = None

    # Stress test state
    self._stress_test_controller = None
    self._stress_test_button = None

  def set_spawn_settings(self, spawn_settings):
    """Set reference to spawn settings UI."""
    self.spawn_settings = spawn_settings

  def set_status_display(self, status_display):
    """Set reference to status display."""
    self.status_display = status_display

  def create_ui(self, parent_stack: ui.VStack):
    """
    Create action button UI elements.

    Args:
        parent_stack: Parent VStack to add buttons to
    """
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

      # Spacer before single tendroid test
      ui.Spacer(height=10)
      ui.Line()
      ui.Spacer(height=5)

      # Single Tendroid Test section
      ui.Label("Single Tendroid Bubble Test", height=20)
      self._test_button = ui.Button(
        "Start Single Test",
        height=30,
        clicked_fn=self._on_single_test_clicked,
        style={ "background_color": 0xFF445566 }
      )

      # Spacer before stress test
      ui.Spacer(height=10)
      ui.Line()
      ui.Spacer(height=5)

      # Stress test button
      ui.Label("Automated Stress Testing", height=20)
      self._stress_test_button = ui.Button(
        "Start Stress Test Suite",
        height=30,
        clicked_fn=self._on_stress_test_clicked,
        style={ "background_color": 0xFF446644 },
        tooltip="Run automated test scenarios: 15-30 Tendroids with/without bubbles"
      )

  def _on_spawn_clicked(self):
    """Handle spawn button - single or multi mode."""
    if not self.spawn_settings or not self.status_display:
      return

    try:
      if self.spawn_settings.spawn_count == 1:
        self._spawn_single_tendroid()
      else:
        self._spawn_multiple_tendroids()
    except Exception as e:
      self.status_display.update_status(f"Error: {e}")
      carb.log_error(f"[ActionButtons] Spawn error: {e}")

  def _spawn_single_tendroid(self):
    """Spawn a single tendroid with custom parameters."""
    settings = self.spawn_settings
    self.status_display.update_status("Spawning single tendroid...")

    # Apply bubble settings
    self._apply_bubble_settings()

    radius = settings.single_diameter / 2.0

    success = self.scene_manager.create_single_tendroid(
      position=(0, 0, 0),
      radius=radius,
      length=settings.single_length,
      bulge_length_percent=settings.bulge_size_percent,
      amplitude=settings.amplitude,
      wave_speed=settings.wave_speed,
      cycle_delay=settings.pause_duration
    )

    if success:
      self.status_display.update_status(
        f"Created: D={settings.single_diameter:.0f}, "
        f"L={settings.single_length:.0f}, "
        f"Wave={settings.bulge_size_percent:.0f}%, "
        f"Amp={settings.amplitude:.2f}"
      )
      self.status_display.update_count(1)
    else:
      self.status_display.update_status("Failed to spawn tendroid")

  def _spawn_multiple_tendroids(self):
    """Spawn multiple tendroids with default settings."""
    settings = self.spawn_settings
    count = settings.spawn_count

    self.status_display.update_status(f"Spawning {count} tendroids...")

    # Apply bubble settings
    self._apply_bubble_settings()

    success = self.scene_manager.create_tendroids(
      count=count,
      spawn_area=(settings.spawn_width, settings.spawn_depth),
      num_segments=settings.num_segments
    )

    if success:
      actual_count = self.scene_manager.get_tendroid_count()
      self.status_display.update_status(f"Spawned {actual_count} tendroids")
      self.status_display.update_count(actual_count)
    else:
      self.status_display.update_status("Failed to spawn tendroids")
  
  def _apply_bubble_settings(self):
    """Apply bubble pop timing settings from UI to scene manager."""
    if not self.spawn_settings:
      return
    
    self.scene_manager.update_bubble_pop_timing(
      self.spawn_settings.min_pop_time,
      self.spawn_settings.max_pop_time
    )


  def _on_start_clicked(self):
    """Handle start animation button."""
    if not self.status_display:
      return

    try:
      self.scene_manager.start_animation()
      self.status_display.update_animation_status("Running")
      self.status_display.update_status("Animation started")
    except Exception as e:
      self.status_display.update_status(f"Error: {e}")
      carb.log_error(f"[ActionButtons] Start error: {e}")

  def _on_stop_clicked(self):
    """Handle stop animation button."""
    if not self.status_display:
      return

    try:
      self.scene_manager.stop_animation()
      self.status_display.update_animation_status("Stopped")
      self.status_display.update_status("Animation stopped")
    except Exception as e:
      self.status_display.update_status(f"Error: {e}")
      carb.log_error(f"[ActionButtons] Stop error: {e}")

  def _on_clear_clicked(self):
    """Handle clear button."""
    if not self.status_display:
      return

    try:
      self.scene_manager.stop_animation()
      self.scene_manager.clear_tendroids()
      self.status_display.update_status("Cleared all tendroids")
      self.status_display.update_count(0)
      self.status_display.update_animation_status("Stopped")

      # Reset single test state
      if self._test_button:
        self._single_test_active = False
        self._test_button.text = "Start Single Test"
    except Exception as e:
      self.status_display.update_status(f"Error: {e}")
      carb.log_error(f"[ActionButtons] Clear error: {e}")

  def _on_single_test_clicked(self):
    """Handle single tendroid bubble test button - toggle start/stop."""
    if not self.status_display:
      return

    try:
      if self._single_test_active:
        # Stop the test
        self.scene_manager.stop_animation()
        self.scene_manager.clear_tendroids()
        self._single_test_active = False
        self._test_button.text = "Start Single Test"
        self.status_display.update_status("Single test stopped")
        self.status_display.update_count(0)
        self.status_display.update_animation_status("Stopped")
      else:
        # Start the test
        self.status_display.update_status("Starting single tendroid bubble test...")

        # Create single tendroid at center
        success = self.scene_manager.create_single_tendroid(
          position=(0, 0, 0),
          radius=10.0,
          length=100.0,
          bulge_length_percent=40.0,
          amplitude=0.35,
          wave_speed=40.0,
          cycle_delay=2.0
        )

        if success:
          # Start animation
          self.scene_manager.start_animation()
          self._single_test_active = True
          self._test_button.text = "Stop Single Test"
          self.status_display.update_status(
            "Single tendroid test running - watch for bubbles!"
          )
          self.status_display.update_count(1)
          self.status_display.update_animation_status("Running")
        else:
          self.status_display.update_status("Failed to create test tendroid")

    except Exception as e:
      self.status_display.update_status(f"Error: {e}")
      carb.log_error(f"[ActionButtons] Single test error: {e}")
      self._single_test_active = False
      if self._test_button:
        self._test_button.text = "Start Single Test"

  def _on_stress_test_clicked(self):
    """Handle stress test button - start/stop automated test suite."""
    if not self.status_display:
      return

    try:
      # Toggle stress test on/off
      if self._stress_test_controller and self._stress_test_controller.is_running():
        # Stop the test
        self._stress_test_controller = None
        self._stress_test_button.text = "Start Stress Test Suite"
        self.status_display.update_status("Stress test stopped")
      else:
        # Start the test
        from ..stress_test_controller import StressTestController
        import omni.usd

        ctx = omni.usd.get_context()
        stage = ctx.get_stage() if ctx else None

        if not stage:
          self.status_display.update_status("Error: No stage available")
          return

        self._stress_test_controller = StressTestController(
          stage,
          self.scene_manager
        )

        if self._stress_test_controller.start_test_suite():
          self._stress_test_button.text = "Stop Stress Test"
          self.status_display.update_status("Stress test running - check console for results")
        else:
          self._stress_test_controller = None
          self.status_display.update_status("Failed to start stress test")

    except Exception as e:
      self.status_display.update_status(f"Stress test error: {e}")
      carb.log_error(f"[ActionButtons] Stress test error: {e}")
      import traceback
      traceback.print_exc()
      self._stress_test_controller = None
      if self._stress_test_button:
        self._stress_test_button.text = "Start Stress Test Suite"

  def update(self, dt: float):
    """
    Update per frame - handles stress test progression.

    Args:
        dt: Delta time in seconds
    """
    # Update stress test if running
    if self._stress_test_controller and self._stress_test_controller.is_running():
      if not self._stress_test_controller.update(dt):
        # Test suite complete
        self._stress_test_controller = None
        if self._stress_test_button:
          self._stress_test_button.text = "Start Stress Test Suite"
        if self.status_display:
          self.status_display.update_status("Stress test complete - see console")
      else:
        # Update progress in status
        if self.status_display:
          progress = self._stress_test_controller.get_current_progress()
          self.status_display.update_status(progress)
