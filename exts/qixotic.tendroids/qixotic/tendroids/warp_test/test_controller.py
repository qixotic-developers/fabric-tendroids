"""
Test Controller

Main controller for Warp test harness. Orchestrates test execution,
geometry creation, kernel application, and memory monitoring.
"""

import time
from typing import List, Optional

import carb
import omni.ext
import omni.usd
from pxr import Gf, Sdf, Usd, UsdGeom, Vt

from .geometry_builder import GeometryBuilder
from .memory_monitor import MemoryMonitor
from .test_scenarios import TestPhase, TestScenario, TestScenarioManager
from .warp_kernels import WarpKernelManager


class WarpTestController:
  """Main controller for Warp deformation testing"""

  def __init__(self):
    self.memory_monitor = MemoryMonitor()
    self.warp_manager = WarpKernelManager()
    self.scenario_manager = TestScenarioManager()

    self.running = False
    self.current_frame = 0
    self.start_time = 0.0
    self.test_cylinders: List = []
    self.test_root_path = "/World/WarpTest"
    self.outer_vertex_count = 0

    self._subscription = None
    self.geometry_builder = None

  def _get_stage(self) -> Optional[Usd.Stage]:
    """Get current USD stage"""
    usd_context = omni.usd.get_context()
    return usd_context.get_stage()

  def start_test(self, phase: TestPhase):
    """Initialize and start a test phase"""
    if self.running:
      carb.log_warn("Test already running")
      return

    # Get stage
    stage = self._get_stage()
    if not stage:
      carb.log_error("No stage available")
      raise RuntimeError("No USD stage available. Please create or open a stage first.")

    # Initialize geometry builder with current stage
    self.geometry_builder = GeometryBuilder(stage)

    scenario = self.scenario_manager.get_scenario(phase)
    self.scenario_manager.set_current(phase)

    carb.log_info(f"Starting test: {scenario.name}")

    # Special warnings
    if phase == TestPhase.PHASE_6A:
      carb.log_info("🔬 Phase 6a: Static double-wall glass test")
      carb.log_info("🔬 NO deformation - testing if geometry itself is valid")
      carb.log_info("🔬 Enable path tracing to see glass rendering")

    # Clean up any existing test geometry
    self._cleanup_geometry()

    # Create test geometry
    self._create_test_geometry(scenario)

    # Initialize Warp buffers (but won't use if static)
    if not scenario.static_test:
      self._initialize_warp_buffers()

    # Start monitoring
    self.memory_monitor.start_monitoring()
    self.running = True
    self.current_frame = 0
    self.start_time = time.time()

    # Subscribe to update events
    update_stream = omni.kit.app.get_app().get_update_event_stream()
    self._subscription = update_stream.create_subscription_to_pop(
      self._on_update, name="warp_test_update"
    )

  def stop_test(self):
    """Stop the current test and generate report"""
    if not self.running:
      return

    self.running = False
    self.memory_monitor.stop_monitoring()

    # Unsubscribe from updates
    if self._subscription:
      self._subscription.unsubscribe()
      self._subscription = None

    # Generate report
    summary = self.memory_monitor.get_summary()
    carb.log_info(f"Test completed: {summary}")

    # Export detailed results
    from . import MEMORY_LOG_PATH
    self.memory_monitor.export_to_json(MEMORY_LOG_PATH)

    return summary

  def _on_update(self, event):
    """Update callback - execute deformation and monitor memory"""
    if not self.running:
      return

    scenario = self.scenario_manager.get_current()
    if not scenario:
      return

    # Check if test should stop
    if self.current_frame >= scenario.max_frames:
      self.stop_test()
      return

    # Skip deformation if static test
    if not scenario.static_test:
      # Apply deformation kernel
      elapsed = time.time() - self.start_time
      self._apply_deformation(scenario, elapsed)

      # Update USD geometry
      self._update_geometry()

    # Sample memory periodically
    from . import MEMORY_SAMPLE_INTERVAL
    if self.current_frame % MEMORY_SAMPLE_INTERVAL == 0:
      self.memory_monitor.sample(self.current_frame)

    self.current_frame += 1

  def _create_test_geometry(self, scenario: TestScenario):
    """Create geometry for test scenario"""
    stage = self._get_stage()
    if not stage:
      return

    # Ensure root exists
    if not stage.GetPrimAtPath(self.test_root_path):
      UsdGeom.Xform.Define(stage, self.test_root_path)

    if scenario.cylinder_count == 1:
      # Single cylinder - check if double-wall needed
      if scenario.use_double_wall:
        mesh, positions, outer_count = self.geometry_builder.create_double_wall_cylinder(
          f"{self.test_root_path}/test_cylinder_double",
          segments=scenario.segments,
          radial_segments=scenario.radial_segments,
          outer_radius=0.5,
          inner_radius=0.45
        )
        self.outer_vertex_count = outer_count
        self.test_cylinders = [(mesh, positions, outer_count)]
      else:
        mesh, positions = self.geometry_builder.create_test_cylinder(
          f"{self.test_root_path}/test_cylinder",
          segments=scenario.segments,
          radial_segments=scenario.radial_segments
        )
        self.outer_vertex_count = 0
        self.test_cylinders = [(mesh, positions, 0)]
    else:
      # Multiple cylinders
      cylinders = self.geometry_builder.create_multiple_cylinders(
        self.test_root_path,
        scenario.cylinder_count,
        spacing=3.0
      )
      self.outer_vertex_count = 0
      self.test_cylinders = [(m, p, 0) for m, p in cylinders]

    # Apply materials if needed
    if scenario.use_materials:
      for mesh, _, _ in self.test_cylinders:
        if scenario.use_transparency:
          # Glass material
          self.geometry_builder.apply_glass_material(mesh, ior=1.5)
        else:
          # Opaque material
          self.geometry_builder.apply_simple_material(mesh)

  def _initialize_warp_buffers(self):
    """Initialize Warp buffers for first cylinder"""
    if not self.test_cylinders:
      return

    _, positions, outer_count = self.test_cylinders[0]

    # For double-wall, only deform outer vertices
    if outer_count > 0:
      # Extract just the outer vertices for Warp
      outer_positions = positions[:outer_count]
      self.warp_manager.initialize_buffers(outer_count, outer_positions)
    else:
      # Single-wall: use all vertices
      vertex_count = len(positions)
      self.warp_manager.initialize_buffers(vertex_count, positions)

  def _apply_deformation(self, scenario: TestScenario, time: float):
    """Apply appropriate kernel based on scenario"""
    if scenario.kernel_type == "sine_wave":
      self.warp_manager.apply_sine_wave(time)
    elif scenario.kernel_type == "radial_pulse":
      self.warp_manager.apply_radial_pulse(time)
    elif scenario.kernel_type == "breathing_wave":
      self.warp_manager.apply_breathing_wave(time)

  def _update_geometry(self):
    """Update USD mesh with deformed positions"""
    new_positions = self.warp_manager.get_positions()

    if not self.test_cylinders:
      return

    mesh, original_positions, outer_count = self.test_cylinders[0]
    points_attr = mesh.GetPointsAttr()

    if outer_count > 0:
      # Double-wall: deform both outer AND inner vertices
      # Create combined VtArray with proper Gf.Vec3f types
      combined = Vt.Vec3fArray(outer_count * 2)

      # Set outer vertices from Warp (convert numpy.float32 to Python float)
      for i in range(outer_count):
        combined[i] = Gf.Vec3f(float(new_positions[i][0]), float(new_positions[i][1]), float(new_positions[i][2]))

      # Create inner vertices scaled from outer
      scale_factor = 0.45 / 0.5
      for i in range(outer_count):
        inner_x = float(new_positions[i][0]) * scale_factor
        inner_y = float(new_positions[i][1])
        inner_z = float(new_positions[i][2]) * scale_factor
        combined[outer_count + i] = Gf.Vec3f(inner_x, inner_y, inner_z)

      points_attr.Set(combined)
    else:
      # Single-wall: convert numpy array to proper VtArray
      vt_positions = Vt.Vec3fArray(len(new_positions))
      for i in range(len(new_positions)):
        vt_positions[i] = Gf.Vec3f(float(new_positions[i][0]), float(new_positions[i][1]), float(new_positions[i][2]))
      points_attr.Set(vt_positions)

  def _cleanup_geometry(self):
    """Remove test geometry from stage"""
    stage = self._get_stage()
    if stage and stage.GetPrimAtPath(self.test_root_path):
      stage.RemovePrim(self.test_root_path)
    self.test_cylinders.clear()
    self.warp_manager.cleanup()
    self.outer_vertex_count = 0
