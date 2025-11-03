"""
Core Tendroid class with Warp-based smooth vertex deformation

Manages a single Tendroid creature with GPU-accelerated breathing animation.
"""

import carb
import omni.usd
from pxr import Gf, UsdGeom, Vt
from .cylinder_generator import CylinderGenerator
from .warp_deformer import WarpDeformer
from ..animation.breathing import BreathingAnimator


class Tendroid:
  """
  A single Tendroid creature with smooth vertex deformation.

  Uses Warp for GPU-accelerated mesh deformation to create realistic
  breathing animation with a single traveling bulge effect.
  """

  def __init__(
    self,
    name: str,
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    num_segments: int = 32,
    radial_resolution: int = 16
  ):
    """
    Initialize Tendroid.

    Args:
        name: Unique identifier
        position: (x, y, z) world position
        radius: Cylinder radius
        length: Total length
        num_segments: Vertical resolution (higher = smoother)
        radial_resolution: Circumference resolution
    """
    self.name = name
    self.position = position
    self.radius = radius
    self.length = length
    self.num_segments = num_segments
    self.radial_resolution = radial_resolution

    # USD references
    self.base_path = None
    self.mesh_path = None
    self.mesh_prim = None

    # Deformation
    self.warp_deformer = None
    self.breathing_animator = None
    self.deform_start_height = 0.0

    # State
    self.is_created = False
    self.is_active = True

    carb.log_info(f"[Tendroid] Initialized '{name}' at {position}")

  def create(self, stage, parent_path: str = "/World/Tendroids") -> bool:
    """
    Create Tendroid geometry in USD stage.

    Args:
        stage: USD stage
        parent_path: Parent prim path

    Returns:
        Success status
    """
    try:
      # Create base Xform
      self.base_path = f"{parent_path}/{self.name}"
      base_xform = UsdGeom.Xform.Define(stage, self.base_path)
      base_xform.AddTranslateOp().Set(Gf.Vec3d(*self.position))

      # Create cylinder mesh with flared base
      self.mesh_path = f"{self.base_path}/mesh"
      mesh_prim, vertices, num_segs, rad_res, deform_start = \
        CylinderGenerator.create_tendroid_cylinder(
          stage=stage,
          path=self.mesh_path,
          radius=self.radius,
          length=self.length,
          num_segments=self.num_segments,
          radial_resolution=self.radial_resolution,
          flare_height_percent=15.0,
          flare_radius_multiplier=2.0
        )

      self.mesh_prim = mesh_prim
      self.deform_start_height = deform_start

      # Initialize Warp deformer
      self.warp_deformer = WarpDeformer(vertices, deform_start)

      # Initialize breathing animator with updated defaults
      self.breathing_animator = BreathingAnimator(
        length=self.length,
        deform_start_height=deform_start,
        wave_speed=40.0,
        bulge_length_percent=40.0,
        amplitude=0.35,
        cycle_delay=2.0
      )

      self.is_created = True
      carb.log_info(f"[Tendroid] Created '{self.name}' at {self.base_path}")
      return True

    except Exception as e:
      carb.log_error(f"[Tendroid] Failed to create '{self.name}': {e}")
      import traceback
      traceback.print_exc()
      return False

  def update(self, dt: float):
    """
    Update animation for current frame.

    Args:
        dt: Delta time (seconds)
    """
    if not self.is_created or not self.is_active:
      return

    try:
      # Get wave parameters
      wave_params = self.breathing_animator.update(dt)

      # Apply deformation if wave is active
      if wave_params['active']:
        deformed_vertices = self.warp_deformer.update(
          wave_center=wave_params['wave_center'],
          bulge_length=wave_params['bulge_length'],
          amplitude=wave_params['amplitude']
        )

        # Update mesh in USD
        self._update_mesh_vertices(deformed_vertices)

      # Check for bubble emission
      if self.breathing_animator.should_emit_bubble():
        self._emit_bubble()

    except Exception as e:
      carb.log_error(f"[Tendroid] Update failed for '{self.name}': {e}")

  def _update_mesh_vertices(self, vertices: list):
    """
    Write deformed vertices to USD mesh.

    Args:
        vertices: List of Gf.Vec3f positions
    """
    try:
      mesh = UsdGeom.Mesh(self.mesh_prim)
      points_attr = mesh.GetPointsAttr()
      points_attr.Set(Vt.Vec3fArray(vertices))
    except Exception as e:
      carb.log_warn(f"[Tendroid] Vertex update failed: {e}")

  def _emit_bubble(self):
    """Emit bubble from top (Phase 2 feature)."""
    carb.log_info(f"[Tendroid] '{self.name}' emitting bubble!")

  def set_active(self, active: bool):
    """Enable/disable animation."""
    self.is_active = active

  def set_breathing_parameters(self, **kwargs):
    """Update breathing animation parameters."""
    if self.breathing_animator:
      self.breathing_animator.set_parameters(**kwargs)

  def destroy(self, stage):
    """Remove from stage and cleanup resources."""
    if self.base_path:
      try:
        stage.RemovePrim(self.base_path)
        carb.log_info(f"[Tendroid] Destroyed '{self.name}'")
      except Exception as e:
        carb.log_error(f"[Tendroid] Destroy failed: {e}")

    if self.warp_deformer:
      self.warp_deformer.cleanup()

    self.is_created = False

  def get_top_position(self) -> tuple:
    """Get world position of top for bubble emission."""
    return (
      self.position[0],
      self.position[1] + self.length,
      self.position[2]
    )
