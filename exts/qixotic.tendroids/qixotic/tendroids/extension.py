"""
Tendroids Extension - Main entry point

Omniverse extension for creating and animating Tendroid creatures.
"""

import carb
import omni.ext
import omni.usd
import omni.kit.ui
from .scene.manager import TendroidSceneManager
from .ui.control_panel import TendroidControlPanel
from .warp_test.test_window import WarpTestWindow


class TendroidsExtension(omni.ext.IExt):
    """
    Tendroids Extension for Omniverse.
    
    Provides tools for creating and animating interactive cylinder-based
    wormlike sea creatures using Fabric/USDRT for optimal performance.
    """

    def on_startup(self, ext_id):
        """
        Called when extension is loaded.
        
        Args:
            ext_id: Extension ID
        """
        carb.log_info("[TendroidsExtension] Starting up")
        
        try:
            # Create scene manager
            self._scene_manager = TendroidSceneManager()
            
            # Create UI control panel
            self._control_panel = TendroidControlPanel(self._scene_manager)
            self._control_panel.create_window()
            
            # Create Warp test window (initially hidden, gets stage dynamically)
            self._warp_test_window = WarpTestWindow("Warp Memory Test")
            self._warp_test_window.visible = False  # Hidden by default
            
            # Add menu item to show Warp Test window
            self._menu_items = [
                omni.kit.ui.get_editor_menu().add_item(
                    "Window/Tendroid Warp Test",
                    self._toggle_warp_test_window,
                    toggle=True,
                    value=False
                )
            ]
            
            carb.log_info("[TendroidsExtension] Startup complete")
            carb.log_info("[TendroidsExtension] Access 'Window > Tendroid Warp Test' to open test harness")
            
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Startup failed: {e}")
            import traceback
            traceback.print_exc()

    def _toggle_warp_test_window(self, menu_path: str, toggled: bool):
        """Toggle visibility of Warp Test window"""
        if self._warp_test_window:
            self._warp_test_window.visible = toggled
            
    def on_shutdown(self):
        """Called when extension is unloaded."""
        carb.log_info("[TendroidsExtension] Shutting down")
        
        try:
            # Remove menu items
            if hasattr(self, '_menu_items'):
                for item in self._menu_items:
                    omni.kit.ui.get_editor_menu().remove_item(item)
                self._menu_items = None
            
            # Cleanup Warp test window
            if hasattr(self, '_warp_test_window'):
                self._warp_test_window.destroy()
                self._warp_test_window = None
            
            # Cleanup scene manager
            if hasattr(self, '_scene_manager'):
                self._scene_manager.shutdown()
                self._scene_manager = None
            
            # Cleanup UI
            if hasattr(self, '_control_panel'):
                self._control_panel.destroy()
                self._control_panel = None
            
            carb.log_info("[TendroidsExtension] Shutdown complete")
            
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Shutdown error: {e}")
            import traceback
            traceback.print_exc()
