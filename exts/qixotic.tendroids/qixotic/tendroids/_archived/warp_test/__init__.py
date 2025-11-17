"""
Warp Test Harness Module

Production C++ + Fabric batch testing system.
Achieves ~50 fps with 15 Tendroids using hybrid approach.

Current Production System:
    - cpp_batch_updater: C++ computation + Fabric updates
    - cpp_batch_test_controller: Test harness with timing
    - geometry_builder: Utility functions
    - tube_geometry_helper: Future swept torus support
    - memory_monitor: Performance monitoring
    - test_window: Simplified UI

Usage:
    from qixotic.tendroids.warp_test import WarpTestWindow
    
    # In extension startup
    self._test_window = WarpTestWindow()
"""

from .test_window import WarpTestWindow
from .memory_monitor import MemoryMonitor
from .cpp_batch_test_controller import CppBatchTestController
from .cpp_batch_updater import CppBatchMeshUpdater
from .geometry_builder import create_simple_cylinder

__all__ = [
    'WarpTestWindow',
    'MemoryMonitor',
    'CppBatchTestController',
    'CppBatchMeshUpdater',
    'create_simple_cylinder'
]

# Module-level configuration
MEMORY_SAMPLE_INTERVAL = 10  # frames between memory samples

# Diagnostic output paths
MEMORY_LOG_PATH = "C:/Dev/Omniverse/fabric-tendroids/logs/warp_test_memory.log"
