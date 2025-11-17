"""
Memory Monitor

Tracks memory usage during Warp kernel execution to identify leaks and allocation patterns.
Monitors both Python process memory and GPU memory usage.
"""

import tracemalloc
import time
import psutil
import json
import os
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MemorySample:
    """Single memory measurement snapshot"""
    frame: int
    timestamp: float
    python_mb: float
    gpu_mb: Optional[float]
    delta_python_mb: float
    delta_gpu_mb: Optional[float]


class MemoryMonitor:
    """Monitors and records memory usage during test execution"""

    def __init__(self):
        self.samples: List[MemorySample] = []
        self.baseline_python_mb: Optional[float] = None
        self.baseline_gpu_mb: Optional[float] = None
        self.last_python_mb: Optional[float] = None
        self.last_gpu_mb: Optional[float] = None
        self.process = psutil.Process()
        self.monitoring = False

    def start_monitoring(self):
        """Begin memory tracking"""
        tracemalloc.start()
        self.monitoring = True
        self.samples.clear()

        # Establish baseline
        self.baseline_python_mb = self._get_python_memory_mb()
        self.baseline_gpu_mb = self._get_gpu_memory_mb()
        self.last_python_mb = self.baseline_python_mb
        self.last_gpu_mb = self.baseline_gpu_mb

    def stop_monitoring(self):
        """Stop memory tracking"""
        self.monitoring = False
        tracemalloc.stop()

    def sample(self, frame: int):
        """Record memory snapshot for current frame"""
        if not self.monitoring:
            return

        python_mb = self._get_python_memory_mb()
        gpu_mb = self._get_gpu_memory_mb()

        delta_python = python_mb - (self.last_python_mb or python_mb)
        delta_gpu = (gpu_mb - self.last_gpu_mb) if (gpu_mb and self.last_gpu_mb) else None

        sample = MemorySample(
            frame=frame,
            timestamp=time.time(),
            python_mb=python_mb,
            gpu_mb=gpu_mb,
            delta_python_mb=delta_python,
            delta_gpu_mb=delta_gpu
        )

        self.samples.append(sample)
        self.last_python_mb = python_mb
        self.last_gpu_mb = gpu_mb

    def get_summary(self) -> Dict:
        """Generate summary statistics"""
        if not self.samples:
            return {"error": "No samples collected"}

        python_values = [s.python_mb for s in self.samples]

        return {
            "total_samples": len(self.samples),
            "duration_frames": self.samples[-1].frame if self.samples else 0,
            "python_memory": {
                "baseline_mb": self.baseline_python_mb,
                "current_mb": python_values[-1],
                "peak_mb": max(python_values),
                "growth_mb": python_values[-1] - self.baseline_python_mb,
            },
            "potential_leak": self._detect_leak()
        }

    def export_to_json(self, filepath: str):
        """Export all samples to JSON file"""
        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        data = {
            "metadata": {
                "exported_at": datetime.now().isoformat(),
                "total_samples": len(self.samples)
            },
            "summary": self.get_summary(),
            "samples": [asdict(s) for s in self.samples]
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def _get_python_memory_mb(self) -> float:
        """Get current Python process memory in MB"""
        return self.process.memory_info().rss / 1024 / 1024

    def _get_gpu_memory_mb(self) -> Optional[float]:
        """Get GPU memory usage if available"""
        try:
            import torch
            if torch.cuda.is_available():
                return torch.cuda.memory_allocated() / 1024 / 1024
        except ImportError:
            pass
        return None

    def _detect_leak(self) -> bool:
        """Simple leak detection: consistent growth over time"""
        if len(self.samples) < 100:
            return False

        # Check if memory grows consistently in last 100 samples
        recent = self.samples[-100:]
        growth_count = sum(1 for s in recent if s.delta_python_mb > 0.1)

        return growth_count > 70  # More than 70% of samples show growth
