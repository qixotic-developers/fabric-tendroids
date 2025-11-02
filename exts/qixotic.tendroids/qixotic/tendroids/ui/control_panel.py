"""
UI control panel for Tendroid management

Provides simple interface to spawn and control Tendroids.
Styled to match Omniverse UI conventions.
"""

import carb
import omni.ui as ui
from ..scene.manager import TendroidSceneManager


class TendroidControlPanel:
    """
    Simple UI panel for Tendroid controls.
    
    Matches Omniverse UI style and provides essential controls for
    spawning and managing Tendroids.
    """

    def __init__(self, scene_manager: TendroidSceneManager):
        """
        Initialize control panel.
        
        Args:
            scene_manager: TendroidSceneManager instance to control
        """
        self.scene_manager = scene_manager
        self.window = None
        
        # UI state
        self.tendroid_count = 1
        self.spawn_width = 200
        self.spawn_depth = 200
        self.num_segments = 16
        
        carb.log_info("[TendroidControlPanel] Initialized")

    def create_window(self):
        """Create the UI window."""
        if self.window:
            return
        
        self.window = ui.Window(
            "Tendroid Controls",
            width=300,
            height=400
        )
        
        with self.window.frame:
            with ui.VStack(spacing=10, height=0):
                # Header
                ui.Label(
                    "Tendroid Manager",
                    alignment=ui.Alignment.CENTER,
                    style={"font_size": 18}
                )
                
                ui.Spacer(height=10)
                
                # Spawn settings
                with ui.CollapsableFrame("Spawn Settings", height=0, collapsed=False):
                    with ui.VStack(spacing=5):
                        # Tendroid count
                        with ui.HStack():
                            ui.Label("Count:", width=100)
                            tendroid_count_field = ui.IntDrag(
                                min=1,
                                max=50,
                                step=1
                            )
                            tendroid_count_field.model.set_value(self.tendroid_count)
                            tendroid_count_field.model.add_value_changed_fn(
                                lambda m: setattr(self, 'tendroid_count', int(m.get_value_as_int()))
                            )
                        
                        # Spawn area width
                        with ui.HStack():
                            ui.Label("Area Width:", width=100)
                            width_field = ui.IntDrag(
                                min=50,
                                max=1000,
                                step=10
                            )
                            width_field.model.set_value(self.spawn_width)
                            width_field.model.add_value_changed_fn(
                                lambda m: setattr(self, 'spawn_width', int(m.get_value_as_int()))
                            )
                        
                        # Spawn area depth
                        with ui.HStack():
                            ui.Label("Area Depth:", width=100)
                            depth_field = ui.IntDrag(
                                min=50,
                                max=1000,
                                step=10
                            )
                            depth_field.model.set_value(self.spawn_depth)
                            depth_field.model.add_value_changed_fn(
                                lambda m: setattr(self, 'spawn_depth', int(m.get_value_as_int()))
                            )
                        
                        # Segments per Tendroid
                        with ui.HStack():
                            ui.Label("Segments:", width=100)
                            segments_field = ui.IntDrag(
                                min=8,
                                max=32,
                                step=1
                            )
                            segments_field.model.set_value(self.num_segments)
                            segments_field.model.add_value_changed_fn(
                                lambda m: setattr(self, 'num_segments', int(m.get_value_as_int()))
                            )
                
                ui.Spacer(height=10)
                
                # Action buttons
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
                
                ui.Spacer(height=10)
                
                # Status display
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

    def _on_spawn_clicked(self):
        """Handle spawn button click."""
        try:
            self._update_status("Spawning Tendroids...")
            
            success = self.scene_manager.create_tendroids(
                count=self.tendroid_count,
                spawn_area=(self.spawn_width, self.spawn_depth),
                num_segments=self.num_segments
            )
            
            if success:
                count = self.scene_manager.get_tendroid_count()
                self._update_status(f"Spawned {count} Tendroids successfully!")
                self._update_count(count)
            else:
                self._update_status("Failed to spawn Tendroids")
                
        except Exception as e:
            self._update_status(f"Error: {e}")
            carb.log_error(f"[TendroidControlPanel] Spawn error: {e}")

    def _on_start_clicked(self):
        """Handle start animation button click."""
        try:
            self.scene_manager.start_animation()
            self._update_animation_status("Running")
            self._update_status("Animation started")
        except Exception as e:
            self._update_status(f"Error: {e}")
            carb.log_error(f"[TendroidControlPanel] Start error: {e}")

    def _on_stop_clicked(self):
        """Handle stop animation button click."""
        try:
            self.scene_manager.stop_animation()
            self._update_animation_status("Stopped")
            self._update_status("Animation stopped")
        except Exception as e:
            self._update_status(f"Error: {e}")
            carb.log_error(f"[TendroidControlPanel] Stop error: {e}")

    def _on_clear_clicked(self):
        """Handle clear button click."""
        try:
            self.scene_manager.stop_animation()
            self.scene_manager.clear_tendroids()
            self._update_status("Cleared all Tendroids")
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
        """Update Tendroid count label."""
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
