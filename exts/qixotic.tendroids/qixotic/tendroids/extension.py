"""
Tendroids Extension - Main entry point

Omniverse extension for creating and animating Tendroid creatures.
"""

import carb
import omni.ext
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
            
            carb.log_info("[TendroidsExtension] Startup complete")
            
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Startup failed: {e}")
            import traceback
            traceback.print_exc()

    def on_shutdown(self):
        """Called when extension is unloaded."""
        carb.log_info("[TendroidsExtension] Shutting down")
        
        try:
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
