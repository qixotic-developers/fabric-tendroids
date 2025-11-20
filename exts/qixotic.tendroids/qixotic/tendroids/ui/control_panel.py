"""
UI control panel for Tendroid management

Coordinates spawn settings, action buttons, wave controls, bubble controls, and status display.
"""

import carb
import omni.ui as ui
from ..scene.manager import TendroidSceneManager
from .spawn_settings_ui import SpawnSettingsUI
from .action_buttons import ActionButtons
from .status_display import StatusDisplay
from .bubble_controls import BubbleControlsBuilder
from .wave_controls import WaveControlsBuilder


class TendroidControlPanel:
  """
  Main control panel coordinator with compact two-column layout.
  
  Delegates UI sections to specialized components:
  - SpawnSettingsUI: Parameter controls with single/multi mode switching
  - ActionButtons: Spawn, start, stop, clear operations
  - BubbleControlsBuilder: Bubble parameters (diameter, pop timing, physics)
  - StatusDisplay: Status labels and updates
  """
  
  def __init__(self, scene_manager: TendroidSceneManager):
    """
    Initialize control panel.
    
    Args:
        scene_manager: TendroidSceneManager instance to control
    """
    self.scene_manager = scene_manager
    self.window = None
    
    # UI components
    self.spawn_settings = SpawnSettingsUI()
    self.action_buttons = ActionButtons(scene_manager)
    self.status_display = StatusDisplay()
    self.bubble_controls = None  # Created after bubble_manager exists
    self.wave_controls = None    # Created after animation_controller exists
    
    # Wire up component references
    self.action_buttons.set_spawn_settings(self.spawn_settings)
    self.action_buttons.set_status_display(self.status_display)
    
    # Register callback for count changes
    self.spawn_settings.on_count_changed_callback = self._on_count_changed
    
    carb.log_info("[TendroidControlPanel] Initialized")
  
  def create_window(self):
    """Create the UI window with compact layout."""
    if self.window:
      return
    
    self.window = ui.Window(
      "Tendroid Controls",
      width=400,
      height=450
    )
    
    with self.window.frame:
      with ui.VStack(spacing=8):
        # Header - fixed height
        with ui.VStack(height=40):
          ui.Spacer(height=5)
          ui.Label(
            "Tendroid Manager",
            alignment=ui.Alignment.CENTER,
            height=30,
            style={"font_size": 18}
          )
        
        ui.Line()
        # ui.Spacer(height=2)
        
        # Spawn settings (compact two-column)
        self.spawn_settings.create_ui(None)
        
        ui.Spacer(height=5)
        ui.Line()
        ui.Spacer(height=5)
        
        # Action buttons
        self.action_buttons.create_ui(None)
        
        ui.Spacer(height=5)
        ui.Line()
        ui.Spacer(height=5)
        
        # Wave controls (if animation controller exists)
        if self.scene_manager.animation_controller:
          if self.scene_manager.animation_controller.wave_controller:
            if not self.wave_controls:
              self.wave_controls = WaveControlsBuilder(
                self.scene_manager.animation_controller.wave_controller
              )
            self.wave_controls.build()
            
            ui.Spacer(height=5)
            ui.Line()
            ui.Spacer(height=5)
        
        # Bubble controls (if bubble manager exists)
        if self.scene_manager.bubble_manager:
          if not self.bubble_controls:
            self.bubble_controls = BubbleControlsBuilder(
              self.scene_manager.bubble_manager
            )
          self.bubble_controls.build()
          
          ui.Spacer(height=5)
          ui.Line()
          ui.Spacer(height=5)
        
        # Status display
        self.status_display.create_ui(None)
    
    carb.log_info("[TendroidControlPanel] Window created")
  
  def _on_count_changed(self, value: int):
    """Handle spawn count changes from settings UI."""
    self.status_display.update_status(f"Spawn count: {value}")
  
  def update(self, dt: float):
    """
    Update control panel per frame.
    
    Args:
        dt: Delta time in seconds
    """
    # Forward update to action buttons (for stress test controller)
    self.action_buttons.update(dt)
  
  def destroy(self):
    """Destroy the window."""
    if self.window:
      self.window.destroy()
      self.window = None
    
    carb.log_info("[TendroidControlPanel] Window destroyed")
