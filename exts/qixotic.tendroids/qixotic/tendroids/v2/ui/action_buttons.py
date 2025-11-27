"""
Action buttons section for V2 control panel

Handles spawn, clear, start/stop animation operations.
"""

import carb
import omni.ui as ui


class ActionButtons:
    """Action buttons with scene manager integration."""
    
    def __init__(self, scene_manager, spawn_controls, geometry_controls):
        """
        Initialize action buttons.
        
        Args:
            scene_manager: V2SceneManager instance
            spawn_controls: SpawnControls for reading parameters
            geometry_controls: GeometryControls for reading parameters
        """
        self.scene_manager = scene_manager
        self.spawn_controls = spawn_controls
        self.geometry_controls = geometry_controls
        self.status_callback = None  # Callback(str) for status updates
        
    def set_status_callback(self, callback):
        """Set callback for status updates."""
        self.status_callback = callback
    
    def _update_status(self, msg: str):
        """Update status display."""
        if self.status_callback:
            self.status_callback(msg)
        carb.log_info(f"[V2ActionButtons] {msg}")
    
    def build(self, parent: ui.VStack = None):
        """Build action buttons UI."""
        with ui.CollapsableFrame("Actions", height=0, collapsed=False):
            with ui.VStack(spacing=5, style={"background_color": 0xFF23211F}):
                ui.Spacer(height=4)
                # Spawn and Clear row
                with ui.HStack(spacing=5, height=28):
                    ui.Button(
                        "Spawn Tendroids",
                        clicked_fn=self._on_spawn_clicked,
                        tooltip="Create tendroids with current settings"
                    )
                    ui.Button(
                        "Clear All",
                        clicked_fn=self._on_clear_clicked,
                        tooltip="Remove all tendroids from scene",
                        style={"background_color": 0xFF554444}
                    )
                
                # Start and Stop row
                with ui.HStack(spacing=5, height=28):
                    ui.Button(
                        "Start Animation",
                        clicked_fn=self._on_start_clicked,
                        tooltip="Begin wave animation loop"
                    )
                    ui.Button(
                        "Stop Animation",
                        clicked_fn=self._on_stop_clicked,
                        tooltip="Pause animation loop"
                    )
                
                ui.Spacer(height=4)
    
    def _on_spawn_clicked(self):
        """Handle spawn button click."""
        try:
            sp = self.spawn_controls
            
            # Use defaults if no geometry controls
            radial_segs = 24
            height_segs = 48
            if self.geometry_controls:
                radial_segs = self.geometry_controls.radial_segments
                height_segs = self.geometry_controls.height_segments
            
            self._update_status(f"Spawning {sp.count} tendroids...")
            
            success = self.scene_manager.create_tendroids(
                count=sp.count,
                spawn_area=(400, 400),  # Default area
                radius_range=(8.0, 12.0),  # Default radius range
                radial_segments=radial_segs,
                height_segments=height_segs
            )
            
            if success:
                actual = self.scene_manager.get_tendroid_count()
                self._update_status(f"Spawned {actual} tendroids")
            else:
                self._update_status("Spawn failed - check console")
                
        except Exception as e:
            self._update_status(f"Error: {e}")
            carb.log_error(f"[V2ActionButtons] Spawn error: {e}")
    
    def _on_clear_clicked(self):
        """Handle clear button click."""
        try:
            self.scene_manager.stop_animation()
            self.scene_manager.clear_tendroids()
            self._update_status("Cleared all tendroids")
        except Exception as e:
            self._update_status(f"Error: {e}")
    
    def _on_start_clicked(self):
        """Handle start animation button click."""
        try:
            self.scene_manager.start_animation(enable_profiling=True)
            self._update_status("Animation started")
        except Exception as e:
            self._update_status(f"Error: {e}")
    
    def _on_stop_clicked(self):
        """Handle stop animation button click."""
        try:
            self.scene_manager.stop_animation()
            self._update_status("Animation stopped")
        except Exception as e:
            self._update_status(f"Error: {e}")
