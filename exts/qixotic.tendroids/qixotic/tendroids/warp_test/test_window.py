"""
Performance Test Window

Simple UI for running C++ accelerated batch tests.
Achieved ~50 fps with 15 Tendroids using C++ + Fabric hybrid approach.
"""

import carb
import omni.ui as ui

from .cpp_batch_test_controller import CppBatchTestController


class WarpTestWindow(ui.Window):
    """UI window for performance testing"""

    def __init__(self, title: str = "Performance Tests", width: int = 400, height: int = 300):
        super().__init__(title, width=width, height=height)

        self.controller = None
        self.frame_label = None
        self.status_label = None

        self._build_ui()

    def _build_ui(self):
        """Construct the UI layout"""
        with self.frame:
            with ui.VStack(spacing=10, height=0):
                # Header
                ui.Label(
                    "Tendroid Performance Tests",
                    alignment=ui.Alignment.CENTER,
                    style={"font_size": 18}
                )

                ui.Spacer(height=10)

                # Status display
                with ui.CollapsableFrame("Status", height=0):
                    with ui.VStack(spacing=5):
                        self.status_label = ui.Label("Ready")
                        self.frame_label = ui.Label("Frame: 0")

                ui.Spacer(height=10)

                # C++ Batch Test
                with ui.CollapsableFrame("🚀 C++ Accelerated Test", height=0, collapsed=False):
                    with ui.VStack(spacing=8):
                        ui.Label(
                            "Batch 15 Tendroids - C++ + Fabric Hybrid",
                            word_wrap=True,
                            style={"color": 0xFF00FF00}
                        )
                        ui.Label(
                            "Performance: ~50 fps (production ready)",
                            word_wrap=True,
                            style={"color": 0xFF00AAFF}
                        )
                        ui.Spacer(height=5)
                        
                        with ui.HStack(spacing=5):
                            ui.Button("Run Test", clicked_fn=self._start_test, width=100)
                            ui.Button("Stop", clicked_fn=self._stop_test, width=100)

                ui.Spacer(height=10)

                # Info
                with ui.CollapsableFrame("ℹ️  Info", height=0, collapsed=True):
                    with ui.VStack(spacing=5):
                        ui.Label("Architecture:", style={"font_size": 14})
                        ui.Label("• C++ vertex computation (0.015ms)", word_wrap=True)
                        ui.Label("• Fabric USD updates (fast path)", word_wrap=True)
                        ui.Label("• 15 tubes, 204 verts each", word_wrap=True)
                        ui.Label("• Zero-copy numpy arrays", word_wrap=True)

    def _start_test(self):
        """Start C++ batch test"""
        if self.controller and self.controller.running:
            carb.log_warn("[TestWindow] Test already running")
            return

        try:
            carb.log_info("[TestWindow] Starting C++ Batch test")
            self.controller = CppBatchTestController()
            self.controller.start_test()
            self.status_label.text = "Running C++ Batch Test"
            carb.log_info("[TestWindow] Test started")

        except Exception as e:
            carb.log_error(f"[TestWindow] Failed to start test: {e}")
            self.status_label.text = f"Error: {str(e)}"
            import traceback
            traceback.print_exc()

    def _stop_test(self):
        """Stop test"""
        if self.controller and self.controller.running:
            self.controller.stop_test()
            self.status_label.text = "Stopped"
            carb.log_info("[TestWindow] Test stopped")

    def destroy(self):
        """Cleanup on window close"""
        if self.controller and self.controller.running:
            self.controller.stop_test()
        super().destroy()
