"""
C++ Batch Test Controller

Runs batch tests using C++ accelerated vertex computation.
"""

import carb
import omni.usd
import omni.kit.app
from pxr import Usd, UsdGeom, Sdf

from .geometry_builder import create_simple_cylinder
from .cpp_batch_updater import CppBatchMeshUpdater
from .memory_monitor import MemoryMonitor
from .test_scenarios import TestPhase, BATCH_15_CPP_SCENARIO


class CppBatchTestController:
    """Controller for C++ accelerated batch tests"""
    
    def __init__(self):
        self.running = False
        self.current_frame = 0
        self.max_frames = BATCH_15_CPP_SCENARIO.max_frames
        self.cpp_updater = None
        self.memory_monitor = MemoryMonitor()
        self._update_subscription = None
        self.mesh_paths = []
        
        carb.log_info("[CppBatchTestController] Initialized")
    
    def start_test(self):
        """Start C++ batch test"""
        if self.running:
            carb.log_warn("[CppBatchTestController] Test already running")
            return
        
        carb.log_info("[CppBatchTestController] Starting C++ Batch 15 test")
        
        # Get stage
        context = omni.usd.get_context()
        stage = context.get_stage()
        
        if not stage:
            carb.log_error("[CppBatchTestController] No stage available")
            return
        
        # Create test scene
        self._create_scene(stage)
        
        # Initialize C++ updater
        try:
            self.cpp_updater = CppBatchMeshUpdater()
            success = self.cpp_updater.register_meshes(stage, self.mesh_paths)
            
            if not success:
                carb.log_error("[CppBatchTestController] Failed to register meshes")
                return
            
            carb.log_info(f"[CppBatchTestController] Registered {len(self.mesh_paths)} meshes")
            
        except Exception as e:
            carb.log_error(f"[CppBatchTestController] C++ updater failed: {e}")
            import traceback
            traceback.print_exc()
            return
        
        # Reset state
        self.current_frame = 0
        self.running = True
        self.memory_monitor.reset()
        
        # Start update loop
        app = omni.kit.app.get_app()
        update_stream = app.get_update_event_stream()
        self._update_subscription = update_stream.create_subscription_to_pop(
            self._on_update,
            name="cpp_batch_test_update"
        )
        
        carb.log_info("[CppBatchTestController] Test started")
    
    def _create_scene(self, stage):
        """Create test scene with 15 tubes"""
        # Clean up existing test
        test_prim = stage.GetPrimAtPath("/World/CppBatchTest")
        if test_prim.IsValid():
            stage.RemovePrim("/World/CppBatchTest")
        
        # Create parent
        test_xform = UsdGeom.Xform.Define(stage, "/World/CppBatchTest")
        
        # Create 15 tubes in a grid (3x5)
        self.mesh_paths = []
        scenario = BATCH_15_CPP_SCENARIO
        
        grid_cols = 5
        spacing = 3.0
        
        for i in range(scenario.cylinder_count):
            row = i // grid_cols
            col = i % grid_cols
            
            x = col * spacing - (grid_cols - 1) * spacing / 2
            z = row * spacing
            
            mesh_path = f"/World/CppBatchTest/Tube_{i:02d}"
            
            create_simple_cylinder(
                stage,
                mesh_path,
                segments=scenario.segments,
                radial_segments=scenario.radial_segments,
                radius=0.5,
                height=8.0,
                position=(x, 4.0, z)
            )
            
            self.mesh_paths.append(mesh_path)
        
        carb.log_info(f"[CppBatchTestController] Created {len(self.mesh_paths)} tubes")
    
    def _on_update(self, event):
        """Update loop for animation"""
        if not self.running:
            return
        
        # Check frame limit
        if self.current_frame >= self.max_frames:
            self.stop_test()
            return
        
        # Update animation using C++
        time = self.current_frame * 0.016  # ~60fps timing
        
        try:
            self.cpp_updater.update(
                time=time,
                wave_speed=2.0,
                amplitude=0.15,
                frequency=0.8
            )
        except Exception as e:
            carb.log_error(f"[CppBatchTestController] Update failed: {e}")
            self.stop_test()
            return
        
        # Memory sampling
        if self.current_frame % 10 == 0:
            self.memory_monitor.sample(self.current_frame)
        
        self.current_frame += 1
        
        # Progress logging
        if self.current_frame % 60 == 0:
            stats = self.cpp_updater.get_stats()
            carb.log_info(
                f"[CppBatchTestController] Frame {self.current_frame}: "
                f"C++ avg {stats['avg_time_ms']:.3f}ms per update"
            )
    
    def stop_test(self):
        """Stop test and cleanup"""
        if not self.running:
            return
        
        self.running = False
        
        if self._update_subscription:
            self._update_subscription.unsubscribe()
            self._update_subscription = None
        
        # Get final stats
        duration_s = self.current_frame / 60.0  # Assuming 60fps target
        avg_fps = self.current_frame / duration_s if duration_s > 0 else 0
        
        memory_summary = self.memory_monitor.analyze()
        
        if self.cpp_updater:
            cpp_stats = self.cpp_updater.get_stats()
            
            carb.log_info("[CppBatchTestController] Test complete:")
            carb.log_info(f"  Frames: {self.current_frame}")
            carb.log_info(f"  Duration: {duration_s:.1f}s")
            carb.log_info(f"  Avg FPS: {avg_fps:.1f}")
            carb.log_info(f"  C++ Updates: {cpp_stats['total_calls']}")
            carb.log_info(f"  C++ Avg Time: {cpp_stats['avg_time_ms']:.3f}ms")
            carb.log_info(f"  Total Vertices: {cpp_stats['total_vertices']}")
        
        carb.log_info(f"[CppBatchTestController] {memory_summary}")
        
        return {
            'frames': self.current_frame,
            'duration_s': duration_s,
            'avg_fps': avg_fps,
            'memory': memory_summary,
            'cpp_stats': self.cpp_updater.get_stats() if self.cpp_updater else None
        }
