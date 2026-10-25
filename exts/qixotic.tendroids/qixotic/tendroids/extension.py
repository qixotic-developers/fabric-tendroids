"""
Tendroids Extension - Main entry point

Omniverse extension for creating and animating Tendroid creatures.
Uses GPU-accelerated system with wave animation.
"""

import carb
import omni.ext
import omni.usd
import omni.kit.ui
import omni.kit.app
import omni.kit.window.extensions
from .scene.manager import V2SceneManager
from .ui.control_panel import V2ControlPanel
from .utils.git_version import get_git_version


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
            # Create scene manager
            self._scene_manager = V2SceneManager()
            
            # Create UI control panel
            ext_manager = omni.kit.app.get_app().get_extension_manager()
            version = get_git_version() or ext_manager.get_extension_dict(ext_id)["package"]["version"]
            self._control_panel = V2ControlPanel(self._scene_manager, version)
            self._control_panel.create_ui()
            
            # Subscribe to update events for UI (stress test controller)
            update_stream = omni.kit.app.get_app().get_update_event_stream()
            self._ui_update_subscription = update_stream.create_subscription_to_pop(
                self._on_ui_update,
                name="TendroidsExtension.UIUpdate"
            )
            
            # Filter Extensions panel to show qixotic.tendroids
            self._set_extensions_filter("qixotic tendroids")
            self._install_author_label("QIXOTIC")

        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Startup failed: {e}")
            import traceback
            traceback.print_exc()
    
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

    def _install_author_label(self, label: str):
        """
        Replace the "COMMUNITY" badge on unverified extensions in the Extensions panel.

        Kit hardcodes the badge text in ExtAuthorGroup.get_ui_name with no setting
        to change it, so the method is wrapped for the lifetime of this extension.
        This affects every unverified extension in the session, not just this one.

        Args:
            label: Badge text to show instead of "COMMUNITY"
        """
        try:
            from omni.kit.window.extensions.common import ExtAuthorGroup
        except ImportError:
            carb.log_warn("[TendroidsExtension] ExtAuthorGroup not found; badge left unchanged")
            return

        original = ExtAuthorGroup.get_ui_name

        def get_ui_name(group):
            if group == ExtAuthorGroup.COMMUNITY_UNVERIFIED:
                return label
            return original(group)

        ExtAuthorGroup.get_ui_name = get_ui_name
        self._restore_author_label = lambda: setattr(ExtAuthorGroup, "get_ui_name", original)

    def on_shutdown(self):
        """Called when extension is unloaded."""
        try:
            if getattr(self, "_restore_author_label", None):
                self._restore_author_label()
                self._restore_author_label = None

            # Unsubscribe from updates
            if hasattr(self, '_ui_update_subscription') and self._ui_update_subscription:
                self._ui_update_subscription.unsubscribe()
                self._ui_update_subscription = None
            
            # Clear Extensions panel filter
            self._set_extensions_filter("")
            
            # Cleanup scene manager (stops animation controller)
            if hasattr(self, '_scene_manager') and self._scene_manager:
                self._scene_manager.shutdown()
                self._scene_manager = None
            
            # Cleanup UI
            if hasattr(self, '_control_panel') and self._control_panel:
                self._control_panel.destroy()
                self._control_panel = None
            
        except Exception as e:
            carb.log_error(f"[TendroidsExtension] Shutdown error: {e}")
            import traceback
            traceback.print_exc()
