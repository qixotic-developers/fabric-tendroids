"""
Test Controller - Executes automated test animations

Manages test execution, creature positioning, and result recording.
"""

import os
import time
from datetime import datetime
from typing import Optional, Callable

import carb

from .test_case import TestCase, TestResult
from .test_registry import get_test_by_id, ALL_TESTS
from ..contact.input_lock_helpers import InputLockReason


class TestController:
    """
    Executes automated creature-tendroid interaction tests.
    
    Handles:
    - Teleporting creature to test start position
    - Animating creature through waypoints
    - Disabling keyboard during test
    - Collecting metrics and saving results
    """
    
    def __init__(self, log_dir: str = None):
        """
        Initialize test controller.
        
        Args:
            log_dir: Directory for saving test logs (optional)
        """
        self._current_test: Optional[TestCase] = None
        self._is_running = False
        self._start_time = 0.0
        self._duration = 5.0  # Default duration in seconds
        self._elapsed = 0.0
        
        # External references (set via setters)
        self._creature_controller = None
        self._deflection_integration = None
        self._color_effect_controller = None
        
        # Metrics collection
        self._result: Optional[TestResult] = None
        self._max_deflection_seen = 0.0
        
        # Callbacks
        self._on_test_complete: Optional[Callable[[TestResult], None]] = None
        self._on_status_change: Optional[Callable[[str], None]] = None
        
        # Logging
        self._log_dir = log_dir
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    def set_creature_controller(self, controller) -> None:
        """Set creature controller reference."""
        self._creature_controller = controller
    
    def set_deflection_integration(self, deflection) -> None:
        """Set deflection integration for metrics."""
        self._deflection_integration = deflection
    
    def set_color_effect_controller(self, color_controller) -> None:
        """Set color effect controller for metrics."""
        self._color_effect_controller = color_controller
    
    def set_on_test_complete(self, callback: Callable[[TestResult], None]) -> None:
        """Set callback for test completion."""
        self._on_test_complete = callback
    
    def set_on_status_change(self, callback: Callable[[str], None]) -> None:
        """Set callback for status updates."""
        self._on_status_change = callback
    
    @property
    def is_running(self) -> bool:
        """Check if a test is currently running."""
        return self._is_running
    
    @property
    def current_test(self) -> Optional[TestCase]:
        """Get currently running test."""
        return self._current_test
    
    @property
    def progress(self) -> float:
        """Get test progress (0.0 - 1.0)."""
        if not self._is_running or self._duration <= 0:
            return 0.0
        return min(1.0, self._elapsed / self._duration)
    
    def start_test(self, test_id: str, duration: float = 5.0) -> bool:
        """
        Start a test by ID.
        
        Args:
            test_id: Test case ID from registry
            duration: Total test duration in seconds
            
        Returns:
            True if test started, False if invalid test or already running
        """
        if self._is_running:
            carb.log_warn("[TestController] Test already running")
            return False
        
        test = get_test_by_id(test_id)
        if not test:
            carb.log_error(f"[TestController] Unknown test: {test_id}")
            return False
        
        if not self._creature_controller:
            carb.log_error("[TestController] No creature controller set")
            return False
        
        self._current_test = test
        self._duration = max(0.5, duration)
        self._elapsed = 0.0
        self._max_deflection_seen = 0.0
        self._animation_stopped = False  # Reset animation stop flag
        
        # Initialize result tracking
        self._result = TestResult(
            test_id=test_id,
            duration=self._duration,
            timestamp=datetime.now().isoformat()
        )
        
        # Note: Creature already positioned by UI setup phase
        # Just disable keyboard input during test
        self._set_keyboard_enabled(False)
        
        self._is_running = True
        self._start_time = time.perf_counter()
        
        self._update_status(f"Running: {test.name}")
        carb.log_info(f"[TestController] Started test: {test.name} ({duration:.1f}s)")
        
        return True
    
    def stop_test(self) -> None:
        """Stop the currently running test."""
        if not self._is_running:
            return
        
        self._is_running = False
        self._set_keyboard_enabled(True)
        
        if self._result:
            self._finalize_result()
            
            # Save log if directory configured
            if self._log_dir:
                self._save_result()
            
            # Callback
            if self._on_test_complete:
                self._on_test_complete(self._result)
        
        self._update_status("Stopped")
        carb.log_info(f"[TestController] Test stopped: {self._current_test.name if self._current_test else 'None'}")
        
        self._current_test = None
        self._result = None
        self._animation_stopped = False
    
    def update(self, dt: float) -> None:
        """
        Update test animation. Call this each frame.
        
        Args:
            dt: Delta time in seconds
        """
        if not self._is_running or not self._current_test:
            return
        
        self._elapsed += dt
        
        # Check if test complete
        if self._elapsed >= self._duration:
            self.stop_test()
            return
        
        # If animation stopped (contact occurred), skip position updates
        # but continue collecting metrics
        if getattr(self, '_animation_stopped', False):
            self._collect_metrics()
            return
        
        # Calculate position from waypoints
        fraction = self._elapsed / self._duration
        position = self._current_test.get_position_at_fraction(fraction)
        
        # Calculate velocity from position change (critical for deflection detection!)
        old_pos = self._creature_controller.position if self._creature_controller else None
        
        # Move creature
        self._set_creature_position(position)
        
        # Update velocity based on actual movement (for deflection detection)
        if self._creature_controller and old_pos is not None and dt > 0:
            from pxr import Gf
            dx = position[0] - float(old_pos[0])
            dy = position[1] - float(old_pos[1])
            dz = position[2] - float(old_pos[2])
            self._creature_controller.velocity = Gf.Vec3f(dx/dt, dy/dt, dz/dt)
        
        # Debug logging every 30 frames
        self._debug_frame_count = getattr(self, '_debug_frame_count', 0) + 1
        if self._debug_frame_count % 30 == 0:
            self._log_test_diagnostics(position)
        
        # Collect metrics
        self._collect_metrics()
    
    def _log_test_diagnostics(self, position: tuple) -> None:
        """Log diagnostic info during test execution."""
        if not self._creature_controller:
            carb.log_warn("[TestController DEBUG] No creature controller!")
            return
        
        cc = self._creature_controller
        carb.log_info(
            f"[TestController DEBUG] pos=({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}), "
            f"cc.pos=({cc.position[0]:.1f}, {cc.position[1]:.1f}, {cc.position[2]:.1f}), "
            f"vel=({cc.velocity[0]:.1f}, {cc.velocity[1]:.1f}, {cc.velocity[2]:.1f})"
        )
        
        if self._deflection_integration:
            states = self._deflection_integration.get_deflection_states()
            for name, state in states.items():
                carb.log_info(
                    f"[TestController DEBUG] {name}: approach={state.last_approach_type}, "
                    f"deflecting={state.is_deflecting}, angle={state.current_angle:.3f}"
                )
    
    def _teleport_creature(self, position: tuple) -> None:
        """Instantly move creature to position."""
        if self._creature_controller:
            from pxr import Gf
            self._creature_controller.position = Gf.Vec3f(*position)
            self._creature_controller.velocity = Gf.Vec3f(0, 0, 0)
            if self._creature_controller.translate_op:
                self._creature_controller.translate_op.Set(Gf.Vec3d(*position))
    
    def _set_creature_position(self, position: tuple) -> None:
        """Set creature position during animation."""
        if self._creature_controller:
            from pxr import Gf
            self._creature_controller.position = Gf.Vec3f(*position)
            if self._creature_controller.translate_op:
                self._creature_controller.translate_op.Set(Gf.Vec3d(*position))
    
    def _set_keyboard_enabled(self, enabled: bool) -> None:
        """Enable/disable keyboard input on creature."""
        if self._creature_controller:
            # Use input lock system
            if enabled:
                # Clear test lock (only if it was TEST, not actual contact)
                if self._creature_controller._input_lock_status.reason == InputLockReason.TEST:
                    self._creature_controller._input_lock_status.is_locked = False
                    self._creature_controller._input_lock_status.reason = InputLockReason.NONE
            else:
                # Lock input for testing (distinct from CONTACT)
                self._creature_controller._input_lock_status.is_locked = True
                self._creature_controller._input_lock_status.reason = InputLockReason.TEST
    
    def _collect_metrics(self) -> None:
        """Collect metrics during test execution."""
        if not self._result:
            return
        
        # Track max deflection angle - use get_deflection_states() method
        if self._deflection_integration:
            states = self._deflection_integration.get_deflection_states()
            for state in states.values():
                if abs(state.current_angle) > self._max_deflection_seen:
                    self._max_deflection_seen = abs(state.current_angle)
        
        # Track color effect (shock = contact)
        if self._color_effect_controller:
            if self._color_effect_controller.is_shocked:
                if not self._result.color_effect_triggered:
                    self._result.color_effect_triggered = True
                    self._result.contact_occurred = True
                    self._result.contact_time = self._elapsed
                    
                    # STOP TEST ON CONTACT: Let physics/repulsion take over
                    self._stop_animation_on_contact()
                    return
        
        # Track contact/repulsion - only count actual contact, not TEST lock
        if self._creature_controller and hasattr(self._creature_controller, '_input_lock_status'):
            status = self._creature_controller._input_lock_status
            if status.is_locked and status.reason != InputLockReason.TEST:
                if not self._result.input_locked:
                    self._result.input_locked = True
                    if not self._result.contact_occurred:
                        self._result.contact_occurred = True
                        self._result.contact_time = self._elapsed
    
    def _stop_animation_on_contact(self) -> None:
        """
        Stop test animation when contact occurs.
        
        Clears TEST input lock so repulsion physics and keyboard can work.
        Test remains "running" for metric collection but position updates stop.
        """
        carb.log_info("[TestController] Contact detected - stopping animation, enabling physics")
        
        # Clear TEST lock so repulsion/keyboard can work
        if self._creature_controller:
            status = self._creature_controller._input_lock_status
            if status.reason == InputLockReason.TEST:
                # Let the color effect system manage lock state now
                self._creature_controller._input_lock_status.is_locked = False
                self._creature_controller._input_lock_status.reason = InputLockReason.NONE
        
        # Stop position updates but keep test "running" for final metrics
        self._animation_stopped = True
    
    def _finalize_result(self) -> None:
        """Finalize metrics at end of test."""
        if not self._result:
            return
        
        self._result.max_deflection_angle = self._max_deflection_seen
        
        # Check if tendroid recovered (angle near zero at end)
        if self._deflection_integration:
            all_recovered = True
            states = self._deflection_integration.get_deflection_states()
            for state in states.values():
                if abs(state.current_angle) > 0.05:  # ~3 degrees
                    all_recovered = False
                    break
            self._result.tendroid_recovered = all_recovered
    
    def _save_result(self) -> None:
        """Save test result to log file."""
        if not self._result or not self._log_dir:
            return
        
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{timestamp}_{self._result.test_id}.yaml"
            filepath = os.path.join(self._log_dir, filename)
            
            # Simple YAML-like format (no external dependency)
            with open(filepath, 'w') as f:
                data = self._result.to_dict()
                f.write(f"test_id: {data['test_id']}\n")
                f.write(f"timestamp: {data['timestamp']}\n")
                f.write(f"duration: {data['duration']}\n")
                f.write("result:\n")
                for key, value in data['result'].items():
                    f.write(f"  {key}: {value}\n")
            
            carb.log_info(f"[TestController] Saved result to {filepath}")
        except Exception as e:
            carb.log_error(f"[TestController] Failed to save result: {e}")
    
    def _update_status(self, status: str) -> None:
        """Update status and notify callback."""
        if self._on_status_change:
            self._on_status_change(status)
    
    def get_available_tests(self) -> list[tuple[str, str]]:
        """Get list of (id, name) tuples for all available tests."""
        return [(test.id, test.name) for test in ALL_TESTS]
