"""
Warp Test Window

Minimal UI for controlling test execution and viewing diagnostics.
"""

import omni.ui as ui
import omni.kit.app
import carb

from .test_controller import WarpTestController
from .test_scenarios import TestPhase


class WarpTestWindow(ui.Window):
    """UI window for Warp test harness"""
    
    def __init__(self, title: str, width: int = 400, height: int = 650):
        super().__init__(title, width=width, height=height)
        
        self.controller = WarpTestController()
        
        self.frame_label = None
        self.memory_label = None
        self.status_label = None
        self._ui_subscription = None
        
        self._build_ui()
        
    def _build_ui(self):
        """Construct the UI layout"""
        with self.frame:
            with ui.VStack(spacing=10, height=0):
                # Header
                ui.Label(
                    "Warp Memory Test Harness",
                    alignment=ui.Alignment.CENTER,
                    style={"font_size": 18}
                )
                
                ui.Spacer(height=10)
                
                # Status display
                with ui.CollapsableFrame("Status", height=0):
                    with ui.VStack(spacing=5):
                        self.status_label = ui.Label("Ready")
                        self.frame_label = ui.Label("Frame: 0")
                        self.memory_label = ui.Label("Memory: -- MB")
                        
                ui.Spacer(height=10)
                
                # Test phase buttons
                with ui.CollapsableFrame("Test Phases", height=0, collapsed=False):
                    with ui.VStack(spacing=8):
                        ui.Label("Phase 1: Baseline ✅", style={"font_size": 14})
                        ui.Label("Single cylinder, sine wave deformation", word_wrap=True)
                        ui.Button("Run Phase 1", clicked_fn=lambda: self._start_test(TestPhase.PHASE_1))
                        
                        ui.Spacer(height=5)
                        
                        ui.Label("Phase 2: Scale Up ✅", style={"font_size": 14})
                        ui.Label("5 cylinders, radial pulse", word_wrap=True)
                        ui.Button("Run Phase 2", clicked_fn=lambda: self._start_test(TestPhase.PHASE_2))
                        
                        ui.Spacer(height=5)
                        
                        ui.Label("Phase 3: Production-Like ✅", style={"font_size": 14})
                        ui.Label("10 cylinders, breathing wave, opaque materials", word_wrap=True)
                        ui.Button("Run Phase 3", clicked_fn=lambda: self._start_test(TestPhase.PHASE_3))
                        
                        ui.Spacer(height=10)
                        ui.Line()
                        ui.Spacer(height=5)
                        
                        ui.Label("Phase 6a: Static Glass ✅", style={"font_size": 14, "color": 0xFF00FF00})
                        ui.Label("Double-wall + glass, NO deformation. PASSED!", word_wrap=True)
                        ui.Button("Run Phase 6a", clicked_fn=lambda: self._start_test(TestPhase.PHASE_6A))
                        
                        ui.Spacer(height=5)
                        
                        ui.Label("Phase 6b: Thick-Wall Dynamic 🔬", style={"font_size": 14, "color": 0xFF00AAFF})
                        ui.Label("60% wall thickness + deformation. Tests edge hypothesis.", word_wrap=True)
                        ui.Button("Run Phase 6b", clicked_fn=lambda: self._start_test(TestPhase.PHASE_6B))
                        
                        ui.Spacer(height=5)
                        
                        ui.Label("Phase 6c-static: Swept Torus - STATIC ⭐", style={"font_size": 14, "color": 0xFF00FF00})
                        ui.Label("Proper manifold tube with glass, NO deformation. Validate geometry.", word_wrap=True)
                        ui.Button("Run Phase 6c-static", clicked_fn=lambda: self._start_test(TestPhase.PHASE_6C_STATIC))
                        
                        ui.Spacer(height=5)
                        
                        ui.Label("Phase 6c: Swept Torus - DYNAMIC ⭐", style={"font_size": 14, "color": 0xFFFFAA00})
                        ui.Label("Proper manifold tube WITH deformation. The final test.", word_wrap=True)
                        ui.Button("Run Phase 6c", clicked_fn=lambda: self._start_test(TestPhase.PHASE_6C))
                        
                ui.Spacer(height=10)
                
                # Control buttons
                with ui.HStack(spacing=10):
                    ui.Button("Stop Test", clicked_fn=self._stop_test)
                    ui.Button("Export Results", clicked_fn=self._export_results)
                    
                ui.Spacer(height=10)
                
                # Info panel
                with ui.CollapsableFrame("Test Info", height=0, collapsed=True):
                    with ui.VStack(spacing=5):
                        ui.Label(
                            "This harness systematically isolates the crash cause.",
                            word_wrap=True
                        )
                        ui.Label("Memory samples taken every 10 frames.", word_wrap=True)
                        ui.Spacer(height=5)
                        ui.Label("Results so far:", style={"font_size": 14})
                        ui.Label("✅ Phase 6a: Static glass works perfectly", word_wrap=True, style={"color": 0xFF00FF00})
                        ui.Label("→ Geometry itself is VALID", word_wrap=True)
                        ui.Label("→ Problem is dynamic updates", word_wrap=True)
                        ui.Spacer(height=5)
                        ui.Label("Phase 6b tests:", style={"font_size": 14})
                        ui.Label("If thicker walls fix it → edge-case geometry", word_wrap=True)
                        ui.Label("If it still crashes → BVH/acceleration structure issue", word_wrap=True)
                        
        # Start update loop for UI refresh
        self._setup_update()
        
    def _start_test(self, phase: TestPhase):
        """Start test for selected phase"""
        try:
            self.controller.start_test(phase)
            self.status_label.text = f"Running Phase {phase.value}"
            carb.log_info(f"Started test phase {phase.value}")
        except Exception as e:
            carb.log_error(f"Failed to start test: {e}")
            self.status_label.text = f"Error: {str(e)}"
            import traceback
            traceback.print_exc()
            
    def _stop_test(self):
        """Stop current test"""
        summary = self.controller.stop_test()
        self.status_label.text = "Stopped"
        if summary:
            carb.log_info(f"Test summary: {summary}")
            
    def _export_results(self):
        """Export test results to file"""
        from . import MEMORY_LOG_PATH
        try:
            self.controller.memory_monitor.export_to_json(MEMORY_LOG_PATH)
            carb.log_info(f"Results exported to {MEMORY_LOG_PATH}")
            self.status_label.text = "Results exported"
        except Exception as e:
            carb.log_error(f"Export failed: {e}")
            self.status_label.text = f"Export failed: {str(e)}"
            
    def _setup_update(self):
        """Setup UI update loop using Kit app update stream"""
        app = omni.kit.app.get_app()
        update_stream = app.get_update_event_stream()
        self._ui_subscription = update_stream.create_subscription_to_pop(
            self._on_ui_update, name="warp_test_ui_update"
        )
        
    def _on_ui_update(self, event):
        """Update UI with current test state"""
        if not self.controller.running:
            return
            
        self.frame_label.text = f"Frame: {self.controller.current_frame}"
        
        # Update memory display
        if self.controller.memory_monitor.samples:
            latest = self.controller.memory_monitor.samples[-1]
            self.memory_label.text = f"Memory: {latest.python_mb:.1f} MB (Δ {latest.delta_python_mb:+.2f})"
            
    def destroy(self):
        """Cleanup on window close"""
        if self._ui_subscription:
            self._ui_subscription.unsubscribe()
            self._ui_subscription = None
        if self.controller.running:
            self.controller.stop_test()
        super().destroy()
