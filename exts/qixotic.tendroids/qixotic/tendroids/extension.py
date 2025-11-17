"""
Tendroids Extension - Main entry point

Omniverse extension for creating and animating Tendroid creatures.
"""

import carb
import omni.ext
import omni.usd
import omni.kit.ui
import omni.kit.window.extensions
from .scene.manager import TendroidSceneManager
from .ui.control_panel import TendroidControlPanel


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
            
            # Filter Extensions panel to show qixotic.tendroids
            self._set_extensions_filter("qixotic tendroids")
            
            carb.log_info("[TendroidsExtension] Startup complete")
            carb.log_info(
                "[TendroidsExtension] Bubble system ready! "
                "Create tendroids and watch them emit bubbles."
            )
            
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Startup failed: {e}")
            import traceback
            traceback.print_exc()

    def _set_extensions_filter(self, filter_text: str):
        """
        Set the Extensions panel search filter.
        
        Args:
            filter_text: Search text to filter extensions
        """
        try:
            # Try to get extension manager window
            ext_window = omni.kit.window.extensions.get_window()
            if ext_window and hasattr(ext_window, 'set_search_text'):
                ext_window.set_search_text(filter_text)
                carb.log_info(
                    f"[TendroidsExtension] Extensions filter set to: '{filter_text}'"
                )
        except Exception as e:
            # Extensions window API may vary by Kit version - not critical
            carb.log_info(
                f"[TendroidsExtension] Extensions filter not available in this Kit version"
            )
            
    def on_shutdown(self):
        """Called when extension is unloaded."""
        carb.log_info("[TendroidsExtension] Shutting down")
        
        try:
            # Clear Extensions panel filter
            self._set_extensions_filter("")
            
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
