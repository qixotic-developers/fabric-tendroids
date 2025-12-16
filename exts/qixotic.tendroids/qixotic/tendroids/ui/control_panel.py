"""
V2 Control Panel - Main coordinator for tendroid UI

Integrated as tab with Stage and Render Settings.
"""

import carb
import omni.ui as ui
from omni.kit.window.property.templates import HORIZONTAL_SPACING

from ..scene.manager import V2SceneManager
from .spawn_controls import SpawnControls
from .wave_controls import WaveControls
from .bubble_controls import BubbleControls
from .creature_controls import CreatureControls
from .debug_controls import DebugControls
from .action_buttons import ActionButtons


class V2ControlPanel:
    """
    Main control panel for V2 tendroid system.
    
    Creates a window that tabs with Stage and Render Settings.
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
        self.wave_controls = WaveControls()
        self.bubble_controls = BubbleControls()
        self.creature_controls = CreatureControls()
        self.debug_controls = DebugControls(self.scene_manager)
        self.action_buttons = ActionButtons(
            self.scene_manager,
            self.spawn_controls,
            self.creature_controls
        )
        
        carb.log_info("[V2ControlPanel] Initialized")
    
    def create_ui(self):
        """Create the UI window as tab with Stage/Render Settings."""
        if self.window:
            return
        
        # Create window docked to same area as Stage window
        # Using None as dockIn target makes it auto-group with Stage
        self.window = ui.Window(
            "Tendroid Controls",  # Keep original name for workspace restore
            width=350,
            height=600,
            # Dock in the upper right panel where Stage/Render Settings are
            dockPreference=ui.DockPreference.RIGHT_TOP,
            # Auto-hide when not in use
            auto_resize=False
        )
        
        # Make visible and focused by default
        self.window.visible = True
        self.window.flags = ui.WINDOW_FLAGS_NO_SCROLLBAR
        
        with self.window.frame:
            # Create scrollable content with dark background
            with ui.ScrollingFrame(
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_AS_NEEDED,
                style_type_name_override="ScrollingFrame",
                style={
                    "background_color": 0xFF23211F,
                    "secondary_color": 0xFF23211F,
                }
            ):
                with ui.VStack(spacing=6, style={"background_color": 0xFF23211F}):
                    ui.Spacer(height=4)
                    
                    # Spawn settings
                    self.spawn_controls.build()
                    
                    # Creature settings
                    self.creature_controls.build()
                    
                    # Wave motion
                    self._bind_wave_controller()
                    self.wave_controls.build()
                    
                    # Bubble settings
                    self._bind_bubble_manager()
                    self.bubble_controls.build()
                    
                    # Debug visualization
                    self.debug_controls.build()
                    
                    # Action buttons
                    self.action_buttons.build()
                    
                    # Bottom spacer for scrolling clearance
                    ui.Spacer(height=20)
        
        # Try to dock with Stage window specifically
        self._dock_with_stage()
        
        carb.log_info("[V2ControlPanel] Window created and docked with Stage")
    
    def _dock_with_stage(self):
        """Try to dock with the Stage window specifically."""
        try:
            # Get Stage window
            stage_window = ui.Workspace.get_window("Stage")
            if stage_window and self.window:
                # Dock our window with Stage window
                self.window.dock_in(stage_window, ui.DockPosition.SAME)
                # Make our window the active tab
                self.window.focus()
                carb.log_info("[V2ControlPanel] Docked with Stage window")
        except Exception as e:
            carb.log_warn(f"[V2ControlPanel] Could not dock with Stage: {e}")
    
    def _bind_wave_controller(self):
        """Bind wave controls to scene manager's wave controller."""
        if self.scene_manager.animation_controller:
            wc = self.scene_manager.animation_controller.wave_controller
            self.wave_controls.set_wave_controller(wc)
    
    def _bind_bubble_manager(self):
        """Bind bubble controls to scene manager's bubble manager."""
        if self.scene_manager.bubble_manager:
            self.bubble_controls.set_bubble_manager(self.scene_manager.bubble_manager)
    
    def update(self, dt: float):
        """Per-frame update."""
        # Rebind if needed after spawning
        if self.scene_manager.animation_controller:
            if not self.wave_controls.wave_controller:
                self._bind_wave_controller()
        
        if self.scene_manager.bubble_manager:
            if not self.bubble_controls.bubble_manager:
                self._bind_bubble_manager()
    
    def destroy(self):
        """Destroy the window."""
        if self.window:
            self.window.visible = False
            self.window.destroy()
            self.window = None
        carb.log_info("[V2ControlPanel] Window destroyed")
