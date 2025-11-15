"""
Phase 2 Stress Test - Performance Ceiling Analysis
==================================================

Automated test to find performance limits of current transform-based architecture.

Test Plan:
1. Spawn Tendroids in increments: 15, 20, 25, 30
2. Monitor FPS for 10 seconds at each count
3. Log performance metrics and degradation curve
4. Identify bottlenecks and breaking points

Usage:
    Run from Omniverse Script Editor or standalone Python with Omniverse Kit
"""

import time
import carb
import omni.usd
from pathlib import Path
from datetime import datetime


class StressTestResults:
    """Container for stress test performance data."""
    
    def __init__(self):
        self.test_runs = []
        self.start_time = datetime.now()
        self.fastmesh_available = False
    
    def add_run(self, tendroid_count: int, actual_count: int, avg_fps: float, 
                min_fps: float, max_fps: float, samples: int):
        """Record results from a test run."""
        self.test_runs.append({
            'requested_count': tendroid_count,
            'actual_count': actual_count,
            'avg_fps': avg_fps,
            'min_fps': min_fps,
            'max_fps': max_fps,
            'samples': samples,
            'timestamp': datetime.now()
        })
    
    def save_to_file(self, output_dir: Path):
        """Save results to timestamped log file."""
        timestamp = self.start_time.strftime("%Y%m%d_%H%M%S")
        filename = f"stress_test_{timestamp}.log"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("Tendroids Phase 2 Stress Test Results\n")
            f.write("=" * 70 + "\n")
            f.write(f"Test Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Architecture: Transform-based (16 segments)\n")
            fastmesh_status = "YES (C++ 240x speedup)" if self.fastmesh_available else "NO (Python fallback)"
            f.write(f"FastMeshUpdater: {fastmesh_status}\n")
            f.write("\n")
            
            f.write("-" * 70 + "\n")
            f.write("Performance Data\n")
            f.write("-" * 70 + "\n")
            f.write(f"{'Requested':<10} {'Actual':<8} {'Avg FPS':<10} {'Min FPS':<10} {'Max FPS':<10} {'Samples':<8}\n")
            f.write("-" * 70 + "\n")
            
            for run in self.test_runs:
                f.write(
                    f"{run['requested_count']:<10} "
                    f"{run['actual_count']:<8} "
                    f"{run['avg_fps']:<10.2f} "
                    f"{run['min_fps']:<10.2f} "
                    f"{run['max_fps']:<10.2f} "
                    f"{run['samples']:<8}\n"
                )
            
            f.write("\n")
            f.write("-" * 70 + "\n")
            f.write("Analysis\n")
            f.write("-" * 70 + "\n")
            
            if len(self.test_runs) > 1:
                baseline = self.test_runs[0]
                f.write(f"Baseline ({baseline['actual_count']} Tendroids): {baseline['avg_fps']:.2f} fps\n\n")
                
                for run in self.test_runs[1:]:
                    degradation = ((baseline['avg_fps'] - run['avg_fps']) / 
                                   baseline['avg_fps'] * 100)
                    f.write(f"{run['actual_count']} Tendroids: {run['avg_fps']:.2f} fps "
                           f"({degradation:+.1f}%)\n")
            
            f.write("\n")
            
            # Warnings section
            spawn_failures = [r for r in self.test_runs if r['actual_count'] < r['requested_count']]
            if spawn_failures:
                f.write("-" * 70 + "\n")
                f.write("WARNINGS\n")
                f.write("-" * 70 + "\n")
                for run in spawn_failures:
                    failed = run['requested_count'] - run['actual_count']
                    f.write(f"⚠ {failed} Tendroids failed to spawn at count {run['requested_count']}\n")
                f.write("\nRecommendation: Increase spawn area or reduce test counts\n")
                f.write("\n")
            
            if not self.fastmesh_available:
                if not spawn_failures:
                    f.write("-" * 70 + "\n")
                    f.write("WARNINGS\n")
                    f.write("-" * 70 + "\n")
                f.write("⚠ FastMeshUpdater C++ extension not loaded\n")
                f.write("Performance results are ~4x slower than production capability\n")
                f.write("Fix PerfStats registration issue before Phase 2B\n")
                f.write("\n")
            
            f.write("=" * 70 + "\n")
        
        carb.log_info(f"[StressTest] Results saved to: {filepath}")
        return filepath


class FPSMonitor:
    """Monitor and calculate FPS statistics using frame timestamps."""
    
    def __init__(self):
        self.fps_samples = []
        self.start_time = None
        self.last_sample_time = None
        self.monitoring = False
    
    def start(self):
        """Begin monitoring."""
        self.fps_samples = []
        self.start_time = time.perf_counter()
        self.last_sample_time = self.start_time
        self.monitoring = True
    
    def record_frame(self):
        """Record a frame timestamp (call this every frame)."""
        if not self.monitoring:
            return
        
        current_time = time.perf_counter()
        if self.last_sample_time is not None:
            delta = current_time - self.last_sample_time
            if delta > 0:
                fps = 1.0 / delta
                # Filter out outliers (>1000 fps likely measurement error)
                if fps < 1000.0:
                    self.fps_samples.append(fps)
        self.last_sample_time = current_time
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time since monitoring started."""
        if self.start_time is None:
            return 0.0
        return time.perf_counter() - self.start_time
    
    def stop(self):
        """Stop monitoring."""
        self.monitoring = False
    
    def get_statistics(self):
        """Calculate avg, min, max FPS."""
        if not self.fps_samples:
            return 0.0, 0.0, 0.0, 0
        
        return (
            sum(self.fps_samples) / len(self.fps_samples),
            min(self.fps_samples),
            max(self.fps_samples),
            len(self.fps_samples)
        )


def check_fastmesh_available():
    """Check if FastMeshUpdater C++ extension is loaded."""
    try:
        from qixotic.tendroids import fast_mesh_updater
        carb.log_info("[StressTest] FastMeshUpdater C++ extension detected")
        return True
    except ImportError:
        carb.log_warn("[StressTest] FastMeshUpdater not available - using Python fallback")
        return False


class StressTestRunner:
    """
    Runs stress test using async update callbacks to avoid blocking Kit.
    
    This approach lets Kit's update loop run normally while we monitor FPS.
    """
    
    def __init__(self, test_counts, monitoring_duration, output_dir):
        self.test_counts = test_counts or [15, 20, 25, 30]
        self.monitoring_duration = monitoring_duration
        self.output_dir = output_dir or Path(__file__).parent / "stress_test_results"
        self.output_dir.mkdir(exist_ok=True)
        
        self.results = StressTestResults()
        self.results.fastmesh_available = check_fastmesh_available()
        
        self.scene_manager = None
        self.fps_monitor = FPSMonitor()
        self.update_sub = None
        
        self.current_test_index = 0
        self.test_state = "init"  # init -> creating -> monitoring -> cleanup -> done
    
    def start(self):
        """Start the test sequence."""
        from qixotic.tendroids.scene.manager import TendroidSceneManager
        
        carb.log_info("=" * 70)
        carb.log_info("[StressTest] Phase 2 Performance Ceiling Analysis")
        carb.log_info("=" * 70)
        
        self.scene_manager = TendroidSceneManager()
        
        # Subscribe to update events
        import omni.kit.app
        update_stream = omni.kit.app.get_app().get_update_event_stream()
        self.update_sub = update_stream.create_subscription_to_pop(
            self._on_update,
            name="StressTest.Monitor"
        )
        
        self.test_state = "creating"
        self._start_next_test()
    
    def _start_next_test(self):
        """Start the next test in the sequence."""
        if self.current_test_index >= len(self.test_counts):
            self._finish_tests()
            return
        
        count = self.test_counts[self.current_test_index]
        carb.log_info(f"\n[StressTest] Testing with {count} Tendroids...")
        
        # Scale spawn area with count
        spawn_size = int(300 + (count - 15) * 15)
        carb.log_info(f"[StressTest] Spawn area: {spawn_size}x{spawn_size}")
        
        # Create Tendroids
        success = self.scene_manager.create_tendroids(
            count=count,
            spawn_area=(spawn_size, spawn_size),
            radius_range=(8, 12),
            num_segments=16
        )
        
        if not success:
            carb.log_error(f"[StressTest] Failed to create {count} Tendroids")
            self.current_test_index += 1
            self._start_next_test()
            return
        
        actual_count = self.scene_manager.get_tendroid_count()
        if actual_count < count:
            carb.log_warn(
                f"[StressTest] Only spawned {actual_count}/{count} Tendroids"
            )
        
        # Start animation
        carb.log_info("[StressTest] Starting animation...")
        self.scene_manager.start_animation()
        
        # Start FPS monitoring after brief warmup
        self.test_state = "monitoring"
        self.fps_monitor.start()
        carb.log_info(f"[StressTest] Monitoring for {self.monitoring_duration}s...")
    
    def _on_update(self, event):
        """Called every frame by Kit."""
        if self.test_state == "monitoring":
            # Record frame
            self.fps_monitor.record_frame()
            
            # Check if monitoring period complete
            if self.fps_monitor.get_elapsed_time() >= self.monitoring_duration:
                self._finish_current_test()
    
    def _finish_current_test(self):
        """Complete current test and move to next."""
        count = self.test_counts[self.current_test_index]
        actual_count = self.scene_manager.get_tendroid_count()
        
        # Get statistics
        self.fps_monitor.stop()
        avg_fps, min_fps, max_fps, samples = self.fps_monitor.get_statistics()
        self.results.add_run(count, actual_count, avg_fps, min_fps, max_fps, samples)
        
        carb.log_info(
            f"[StressTest] {actual_count} Tendroids: "
            f"Avg={avg_fps:.2f} fps, Min={min_fps:.2f}, Max={max_fps:.2f}"
        )
        
        # Stop animation
        self.scene_manager.stop_animation()
        
        # Move to next test
        self.current_test_index += 1
        self.test_state = "creating"
        self._start_next_test()
    
    def _finish_tests(self):
        """Complete all tests and save results."""
        # Unsubscribe from updates
        if self.update_sub:
            self.update_sub.unsubscribe()
            self.update_sub = None
        
        # Save results
        log_path = self.results.save_to_file(self.output_dir)
        
        carb.log_info("\n" + "=" * 70)
        carb.log_info("[StressTest] Test Complete")
        carb.log_info(f"[StressTest] Results: {log_path}")
        carb.log_info("=" * 70)
        
        if not self.results.fastmesh_available:
            carb.log_warn("[StressTest] ⚠ CRITICAL: FastMeshUpdater not loaded!")
            carb.log_warn("[StressTest] Performance is ~4x slower than production")


def run_stress_test(
    test_counts: list = None,
    monitoring_duration: float = 10.0,
    output_dir: Path = None
):
    """
    Execute automated stress test.
    
    Args:
        test_counts: List of Tendroid counts to test (default: [15, 20, 25, 30])
        monitoring_duration: Seconds to monitor FPS at each count
        output_dir: Directory for log files (default: ./stress_test_results)
    
    Returns:
        StressTestRunner instance (test runs asynchronously)
    """
    runner = StressTestRunner(test_counts, monitoring_duration, output_dir)
    runner.start()
    return runner


if __name__ == "__main__":
    # Run with default settings
    run_stress_test()
