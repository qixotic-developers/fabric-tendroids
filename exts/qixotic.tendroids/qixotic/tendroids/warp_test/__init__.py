"""
Warp Test Harness Module

Isolated testing environment for Warp-based vertex deformation to diagnose memory issues.
Provides incremental testing phases from simple single-cylinder deformation to complex
multi-geometry scenarios with materials and transparency.

Test Phases:
    Phase 1: Single cylinder with basic sine wave deformation
    Phase 2: Multiple cylinders with varying update frequencies
    Phase 3: Add materials (opaque -> transparent) and path tracing

Usage:
    from qixotic.tendroids.warp_test import WarpTestController
    
    controller = WarpTestController()
    controller.start_test(phase=1)
    controller.stop_test()
"""

from .test_controller import WarpTestController
from .test_window import WarpTestWindow
from .memory_monitor import MemoryMonitor

__all__ = [
    'WarpTestController',
    'WarpTestWindow', 
    'MemoryMonitor'
]

# Module-level configuration
DEFAULT_TEST_PHASE = 1
MAX_TEST_DURATION_FRAMES = 10000
MEMORY_SAMPLE_INTERVAL = 10  # frames between memory samples

# Diagnostic output paths
MEMORY_LOG_PATH = "C:/Dev/Omniverse/fabric-tendroids/logs/warp_test_memory.log"
PROFILE_OUTPUT_PATH = "C:/Dev/Omniverse/fabric-tendroids/logs/warp_test_profile.json"
