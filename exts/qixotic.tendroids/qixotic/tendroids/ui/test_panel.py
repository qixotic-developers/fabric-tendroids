"""
Test Panel - UI for automated creature-tendroid interaction tests

Provides test selection, duration control, and setup/execute/reset cycle.
"""

import math
import omni.ui as ui

from ..testing import TestController, get_all_test_ids, get_all_test_names, ALL_TESTS


# Log directory relative to extension
import os
_EXT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOG_DIR = os.path.join(_EXT_ROOT, "logs", "test_runs")


class TestState:
    """Test execution states."""
    IDLE = "idle"           # Ready to select/setup test
    SETUP = "setup"         # Creature positioned at start, ready to run
    RUNNING = "running"     # Test animation in progress
    COMPLETE = "complete"   # Test finished, ready to reset


class TestPanel:
    """UI panel for running automated interaction tests."""
    
    def __init__(self):
        """Initialize test panel."""
        self._controller = TestController(log_dir=_LOG_DIR)
        self._state = TestState.IDLE
        
        # UI elements
        self._test_dropdown = None
        self._duration_slider = None
        self._duration_label = None
        self._setup_button = None
        self._run_button = None
        self._reset_button = None
        self._status_label = None
        self._description_label = None
        
        # Current settings
        self._selected_test_index = 0
        self._duration = 5.0
        
        # Set up callbacks
        self._controller.set_on_status_change(self._on_status_change)
        self._controller.set_on_test_complete(self._on_test_complete)
    
    @property
    def controller(self) -> TestController:
        """Get the test controller for external configuration."""
        return self._controller
    
    def build(self, parent: ui.VStack = None):
        """Build test panel UI."""
        with ui.CollapsableFrame("Test Animations", height=0, collapsed=False):
            with ui.VStack(spacing=4, style={"background_color": 0xFF23211F}):
                ui.Spacer(height=4)
                
                # Test selection dropdown
                with ui.HStack(height=24, spacing=8):
                    ui.Spacer(width=8)
                    ui.Label("Test:", width=60)
                    self._test_dropdown = ui.ComboBox(
                        self._selected_test_index,
                        *get_all_test_names(),
                        width=ui.Fraction(1),
                        height=22,
                    )
                    self._test_dropdown.model.add_item_changed_fn(
                        self._on_test_selection_changed
                    )
                    ui.Spacer(width=8)
                
                ui.Spacer(height=2)
                
                # Duration slider
                with ui.HStack(height=24, spacing=8):
                    ui.Spacer(width=8)
                    ui.Label("Duration:", width=60)
                    self._duration_slider = ui.FloatSlider(
                        min=1.0,
                        max=10.0,
                        width=ui.Fraction(1),
                        height=18,
                    )
                    self._duration_slider.model.set_value(self._duration)
                    self._duration_slider.model.add_value_changed_fn(
                        self._on_duration_changed
                    )
                    self._duration_label = ui.Label(
                        f"{self._duration:.1f}s",
                        width=40,
                        style={"color": 0xFFAAAAAA}
                    )
                    ui.Spacer(width=8)
                
                ui.Spacer(height=4)
                
                # Description of selected test
                with ui.HStack(height=0):
                    ui.Spacer(width=8)
                    self._description_label = ui.Label(
                        self._get_current_description(),
                        word_wrap=True,
                        style={"color": 0xFF808080, "font_size": 11},
                        height=0,
                    )
                    ui.Spacer(width=8)
                
                ui.Spacer(height=6)
                
                # Setup / Run / Reset buttons
                with ui.HStack(height=28, spacing=8):
                    ui.Spacer(width=8)
                    self._setup_button = ui.Button(
                        "Setup",
                        width=70,
                        height=26,
                        clicked_fn=self._on_setup_clicked,
                        style={
                            "background_color": 0xFF1565C0,
                            "border_radius": 4,
                        }
                    )
                    self._run_button = ui.Button(
                        "Run",
                        width=70,
                        height=26,
                        clicked_fn=self._on_run_clicked,
                        enabled=False,
                        style={
                            "background_color": 0xFF2E7D32,
                            "border_radius": 4,
                        }
                    )
                    self._reset_button = ui.Button(
                        "Reset",
                        width=70,
                        height=26,
                        clicked_fn=self._on_reset_clicked,
                        enabled=False,
                        style={
                            "background_color": 0xFF757575,
                            "border_radius": 4,
                        }
                    )
                    ui.Spacer()
                
                ui.Spacer(height=4)
                
                # Status display
                with ui.HStack(height=20, spacing=8):
                    ui.Spacer(width=8)
                    ui.Label("Status:", width=50, style={"color": 0xFF808080})
                    self._status_label = ui.Label(
                        "Idle - Select test and click Setup",
                        width=ui.Fraction(1),
                        style={"color": 0xFFAAAAAA}
                    )
                    ui.Spacer(width=8)
                
                ui.Spacer(height=4)
    
    def _get_current_description(self) -> str:
        """Get description of currently selected test."""
        if 0 <= self._selected_test_index < len(ALL_TESTS):
            return ALL_TESTS[self._selected_test_index].description
        return ""
    
    def _on_test_selection_changed(self, model, item) -> None:
        """Handle test selection change."""
        self._selected_test_index = model.get_item_value_model().get_value_as_int()
        if self._description_label:
            self._description_label.text = self._get_current_description()
        
        # Reset to idle if test changed
        if self._state != TestState.IDLE:
            self._set_state(TestState.IDLE)
    
    def _on_duration_changed(self, model) -> None:
        """Handle duration slider change."""
        self._duration = model.get_value_as_float()
        if self._duration_label:
            self._duration_label.text = f"{self._duration:.1f}s"
    
    def _on_setup_clicked(self) -> None:
        """Handle Setup button - position creature at test start."""
        test_ids = get_all_test_ids()
        if not (0 <= self._selected_test_index < len(test_ids)):
            return
        
        test = ALL_TESTS[self._selected_test_index]
        start_pos = test.get_start_position()
        
        # Teleport creature to start and face toward tendroid (origin)
        self._teleport_creature_facing_origin(start_pos)
        
        self._set_state(TestState.SETUP)
        self._update_status(f"Ready: {test.name}")
    
    def _on_run_clicked(self) -> None:
        """Handle Run button - execute test animation."""
        if self._state != TestState.SETUP:
            return
        
        test_ids = get_all_test_ids()
        if 0 <= self._selected_test_index < len(test_ids):
            test_id = test_ids[self._selected_test_index]
            if self._controller.start_test(test_id, self._duration):
                self._set_state(TestState.RUNNING)
    
    def _on_reset_clicked(self) -> None:
        """Handle Reset button - return to idle state."""
        if self._controller.is_running:
            self._controller.stop_test()
        self._set_state(TestState.IDLE)
        self._update_status("Idle - Select test and click Setup")
    
    def _on_status_change(self, status: str) -> None:
        """Handle status update from controller."""
        self._update_status(status)
    
    def _on_test_complete(self, result) -> None:
        """Handle test completion."""
        self._set_state(TestState.COMPLETE)
        contact_msg = "Contact!" if result.contact_occurred else "No contact"
        self._update_status(f"Complete - {contact_msg} - Click Reset")
    
    def _set_state(self, state: str) -> None:
        """Update state and button enabled states."""
        self._state = state
        
        if self._setup_button:
            self._setup_button.enabled = (state == TestState.IDLE)
        if self._run_button:
            self._run_button.enabled = (state == TestState.SETUP)
        if self._reset_button:
            self._reset_button.enabled = (state in [TestState.SETUP, TestState.RUNNING, TestState.COMPLETE])
        if self._test_dropdown:
            self._test_dropdown.enabled = (state == TestState.IDLE)
    
    def _update_status(self, status: str) -> None:
        """Update status label."""
        if self._status_label:
            self._status_label.text = status
    
    def _teleport_creature_facing_origin(self, position: tuple) -> None:
        """Teleport creature to position and face toward origin (tendroid)."""
        cc = self._controller._creature_controller
        if not cc:
            return
        
        from pxr import Gf
        
        # Set position
        cc.position = Gf.Vec3f(*position)
        cc.velocity = Gf.Vec3f(0, 0, 0)
        if cc.translate_op:
            cc.translate_op.Set(Gf.Vec3d(*position))
        
        # Calculate yaw angle to face origin (tendroid at 0,0,0)
        # Direction from creature to origin
        dx = 0.0 - position[0]
        dz = 0.0 - position[2]
        
        # Calculate yaw (rotation around Y axis) in degrees
        # atan2(x, z) gives angle from +Z axis
        yaw_rad = math.atan2(dx, dz)
        yaw_deg = math.degrees(yaw_rad)
        
        # Set creature's rotation (pitch, yaw, roll) - only yaw changes
        cc.current_rotation = Gf.Vec3f(0, yaw_deg, 0)
        if cc.rotate_op:
            cc.rotate_op.Set(cc.current_rotation)
    
    def update(self, dt: float) -> None:
        """
        Update test controller. Call each frame.
        
        Args:
            dt: Delta time in seconds
        """
        self._controller.update(dt)
