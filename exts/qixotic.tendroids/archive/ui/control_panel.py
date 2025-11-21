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
        self.bubble_controls = None
        self.wave_controls = None
        
        # Dynamic rebuild containers
        self._wave_container = None
        self._bubble_container = None
        
        # Wire up component references
        self.action_buttons.set_spawn_settings(self.spawn_settings)
        self.action_buttons.set_status_display(self.status_display)
        self.action_buttons.set_on_spawn_callback(self._on_tendroids_spawned)
        
        # Register callback for count changes
        self.spawn_settings.on_count_changed_callback = self._on_count_changed
        
        carb.log_info("[TendroidControlPanel] Initialized")
    
    def create_window(self):
        """Create the UI window with compact layout."""
        if self.window:
            return
        
        self.window = ui.Window("Tendroid Controls", width=400, height=500)
        
        with self.window.frame:
            with ui.VStack(spacing=8):
                self._build_header()
                ui.Line()
                self.spawn_settings.create_ui(None)
                ui.Spacer(height=5)
                ui.Line()
                ui.Spacer(height=5)
                self.action_buttons.create_ui(None)
                ui.Spacer(height=5)
                ui.Line()
                ui.Spacer(height=5)
                
                # Container for wave controls (rebuilt dynamically)
                self._wave_container = ui.VStack(spacing=0)
                self._build_wave_controls()
                
                # Container for bubble controls (rebuilt dynamically)
                self._bubble_container = ui.VStack(spacing=0)
                self._build_bubble_controls()
                
                # Status display
                self.status_display.create_ui(None)
        
        carb.log_info("[TendroidControlPanel] Window created")
    
    def _build_header(self):
        """Build panel header."""
        with ui.VStack(height=40):
            ui.Spacer(height=5)
            ui.Label(
                "Tendroid Manager",
                alignment=ui.Alignment.CENTER,
                height=30,
                style={"font_size": 18}
            )
    
    def _build_wave_controls(self):
        """Build wave controls if animation controller exists."""
        if not self._wave_container:
            return
        
        # Clear existing
        self._wave_container.clear()
        
        with self._wave_container:
            if (self.scene_manager.animation_controller and
                self.scene_manager.animation_controller.wave_controller):
                
                if not self.wave_controls:
                    self.wave_controls = WaveControlsBuilder(
                        self.scene_manager.animation_controller.wave_controller
                    )
                self.wave_controls.build()
                ui.Spacer(height=5)
                ui.Line()
                ui.Spacer(height=5)
    
    def _build_bubble_controls(self):
        """Build bubble controls if bubble manager exists."""
        if not self._bubble_container:
            return
        
        # Clear existing
        self._bubble_container.clear()
        
        with self._bubble_container:
            if self.scene_manager.bubble_manager:
                if not self.bubble_controls:
                    self.bubble_controls = BubbleControlsBuilder(
                        self.scene_manager.bubble_manager
                    )
                self.bubble_controls.build()
                ui.Spacer(height=5)
                ui.Line()
                ui.Spacer(height=5)
                carb.log_info("[TendroidControlPanel] Bubble controls built")
            else:
                carb.log_info("[TendroidControlPanel] No bubble_manager yet")
    
    def _on_tendroids_spawned(self):
        """Callback when tendroids are spawned - rebuild dynamic controls."""
        carb.log_info("[TendroidControlPanel] Tendroids spawned - rebuilding controls")
        
        # Reset builders to force recreation with new managers
        self.bubble_controls = None
        self.wave_controls = None
        
        # Rebuild dynamic sections
        self._build_wave_controls()
        self._build_bubble_controls()
    
    def _on_count_changed(self, value: int):
        """Handle spawn count changes from settings UI."""
        self.status_display.update_status(f"Spawn count: {value}")
    
    def update(self, dt: float):
        """Update control panel per frame."""
        self.action_buttons.update(dt)
    
    def destroy(self):
        """Destroy the window."""
        if self.window:
            self.window.destroy()
            self.window = None
        carb.log_info("[TendroidControlPanel] Window destroyed")
