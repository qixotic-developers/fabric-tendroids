"""
Stress Test Controller for Tendroids Performance Analysis

Orchestrates automated stress testing scenarios to identify performance ceilings.
Runs predefined test configurations, measures FPS, and generates performance reports.
"""

import time
import json
from pathlib import Path
from typing import Dict, List, Optional
import carb
from pxr import Usd


class StressTestController:
    """Manages automated stress testing of Tendroid system performance."""
    
    def __init__(self, stage: Usd.Stage, scene_manager, config_path: Optional[str] = None):
        """
        Initialize stress test controller.
        
        Args:
            stage: USD stage
            scene_manager: TendroidSceneManager instance
            config_path: Optional path to stress test config JSON
        """
        self._stage = stage
        self._scene_manager = scene_manager
        self._results: List[Dict] = []
        self._fps_samples: List[float] = []
        self._current_scenario: Optional[Dict] = None
        self._scenario_start_time: float = 0.0
        self._last_sample_time: float = 0.0
        
        # Load configuration
        if config_path is None:
            config_path = str(Path(__file__).parent / "config" / "stress_test_config.json")
        
        self._config = self._load_config(config_path)
        self._test_settings = self._config.get("test_settings", {})
        self._scenarios = self._config.get("scenarios", [])
        self._current_scenario_index = 0
        
        carb.log_info(f"Stress test controller initialized with {len(self._scenarios)} scenarios")
    
    def _load_config(self, config_path: str) -> Dict:
        """Load stress test configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            carb.log_error(f"Failed to load stress test config: {e}")
            return {"test_settings": {}, "scenarios": []}
    
    def start_test_suite(self) -> bool:
        """
        Start the full stress test suite.
        
        Returns:
            True if test suite started successfully
        """
        if not self._scenarios:
            carb.log_error("No test scenarios defined")
            return False
        
        self._current_scenario_index = 0
        self._results = []
        
        carb.log_info("=" * 80)
        carb.log_info("STRESS TEST SUITE STARTING")
        carb.log_info(f"Total scenarios: {len(self._scenarios)}")
        carb.log_info("=" * 80)
        
        return self._start_next_scenario()
    
    def _start_next_scenario(self) -> bool:
        """Start the next test scenario."""
        if self._current_scenario_index >= len(self._scenarios):
            self._finish_test_suite()
            return False
        
        scenario = self._scenarios[self._current_scenario_index]
        self._current_scenario = scenario
        self._fps_samples = []
        self._scenario_start_time = time.time()
        self._last_sample_time = self._scenario_start_time
        
        carb.log_info("-" * 80)
        carb.log_info(f"SCENARIO {self._current_scenario_index + 1}/{len(self._scenarios)}: {scenario['name']}")
        carb.log_info(f"Description: {scenario['description']}")
        carb.log_info(f"Tendroids: {scenario['tendroid_count']}, Bubbles: {scenario['bubbles_enabled']}")
        carb.log_info("-" * 80)
        
        # Configure scene manager
        self._scene_manager.stop_animation()
        self._scene_manager.clear_tendroids()
        
        # Set bubble system state (if manager exists)
        if self._scene_manager.bubble_manager:
            # For now, bubbles are controlled by config - we can't dynamically disable them
            # without recreating the bubble manager
            pass
        
        # Spawn Tendroids
        self._scene_manager.create_tendroids(
            count=scenario['tendroid_count'],
            spawn_area=(200, 200),
            num_segments=16
        )
        
        # Start animation
        self._scene_manager.start_animation()
        
        return True
    
    def update(self, dt: float) -> bool:
        """
        Update stress test controller (call every frame).
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if test suite is still running
        """
        if self._current_scenario is None:
            return False
        
        elapsed = time.time() - self._scenario_start_time
        warmup = self._test_settings.get("warmup_duration", 3.0)
        
        # Sample FPS after warmup period
        if elapsed > warmup:
            sample_interval = self._test_settings.get("fps_sample_interval", 0.5)
            if time.time() - self._last_sample_time >= sample_interval:
                fps = 1.0 / dt if dt > 0 else 0.0
                self._fps_samples.append(fps)
                self._last_sample_time = time.time()
        
        # Check if scenario duration complete
        duration = self._test_settings.get("duration_per_scenario", 15.0)
        if elapsed >= (warmup + duration):
            self._finish_scenario()
            self._current_scenario_index += 1
            return self._start_next_scenario()
        
        return True
    
    def _finish_scenario(self):
        """Finish current scenario and record results."""
        if not self._fps_samples:
            carb.log_warn("No FPS samples collected for scenario")
            return
        
        avg_fps = sum(self._fps_samples) / len(self._fps_samples)
        min_fps = min(self._fps_samples)
        max_fps = max(self._fps_samples)
        
        # Get bubble count if available
        bubble_count = self._scene_manager.get_bubble_count() if self._scene_manager.bubble_manager else 0
        
        result = {
            "scenario": self._current_scenario["name"],
            "tendroid_count": self._current_scenario["tendroid_count"],
            "bubbles_enabled": self._current_scenario["bubbles_enabled"],
            "bubble_count": bubble_count,
            "avg_fps": avg_fps,
            "min_fps": min_fps,
            "max_fps": max_fps,
            "sample_count": len(self._fps_samples)
        }
        
        self._results.append(result)
        
        # Log immediate results
        carb.log_info(f"Results: AVG={avg_fps:.1f} fps, MIN={min_fps:.1f}, MAX={max_fps:.1f}, Bubbles={bubble_count}")
        
        # Performance assessment
        target_fps = self._test_settings.get("target_fps", 30.0)
        if avg_fps >= target_fps:
            carb.log_info(f"✓ PASS - Exceeded target {target_fps} fps")
        else:
            carb.log_warn(f"✗ FAIL - Below target {target_fps} fps")
    
    def _finish_test_suite(self):
        """Complete test suite and generate final report."""
        carb.log_info("=" * 80)
        carb.log_info("STRESS TEST SUITE COMPLETE")
        carb.log_info("=" * 80)
        
        self._print_summary()
        self._save_results()
        
        self._current_scenario = None
    
    def _print_summary(self):
        """Print summary table of all results."""
        carb.log_info("\nPerformance Summary:")
        carb.log_info(f"{'Scenario':<20} {'Tendroids':>10} {'Bubbles':>8} {'Bubble#':>8} {'AVG FPS':>10} {'MIN FPS':>10}")
        carb.log_info("-" * 80)
        
        for result in self._results:
            bubbles = "Yes" if result["bubbles_enabled"] else "No"
            carb.log_info(
                f"{result['scenario']:<20} "
                f"{result['tendroid_count']:>10} "
                f"{bubbles:>8} "
                f"{result['bubble_count']:>8} "
                f"{result['avg_fps']:>10.1f} "
                f"{result['min_fps']:>10.1f}"
            )
    
    def _save_results(self):
        """Save detailed results to log file."""
        log_file = self._test_settings.get("log_file", "stress_test_results.log")
        log_path = Path(__file__).parent.parent / log_file
        
        try:
            with open(log_path, 'w') as f:
                f.write("Tendroids Stress Test Results\n")
                f.write("=" * 80 + "\n")
                f.write(f"Test Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Total Scenarios: {len(self._results)}\n\n")
                
                for result in self._results:
                    f.write(f"Scenario: {result['scenario']}\n")
                    f.write(f"  Tendroids: {result['tendroid_count']}\n")
                    f.write(f"  Bubbles Enabled: {result['bubbles_enabled']}\n")
                    f.write(f"  Active Bubbles: {result['bubble_count']}\n")
                    f.write(f"  Average FPS: {result['avg_fps']:.2f}\n")
                    f.write(f"  Min FPS: {result['min_fps']:.2f}\n")
                    f.write(f"  Max FPS: {result['max_fps']:.2f}\n")
                    f.write(f"  Samples: {result['sample_count']}\n\n")
                
                # Analysis
                f.write("\nAnalysis:\n")
                f.write("-" * 80 + "\n")
                
                target_fps = self._test_settings.get("target_fps", 30.0)
                passing = [r for r in self._results if r["avg_fps"] >= target_fps]
                failing = [r for r in self._results if r["avg_fps"] < target_fps]
                
                f.write(f"Scenarios passing {target_fps} fps target: {len(passing)}/{len(self._results)}\n")
                if failing:
                    f.write(f"\nScenarios below target:\n")
                    for r in failing:
                        f.write(f"  - {r['scenario']}: {r['avg_fps']:.1f} fps\n")
            
            carb.log_info(f"Detailed results saved to: {log_path}")
        
        except Exception as e:
            carb.log_error(f"Failed to save results: {e}")
    
    def is_running(self) -> bool:
        """Check if test suite is currently running."""
        return self._current_scenario is not None
    
    def get_current_progress(self) -> str:
        """Get current test progress as string."""
        if not self.is_running():
            return "Test suite not running"
        
        return f"Scenario {self._current_scenario_index + 1}/{len(self._scenarios)}: {self._current_scenario['name']}"
