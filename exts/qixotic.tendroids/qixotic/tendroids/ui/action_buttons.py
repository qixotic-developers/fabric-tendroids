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
        style={"background_color": 0xFF664444}
      )
      
      # Spacer before stress test
      ui.Spacer(height=10)
      ui.Line()
      ui.Spacer(height=5)
      
      # Stress test button
      stress_test_button = ui.Button(
        "Run Stress Test (15-30 Tendroids)",
        height=30,
        clicked_fn=self._on_stress_test_clicked,
        style={"background_color": 0xFF446644},
        tooltip="Automated performance test: spawns 15, 20, 25, 30 Tendroids and measures FPS"
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
    except Exception as e:
      self.status_display.update_status(f"Error: {e}")
      carb.log_error(f"[ActionButtons] Clear error: {e}")
  
  def _on_stress_test_clicked(self):
    """Handle stress test button - run automated performance test."""
    if not self.status_display:
      return
    
    try:
      from ..test_stress_phase2 import run_stress_test
      
      self.status_display.update_status("Starting stress test...")
      carb.log_info("[ActionButtons] Starting Phase 2 stress test")
      
      # Run stress test in background
      # Note: This will block UI - in production we'd use async/threading
      results = run_stress_test()
      
      # Show summary in status
      if results.test_runs:
        final_run = results.test_runs[-1]
        self.status_display.update_status(
          f"Stress test complete: {final_run['actual_count']} @ {final_run['avg_fps']:.1f} fps"
        )
      else:
        self.status_display.update_status("Stress test failed")
      
    except Exception as e:
      self.status_display.update_status(f"Stress test error: {e}")
      carb.log_error(f"[ActionButtons] Stress test error: {e}")
      import traceback
      traceback.print_exc()
