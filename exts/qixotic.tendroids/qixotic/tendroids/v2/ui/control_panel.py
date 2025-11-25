"""
V2 Control Panel - Main coordinator for tendroid UI

Compact panel with slider-based controls and no header.
"""

import carb
import omni.ui as ui

from ..scene.manager import V2SceneManager
from .spawn_controls import SpawnControls
from .geometry_controls import GeometryControls
from .wave_controls import WaveControls
from .bubble_controls import BubbleControls
from .action_buttons import ActionButtons
from .status_display import StatusDisplay


class V2ControlPanel:
    """
    Main control panel for V2 tendroid system.
    
    Coordinates spawn, geometry, wave, and action controls.
    """
    
    def __init__(self, scene_manager: V2SceneManager = None):
        """
        Initialize control panel.
        
        Args:
            scene_manager: V2SceneManager instance (created if None)
        """
        self.scene_manager = scene_manager or V2SceneManager()
        self.window = None
        
        # UI sections
        self.spawn_controls = SpawnControls()
        self.geometry_controls = GeometryControls()
        self.wave_controls = WaveControls()
        self.bubble_controls = BubbleControls()
        self.action_buttons = ActionButtons(
            self.scene_manager,
            self.spawn_controls,
            self.geometry_controls
        )
        self.status_display = StatusDisplay()
        
        # Wire callbacks
        self.action_buttons.set_status_callback(self._on_status_update)
        
        carb.log_info("[V2ControlPanel] Initialized")
    
    def create_window(self):
        """Create the UI window."""
        if self.window:
            return
        
        self.window = ui.Window("Tendroid Controls", width=340, height=520)
        
        with self.window.frame:
            with ui.VStack(spacing=4):
                # Spawn settings
                self.spawn_controls.build()
                
                # Geometry settings (collapsed by default)
                self.geometry_controls.build()
                
                # Wave motion
                self._bind_wave_controller()
                self.wave_controls.build()
                
                # Bubble settings
                self._bind_bubble_manager()
                self.bubble_controls.build()
                
                # Action buttons
                self.action_buttons.build()
                
                # Status display
                self.status_display.build()
        
        carb.log_info("[V2ControlPanel] Window created")
    
    def _bind_wave_controller(self):
        """Bind wave controls to scene manager's wave controller."""
        if self.scene_manager.animation_controller:
            wc = self.scene_manager.animation_controller.wave_controller
            self.wave_controls.set_wave_controller(wc)
    
    def _bind_bubble_manager(self):
        """Bind bubble controls to scene manager's bubble manager."""
        if self.scene_manager.bubble_manager:
            self.bubble_controls.set_bubble_manager(self.scene_manager.bubble_manager)
    
    def _on_status_update(self, message: str):
        """Handle status updates from action buttons."""
        self.status_display.update_status(message)
        
        # Update count
        count = self.scene_manager.get_tendroid_count()
        self.status_display.update_count(count)
        
        # Update animation state
        running = self.scene_manager.animation_controller.is_running
        self.status_display.update_animation_state(running)
        
        # Rebind wave controller if needed
        self._bind_wave_controller()
        
        # Rebind bubble manager if needed
        self._bind_bubble_manager()
    
    def update(self, dt: float):
        """Per-frame update (for future profiling display)."""
        pass
    
    def destroy(self):
        """Destroy the window."""
        if self.window:
            self.window.destroy()
            self.window = None
        carb.log_info("[V2ControlPanel] Window destroyed")
