"""
Frame-by-frame performance profiler for Tendroid animation

Instruments the update pipeline to identify bottlenecks.
"""

import time
import carb
from collections import defaultdict


class PerformanceProfiler:
    """
    Profiles Tendroid animation performance.
    
    Call start() at beginning of frame, record() at checkpoints, end() at frame end.
    """
    
    def __init__(self):
        self.frame_times = defaultdict(list)
        self.frame_start = 0
        self.last_checkpoint = 0
        self.enabled = False
        self.frame_count = 0
    
    def enable(self):
        """Enable profiling."""
        self.enabled = True
        self.frame_times.clear()
        self.frame_count = 0
        carb.log_info("[Profiler] Performance profiling ENABLED")
    
    def disable(self):
        """Disable profiling."""
        self.enabled = False
        carb.log_info("[Profiler] Performance profiling DISABLED")
    
    def start_frame(self):
        """Start timing a new frame."""
        if not self.enabled:
            return
        self.frame_start = time.perf_counter()
        self.last_checkpoint = self.frame_start
    
    def record(self, checkpoint_name: str):
        """Record time since last checkpoint."""
        if not self.enabled:
            return
        
        now = time.perf_counter()
        elapsed_ms = (now - self.last_checkpoint) * 1000
        self.frame_times[checkpoint_name].append(elapsed_ms)
        self.last_checkpoint = now
    
    def end_frame(self):
        """End frame timing."""
        if not self.enabled:
            return
        
        now = time.perf_counter()
        total_ms = (now - self.frame_start) * 1000
        self.frame_times['TOTAL_FRAME'].append(total_ms)
        self.frame_count += 1
    
    def print_report(self):
        """Print performance report."""
        if not self.enabled or self.frame_count == 0:
            carb.log_warn("[Profiler] No data to report")
            return
        
        carb.log_info("=" * 70)
        carb.log_info(f"Performance Profile Report ({self.frame_count} frames)")
        carb.log_info("=" * 70)
        
        # Sort by average time (descending)
        sorted_checkpoints = sorted(
            self.frame_times.items(),
            key=lambda x: sum(x[1]) / len(x[1]),
            reverse=True
        )
        
        carb.log_info(f"{'Checkpoint':<30} {'Avg (ms)':<12} {'Min (ms)':<12} {'Max (ms)':<12}")
        carb.log_info("-" * 70)
        
        for name, times in sorted_checkpoints:
            avg = sum(times) / len(times)
            min_t = min(times)
            max_t = max(times)
            carb.log_info(f"{name:<30} {avg:<12.3f} {min_t:<12.3f} {max_t:<12.3f}")
        
        carb.log_info("=" * 70)
        
        # Calculate per-Tendroid costs
        if 'UPDATE_ALL_TENDROIDS' in self.frame_times:
            total_update_times = self.frame_times['UPDATE_ALL_TENDROIDS']
            avg_total = sum(total_update_times) / len(total_update_times)
            
            # Estimate per-tendroid cost (assuming 30 Tendroids)
            per_tendroid = avg_total / 30
            carb.log_info(f"Estimated cost per Tendroid: {per_tendroid:.3f} ms")
            carb.log_info(f"Theoretical max Tendroids at 60fps: {int(16.67 / per_tendroid)}")
            carb.log_info("=" * 70)


# Global profiler instance
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _profiler


# Convenience functions
def enable():
    """Enable profiling."""
    _profiler.enable()


def disable():
    """Disable profiling."""
    _profiler.disable()


def start_frame():
    """Start frame timing."""
    _profiler.start_frame()


def record(checkpoint: str):
    """Record checkpoint."""
    _profiler.record(checkpoint)


def end_frame():
    """End frame timing."""
    _profiler.end_frame()


def print_report():
    """Print report."""
    _profiler.print_report()
