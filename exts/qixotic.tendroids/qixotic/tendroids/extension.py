"""
Tendroids Extension - Main entry point

Omniverse extension for creating and animating Tendroid creatures.
"""

import carb
import carb.settings
import omni.ext
import omni.usd
import omni.kit.ui
import omni.kit.app
import omni.kit.window.extensions
from .v1.scene.manager import TendroidSceneManager
from .v1.ui.control_panel import TendroidControlPanel


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
        try:
            # Suppress noisy USD Runtime plugin logging
            self._suppress_usdrt_logging()
            
            # Create scene manager
            self._scene_manager = TendroidSceneManager()
            
            # Create UI control panel
            self._control_panel = TendroidControlPanel(self._scene_manager)
            self._control_panel.create_window()
            
            # Subscribe to update events for UI (stress test controller)
            update_stream = omni.kit.app.get_app().get_update_event_stream()
            self._ui_update_subscription = update_stream.create_subscription_to_pop(
                self._on_ui_update,
                name="TendroidsExtension.UIUpdate"
            )
            
            # Filter Extensions panel to show qixotic.tendroids
            self._set_extensions_filter("qixotic tendroids")
            
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Startup failed: {e}")
            import traceback
            traceback.print_exc()
    
    def _suppress_usdrt_logging(self):
        """
        Suppress noisy USDRT plugin info messages.
        
        Sets log level to WARN (2) for usdrt.population.plugin to hide
        repetitive FabricPopulation and primvar messages during animation.
        
        Log levels: 0=VERBOSE, 1=INFO, 2=WARN, 3=ERROR, 4=FATAL
        """
        try:
            settings = carb.settings.get_settings()
            # Suppress usdrt.population.plugin info messages (use integer 2 for WARN)
            settings.set("/log/channels/usdrt.population.plugin/level", 2)
        except Exception as e:
            # Not critical if this fails
            pass
    
    def _on_ui_update(self, event):
        """
        Update handler for UI components (stress test controller).
        
        Args:
            event: Update event
        """
        try:
            dt = event.payload.get("dt", 0.0)
            self._control_panel.update(dt)
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] UI update error: {e}")

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
        except Exception:
            # Extensions window API may vary by Kit version - not critical
            pass
            
    def on_shutdown(self):
        """Called when extension is unloaded."""
        try:
            # Unsubscribe from updates
            if hasattr(self, '_ui_update_subscription'):
                self._ui_update_subscription = None
            
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
            
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Shutdown error: {e}")
            import traceback
            traceback.print_exc()
