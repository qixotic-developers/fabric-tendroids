"""
Batch Test Controller

Controller for batch processing tests.
Manages shared geometry, batch deformation, and performance measurement.
Uses Fabric API for high-performance mesh updates.
"""

import time
import random
import math
import carb
import omni.kit.app
import omni.usd
from pxr import Gf, UsdGeom, Vt

from .batch_geometry_builder import BatchGeometryBuilder
from .batch_deformer import BatchDeformer
from .batch_animation_helper import BatchAnimationHelper
from .test_batch_scenario import BatchTestPhase, BatchScenarioManager
from .memory_monitor import MemoryMonitor

# Force reload of fabric updater to get latest code
import importlib
from . import fabric_batch_updater
importlib.reload(fabric_batch_updater)
from .fabric_batch_updater import FabricBatchMeshUpdater

carb.log_info("[BatchTestController] Imported FabricBatchMeshUpdater")


class BatchTestController:
  """
  Controller for batch processing tests.
  
  Demonstrates single-kernel approach for multiple identical-diameter tubes
  with Fabric-based updates for maximum performance.
  """
  
  def __init__(self):
    """Initialize batch test controller"""
    self.scenario_manager = BatchScenarioManager()
    self.memory_monitor = MemoryMonitor()
    
    self.running = False
    self.current_frame = 0
    self.start_time = 0.0
    
    # Components
    self.geometry_builder = None
    self.batch_deformer = None
    self.animation_helper = None
    self.fabric_updater = None
    
    # Scene data
    self.tube_meshes = []  # List of mesh prims
    self.tube_paths = []  # Paths for Fabric registration
    self.shared_positions = None
    self.vertex_count = 0
    
    # Performance tracking
    self.min_frame_time = float('inf')
    self.max_frame_time = 0.0
    self.total_frame_time = 0.0
    
    self._subscription = None
  
  def _get_stage(self):
    """Get current USD stage"""
    usd_context = omni.usd.get_context()
    return usd_context.get_stage()
  
  def start_test(self, phase: BatchTestPhase):
    """Start batch processing test"""
    if self.running:
      carb.log_warn("[BatchTestController] Test already running")
      return
    
    stage = self._get_stage()
    if not stage:
      carb.log_error("[BatchTestController] No USD stage available")
      return
    
    scenario = self.scenario_manager.get_scenario(phase)
    self.scenario_manager.set_current(phase)
    
    carb.log_info(f"[BatchTestController] Starting: {scenario.name}")
    carb.log_info(f"[BatchTestController] {scenario.tube_count} tubes, target {scenario.target_fps} fps")
    
    # Initialize components
    self.geometry_builder = BatchGeometryBuilder(stage)
    
    # Clean up existing geometry first
    self._cleanup_geometry()
    
    # Initialize Fabric updater AFTER cleanup
    try:
      self.fabric_updater = FabricBatchMeshUpdater()
      if not self.fabric_updater.is_fabric_available():
        carb.log_warn("[BatchTestController] Fabric not available, using standard USD updates")
        self.fabric_updater = None
    except Exception as e:
      carb.log_error(f"[BatchTestController] Failed to initialize Fabric updater: {e}")
      self.fabric_updater = None
    
    # Create tube meshes
    self._create_tube_meshes(scenario)
    
    # Register meshes with Fabric updater
    if self.fabric_updater and self.fabric_updater.is_fabric_available():
      for path in self.tube_paths:
        self.fabric_updater.register_mesh(path)
      carb.log_info(f"[BatchTestController] Registered {len(self.tube_paths)} meshes with Fabric")
    
    # Initialize batch deformer
    self._initialize_batch_deformer(scenario)
    
    # Initialize animation
    self._initialize_animation(scenario)
    
    # Start monitoring
    self.memory_monitor.start_monitoring()
    self.running = True
    self.current_frame = 0
    self.start_time = time.time()
    
    # Subscribe to updates
    update_stream = omni.kit.app.get_app().get_update_event_stream()
    self._subscription = update_stream.create_subscription_to_pop(
      self._on_update,
      name="batch_test_update"
    )
    
    carb.log_info("[BatchTestController] Test started")
  
  def stop_test(self):
    """Stop test and generate report"""
    if not self.running:
      return
    
    self.running = False
    self.memory_monitor.stop_monitoring()
    
    if self._subscription:
      self._subscription.unsubscribe()
      self._subscription = None
    
    # Generate report
    elapsed = time.time() - self.start_time
    avg_fps = self.current_frame / elapsed if elapsed > 0 else 0
    avg_frame_ms = self.total_frame_time / self.current_frame if self.current_frame > 0 else 0
    max_fps = 1000.0 / self.min_frame_time if self.min_frame_time > 0 else 0
    min_fps = 1000.0 / self.max_frame_time if self.max_frame_time > 0 else 0
    
    summary = self.memory_monitor.get_summary()
    carb.log_info(
      f"[BatchTestController] Test complete: "
      f"{self.current_frame} frames in {elapsed:.1f}s\n"
      f"  Avg: {avg_fps:.1f} fps ({avg_frame_ms:.2f}ms/frame)\n"
      f"  Min: {min_fps:.1f} fps ({self.max_frame_time:.2f}ms)\n"
      f"  Max: {max_fps:.1f} fps ({self.min_frame_time:.2f}ms)"
    )
    carb.log_info(f"[BatchTestController] {summary}")
    
    return summary
  
  def _create_tube_meshes(self, scenario):
    """Create separate mesh for each tube at different positions"""
    global x, z
    width, depth = scenario.spawn_area
    spacing = scenario.tube_radius * 4.0  # 2x diameter spacing
    
    positions = []
    
    # Create base geometry once to get vertex data
    temp_path = "/World/BatchTest/TempBase"
    _, base_positions, vertex_count = self.geometry_builder.create_shared_tube(
      path=temp_path,
      height=scenario.tube_height,
      radius=scenario.tube_radius,
      height_segments=scenario.height_segments,
      radial_segments=scenario.radial_segments
    )
    
    self.shared_positions = base_positions
    self.vertex_count = vertex_count
    
    # Now create individual tubes at different locations
    stage = self._get_stage()
    
    for i in range(scenario.tube_count):
      # Random position with interference checking
      placed = False
      attempts = 0
      
      while not placed and attempts < 100:
        x = random.uniform(-width / 2, width / 2)
        z = random.uniform(-depth / 2, depth / 2)
        
        # Check interference
        valid = True
        for px, pz in positions:
          dist = math.sqrt((x - px) ** 2 + (z - pz) ** 2)
          if dist < spacing:
            valid = False
            break
        
        if valid:
          positions.append((x, z))
          placed = True
        
        attempts += 1
      
      if not placed:
        carb.log_warn(f"[BatchTestController] Could not place tube {i}")
        continue
      
      # Create actual mesh at this position
      tube_path = f"/World/BatchTest/Tube_{i:02d}"
      mesh_prim, _, _ = self.geometry_builder.create_shared_tube(
        path=tube_path,
        height=scenario.tube_height,
        radius=scenario.tube_radius,
        height_segments=scenario.height_segments,
        radial_segments=scenario.radial_segments
      )
      
      # Position the mesh
      mesh = UsdGeom.Mesh(mesh_prim)
      xform = UsdGeom.Xformable(mesh_prim)
      xform.AddTranslateOp().Set(Gf.Vec3d(x, 0, z))
      
      self.tube_meshes.append(mesh)
      self.tube_paths.append(tube_path)
    
    # Remove temp base
    if stage.GetPrimAtPath(temp_path):
      stage.RemovePrim(temp_path)
    
    carb.log_info(
      f"[BatchTestController] Created {len(self.tube_meshes)} tube meshes, "
      f"{vertex_count} vertices each"
    )
  
  def _initialize_batch_deformer(self, scenario):
    """Initialize batch GPU deformer"""
    self.batch_deformer = BatchDeformer(
      tube_count=len(self.tube_meshes),
      vertices_per_tube=self.vertex_count,
      base_positions=self.shared_positions,
      deform_start_height=scenario.tube_height * 0.15  # After flare
    )
  
  def _initialize_animation(self, scenario):
    """Initialize animation helper"""
    self.animation_helper = BatchAnimationHelper(
      tube_count=len(self.tube_meshes),
      tube_height=scenario.tube_height
    )
    
    self.animation_helper.create_animations(
      vary_parameters=scenario.vary_parameters,
      stagger_start=scenario.stagger_start
    )
  
  def _on_update(self, event):
    """Update callback - batch deformation"""
    if not self.running:
      return
    
    scenario = self.scenario_manager.get_current()
    if not scenario:
      return
    
    # Check if test should stop
    if self.current_frame >= scenario.max_frames:
      self.stop_test()
      return
    
    # TIMING: Track where time is spent
    import time as time_module
    frame_start = time_module.perf_counter()
    
    # Update animation timing
    dt = 1.0 / 60.0  # Assume 60fps
    self.animation_helper.update(dt)
    anim_time = time_module.perf_counter() - frame_start
    
    # Get wave parameters for all tubes
    wave_centers, amplitudes, bulge_lengths, active_flags = \
      self.animation_helper.get_wave_parameters()
    params_time = time_module.perf_counter() - frame_start - anim_time
    
    # Single batch deformation
    deform_start = time_module.perf_counter()
    deformed_vertices = self.batch_deformer.update(
      wave_centers=wave_centers,
      amplitudes=amplitudes,
      bulge_lengths=bulge_lengths,
      active_flags=active_flags
    )
    deform_time = time_module.perf_counter() - deform_start
    
    # Update meshes (Fabric or standard USD)
    update_start = time_module.perf_counter()
    if self.fabric_updater and self.fabric_updater.is_fabric_available():
      # HIGH PERFORMANCE: Fabric batch update with GPU array
      self.fabric_updater.batch_update_vertices_gpu(deformed_vertices, self.vertex_count)
    else:
      # FALLBACK: Standard USD updates (need to convert GPU array)
      self._update_tube_meshes_usd(deformed_vertices)
    update_time = time_module.perf_counter() - update_start
    
    frame_time = time_module.perf_counter() - frame_start
    
    # Track performance
    self.min_frame_time = min(self.min_frame_time, frame_time * 1000)
    self.max_frame_time = max(self.max_frame_time, frame_time * 1000)
    self.total_frame_time += frame_time * 1000
    
    # Log timing every 120 frames (less spam)
    if self.current_frame % 120 == 0 and self.current_frame > 0:
      avg_ms = self.total_frame_time / self.current_frame
      carb.log_info(
        f"[BatchTestController] Frame {self.current_frame}: "
        f"deform={deform_time*1000:.2f}ms, update={update_time*1000:.2f}ms, "
        f"total={frame_time*1000:.2f}ms (avg={avg_ms:.2f}ms, min={self.min_frame_time:.2f}ms)"
      )
    
    # Sample memory periodically
    from . import MEMORY_SAMPLE_INTERVAL
    if self.current_frame % MEMORY_SAMPLE_INTERVAL == 0:
      self.memory_monitor.sample(self.current_frame)
    
    self.current_frame += 1
  
  def _update_tube_meshes_usd(self, warp_array):
    """Fallback: Update USD meshes with standard API"""
    from pxr import Gf, Vt
    
    # Convert GPU array to CPU
    all_vertices_cpu = warp_array.numpy()
    
    # Convert to Gf.Vec3f
    all_vertices = [Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) for v in all_vertices_cpu]
    
    for i, mesh in enumerate(self.tube_meshes):
      start_idx = i * self.vertex_count
      end_idx = start_idx + self.vertex_count
      
      tube_vertices = all_vertices[start_idx:end_idx]
      mesh.GetPointsAttr().Set(Vt.Vec3fArray(tube_vertices))
  
  def _cleanup_geometry(self):
    """Remove test geometry"""
    stage = self._get_stage()
    if not stage:
      return
    
    root_path = "/World/BatchTest"
    if stage.GetPrimAtPath(root_path):
      stage.RemovePrim(root_path)
    
    self.tube_meshes.clear()
    self.tube_paths.clear()
    self.shared_positions = None
    
    if self.batch_deformer:
      self.batch_deformer.cleanup()
      self.batch_deformer = None
    
    if self.fabric_updater:
      self.fabric_updater.cleanup()
      self.fabric_updater = None
