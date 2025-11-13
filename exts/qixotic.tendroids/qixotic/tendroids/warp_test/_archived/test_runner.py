"""
Batch Test Runner

Executes performance tests for batch GPU mesh deformation.
Minimal logging for maximum FPS measurement.
"""

import time

import carb

from .test_batch_scenario import BatchTestScenario


class BatchTestRunner:
  """Runs performance tests with minimal overhead."""

  def __init__(self, animator, scenario: BatchTestScenario):
    """Initialize test runner."""
    self.animator = animator
    self.scenario = scenario
    self.current_frame = 0

    # Performance tracking
    self.frame_times = []
    self.min_frame_time = float('inf')
    self.max_frame_time = 0.0
    self.last_log_time = 0
    self.log_interval = 2.0  # Log every 2 seconds instead of every frame

    self.start_time = None
    self.running = False

  def start(self):
    """Start test execution."""
    self.running = True
    self.start_time = time.perf_counter()
    self.current_frame = 0
    self.frame_times.clear()
    self.min_frame_time = float('inf')
    self.max_frame_time = 0.0
    self.last_log_time = self.start_time

    carb.log_info(f"[TestRunner] Started: {self.scenario.name}")
    carb.log_info(f"[TestRunner] Target: {self.scenario.max_frames} frames @ {self.scenario.target_fps}fps")

  def update(self, dt: float) -> bool:
    """
    Update test - returns True if test should continue.
    Ultra-minimal overhead version.
    """
    if not self.running:
      return False

    # Track frame time
    self.frame_times.append(dt)
    self.min_frame_time = min(self.min_frame_time, dt)
    self.max_frame_time = max(self.max_frame_time, dt)

    # Periodic logging (not every frame)
    current_time = time.perf_counter()
    if current_time - self.last_log_time >= self.log_interval:
      elapsed = current_time - self.start_time
      avg_fps = self.current_frame / elapsed if elapsed > 0 else 0
      current_fps = 1.0 / dt if dt > 0 else 0

      carb.log_info(
        f"[TestRunner] Frame {self.current_frame}/{self.scenario.max_frames} | "
        f"Current: {current_fps:.1f}fps | Avg: {avg_fps:.1f}fps | "
        f"Min: {1000 * self.min_frame_time:.2f}ms | Max: {1000 * self.max_frame_time:.2f}ms"
      )
      self.last_log_time = current_time

    self.current_frame += 1

    # Check completion
    if self.current_frame >= self.scenario.max_frames:
      self._finish_test()
      return False

    return True

  def _finish_test(self):
    """Complete test and report results."""
    if not self.frame_times:
      return

    total_time = time.perf_counter() - self.start_time

    # Calculate statistics
    avg_frame_time = sum(self.frame_times) / len(self.frame_times)
    avg_fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
    min_fps = 1.0 / self.max_frame_time if self.max_frame_time > 0 else 0
    max_fps = 1.0 / self.min_frame_time if self.min_frame_time > 0 else 0

    # Final report
    carb.log_info("=" * 80)
    carb.log_info(f"[TestRunner] COMPLETED: {self.scenario.name}")
    carb.log_info(f"[TestRunner] Tubes: {self.scenario.tube_count}")
    carb.log_info(f"[TestRunner] Frames: {self.current_frame}")
    carb.log_info(f"[TestRunner] Duration: {total_time:.2f}s")
    carb.log_info("-" * 80)
    carb.log_info(f"[TestRunner] Average FPS: {avg_fps:.2f}")
    carb.log_info(f"[TestRunner] Min FPS: {min_fps:.2f} (worst frame: {1000 * self.max_frame_time:.2f}ms)")
    carb.log_info(f"[TestRunner] Max FPS: {max_fps:.2f} (best frame: {1000 * self.min_frame_time:.2f}ms)")
    carb.log_info("-" * 80)

    # Performance assessment
    if avg_fps >= self.scenario.target_fps:
      carb.log_info(f"[TestRunner] ✓ TARGET MET ({self.scenario.target_fps}fps)")
    else:
      shortfall = self.scenario.target_fps - avg_fps
      carb.log_info(f"[TestRunner] ✗ Below target by {shortfall:.1f}fps")

    carb.log_info("=" * 80)

    self.running = False

  def stop(self):
    """Stop test early."""
    if self.running:
      self._finish_test()
