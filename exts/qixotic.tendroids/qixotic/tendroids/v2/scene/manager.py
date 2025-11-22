"""
V2 Scene Manager - High-level coordinator for tendroids and bubbles

Orchestrates scene creation, animation, and cleanup.
"""

import carb
import omni.usd
from pxr import UsdGeom

from .animation_controller import V2AnimationController
from .tendroid_factory import V2TendroidFactory
from ..core import V2WarpDeformer
from ..environment import SeaFloorController, get_height_at


class V2SceneManager:
  """
  High-level scene coordinator for V2 Tendroids.

  Manages tendroid creation, bubble system, and animation.
  """

  def __init__(self):
    """Initialize scene manager."""
    self.tendroids = []  # V2WarpTendroid instances
    self.tendroid_data = []  # Builder data dicts
    self.bubble_manager = None
    self.animation_controller = V2AnimationController()
    self._sea_floor_created = False

  def _ensure_sea_floor(self, stage):
    """Create sea floor if not present."""
    if not self._sea_floor_created and stage:
      try:
        SeaFloorController.create_sea_floor(stage)
        self._sea_floor_created = True
      except Exception as e:
        carb.log_error(f"[V2SceneManager] Sea floor failed: {e}")

  def _ensure_parent_prim(self, stage, path: str):
    """Ensure parent prim exists."""
    if not stage.GetPrimAtPath(path):
      UsdGeom.Xform.Define(stage, path)

  def create_tendroids(
    self,
    count: int = None,
    spawn_area: tuple = None,
    radius_range: tuple = None,
    radial_segments: int = 24,
    height_segments: int = 48
  ) -> bool:
    """
    Create multiple tendroids in the scene.

    Args:
        count: Number of tendroids (None = use config)
        spawn_area: (width, depth) spawn area (None = use config)
        radius_range: (min, max) radius (None = use config)
        radial_segments: Circumference resolution
        height_segments: Vertical resolution

    Returns:
        True if successful
    """
    try:
      ctx = omni.usd.get_context()
      if not ctx:
        carb.log_error("[V2SceneManager] No USD context")
        return False

      stage = ctx.get_stage()
      if not stage:
        carb.log_error("[V2SceneManager] No USD stage")
        return False

      # Setup scene
      self._ensure_sea_floor(stage)
      self._ensure_parent_prim(stage, "/World/Tendroids")

      # Clear existing
      self.clear_tendroids(stage)

      # Create tendroid geometry via factory
      self.tendroid_data = V2TendroidFactory.create_batch(
        stage=stage,
        count=count,
        spawn_area=spawn_area,
        radius_range=radius_range,
        radial_segments=radial_segments,
        height_segments=height_segments,
        get_height_fn=get_height_at
      )

      # Create V2WarpTendroid instances from data
      self.tendroids = []
      for data in self.tendroid_data:
        tendroid = self._create_warp_tendroid(stage, data)
        if tendroid:
          self.tendroids.append(tendroid)

      # Setup animation controller
      self.animation_controller.set_tendroids(
        self.tendroids,
        self.tendroid_data
      )

      carb.log_info(
        f"[V2SceneManager] Created {len(self.tendroids)} tendroids"
      )
      return True

    except Exception as e:
      carb.log_error(f"[V2SceneManager] Create failed: {e}")
      import traceback
      traceback.print_exc()
      return False

  def _create_warp_tendroid(self, stage, data: dict):
    """
    Create V2WarpTendroid from builder data.

    Reuses existing mesh prim, just creates deformer.
    """
    try:
      # Create Warp deformer for existing mesh
      deformer = V2WarpDeformer(
        base_points_list=data['base_points'],
        cylinder_radius=data['radius'],
        max_amplitude=data.get('max_amplitude', 0.8),
        bulge_width=data.get('bulge_width', 0.9)
      )

      # Create lightweight wrapper
      tendroid = _V2TendroidWrapper(
        name=data['name'],
        position=data['position'],
        radius=data['radius'],
        length=data['length'],
        mesh_prim=data['mesh_prim'],
        deformer=deformer,
        deform_start_height=data['deform_start_height']
      )

      return tendroid

    except Exception as e:
      carb.log_error(
        f"[V2SceneManager] Warp tendroid failed for {data['name']}: {e}"
      )
      return None

  def create_single_tendroid(
    self,
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    radial_segments: int = 24,
    height_segments: int = 48
  ) -> bool:
    """Create a single tendroid at specified position."""
    try:
      ctx = omni.usd.get_context()
      if not ctx:
        return False

      stage = ctx.get_stage()
      if not stage:
        return False

      self._ensure_sea_floor(stage)
      self._ensure_parent_prim(stage, "/World/Tendroids")
      self.clear_tendroids(stage)

      from ..builders import V2TendroidBuilder
      data = V2TendroidBuilder.create_tendroid(
        stage=stage,
        name="Tendroid_Single",
        position=position,
        radius=radius,
        length=length,
        radial_segments=radial_segments,
        height_segments=height_segments,
        get_height_fn=get_height_at
      )

      if data:
        self.tendroid_data = [data]
        tendroid = self._create_warp_tendroid(stage, data)
        if tendroid:
          self.tendroids = [tendroid]
          self.animation_controller.set_tendroids(
            self.tendroids,
            self.tendroid_data
          )
          return True

      return False

    except Exception as e:
      carb.log_error(f"[V2SceneManager] Single create failed: {e}")
      return False

  def start_animation(self, enable_profiling: bool = False):
    """Start animation loop."""
    self.animation_controller.start(enable_profiling=enable_profiling)

  def stop_animation(self):
    """Stop animation loop."""
    self.animation_controller.stop()

  def clear_tendroids(self, stage=None):
    """Remove all tendroids from scene."""
    if not stage:
      ctx = omni.usd.get_context()
      if ctx:
        stage = ctx.get_stage()

    if stage:
      for data in self.tendroid_data:
        base_path = data.get('base_path')
        if base_path:
          prim = stage.GetPrimAtPath(base_path)
          if prim.IsValid():
            stage.RemovePrim(base_path)

    # Cleanup deformers
    for tendroid in self.tendroids:
      if hasattr(tendroid, 'deformer') and tendroid.deformer:
        tendroid.deformer.destroy()

    self.tendroids.clear()
    self.tendroid_data.clear()
    self.animation_controller.set_tendroids([], [])

  def get_tendroid_count(self) -> int:
    """Get active tendroid count."""
    return len(self.tendroids)

  def get_profile_data(self):
    """Get profiling data from animation controller."""
    return self.animation_controller.get_profile_data()

  def shutdown(self):
    """Cleanup on shutdown."""
    self.animation_controller.shutdown()
    ctx = omni.usd.get_context()
    if ctx:
      stage = ctx.get_stage()
      if stage:
        self.clear_tendroids(stage)


class _V2TendroidWrapper:
  """
  Lightweight wrapper for V2 tendroid with Warp deformer.

  Wraps existing USD mesh with deformation capability.
  """

  def __init__(
    self,
    name: str,
    position: tuple,
    radius: float,
    length: float,
    mesh_prim,
    deformer,
    deform_start_height: float
  ):
    self.name = name
    self.position = position
    self.radius = radius
    self.length = length
    self.mesh_prim = mesh_prim
    self.deformer = deformer
    self.deform_start_height = deform_start_height
    self.points_attr = mesh_prim.GetPointsAttr() if mesh_prim else None

  def apply_deformation(self, bubble_y: float, bubble_radius: float):
    """Apply bubble-guided deformation."""
    if not self.deformer or not self.points_attr:
      return

    new_points = self.deformer.deform(bubble_y, bubble_radius)
    if new_points is not None:
      self.points_attr.Set(new_points)

  def get_top_position(self) -> tuple:
    """Get world position of tendroid top."""
    return (
      self.position[0],
      self.position[1] + self.length,
      self.position[2]
    )
