"""
UI control panel for Tendroid management

Coordinates spawn settings, action buttons, and status display.
"""

import carb
import omni.ui as ui
from ..scene.manager import TendroidSceneManager
from .spawn_settings_ui import SpawnSettingsUI
from .action_buttons import ActionButtons
from .status_display import StatusDisplay


class TendroidControlPanel:
  """
  Main control panel coordinator.
  
  Delegates UI sections to specialized components:
  - SpawnSettingsUI: Parameter controls with single/multi mode switching
  - ActionButtons: Spawn, start, stop, clear operations
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
    
    # Wire up component references
    self.action_buttons.set_spawn_settings(self.spawn_settings)
    self.action_buttons.set_status_display(self.status_display)
    
    # Register callback for count changes
    self.spawn_settings.on_count_changed_callback = self._on_count_changed
    
    carb.log_info("[TendroidControlPanel] Initialized")
  
  def create_window(self):
    """Create the UI window with all components."""
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
            style={"font_size": 18}
          )
          
          ui.Spacer(height=5)
          
          # Spawn settings
          self.spawn_settings.create_ui(None)
          
          ui.Spacer(height=10)
          
          # Action buttons
          self.action_buttons.create_ui(None)
          
          ui.Spacer(height=10)
          
          # Status display
          self.status_display.create_ui(None)
    
    carb.log_info("[TendroidControlPanel] Window created")
  
  def _on_count_changed(self, value: int):
    """Handle spawn count changes from settings UI."""
    self.status_display.update_status(f"Spawn count: {value}")
  
  def destroy(self):
    """Destroy the window."""
    if self.window:
      self.window.destroy()
      self.window = None
    
    carb.log_info("[TendroidControlPanel] Window destroyed")
