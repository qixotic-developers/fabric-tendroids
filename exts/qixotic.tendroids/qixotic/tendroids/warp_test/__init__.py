"""
Warp Test Harness Module

Isolated testing environment for Warp-based vertex deformation.
Includes both original diagnostic tests and new batch processing tests.

Original Test Phases:
    Phase 1: Single cylinder with basic sine wave deformation
    Phase 2: Multiple cylinders with varying update frequencies
    Phase 3: Add materials (opaque -> transparent) and path tracing
    Phase 6: Glass material tests (static and dynamic)

Batch Processing Tests:
    Batch 15: Production target - 15 uniform tubes with shared geometry
    Batch 30: Stress test - 2x production load
    Batch 50: Maximum capacity test

Usage:
    from qixotic.tendroids.warp_test import WarpTestController, BatchTestController
    
    # Original tests
    controller = WarpTestController()
    controller.start_test(phase=TestPhase.PHASE_1)
    
    # Batch tests
    batch_controller = BatchTestController()
    batch_controller.start_test(BatchTestPhase.BATCH_15_TUBES)
"""

from .test_controller import WarpTestController
from .test_window import WarpTestWindow
from .memory_monitor import MemoryMonitor
from .batch_test_controller import BatchTestController
from .batch_geometry_builder import BatchGeometryBuilder
from .batch_deformer import BatchDeformer
from .batch_animation_helper import BatchAnimationHelper
from .test_batch_scenario import BatchTestPhase, BatchScenarioManager

__all__ = [
  'WarpTestController',
  'WarpTestWindow',
  'MemoryMonitor',
  'BatchTestController',
  'BatchGeometryBuilder',
  'BatchDeformer',
  'BatchAnimationHelper',
  'BatchTestPhase',
  'BatchScenarioManager'
]

# Module-level configuration
DEFAULT_TEST_PHASE = 1
MAX_TEST_DURATION_FRAMES = 10000
MEMORY_SAMPLE_INTERVAL = 10  # frames between memory samples

# Diagnostic output paths
MEMORY_LOG_PATH = "C:/Dev/Omniverse/fabric-tendroids/logs/warp_test_memory.log"
PROFILE_OUTPUT_PATH = "C:/Dev/Omniverse/fabric-tendroids/logs/warp_test_profile.json"
