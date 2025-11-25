"""
V2 Tendroid Builder - Creates V2WarpTendroids with flared bases and terrain conforming

Handles USD geometry creation, terrain conforming, and Warp deformer initialization.
"""

import carb
from pxr import Gf, UsdGeom

from .cylinder_generator import CylinderGenerator
from .terrain_conform import conform_base_to_terrain
from ..config import get_config_value
from ..utils import apply_material


class V2TendroidBuilder:
  """
  Builder for creating V2 Tendroids with full production features.

  Creates flared-base cylinders that conform to terrain,
  with Warp GPU deformation support.
  """

  @staticmethod
  def create_tendroid(
    stage,
    name: str,
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    radial_segments: int = 24,
    height_segments: int = 48,
    flare_height_percent: float = None,
    flare_radius_multiplier: float = None,
    max_amplitude: float = 0.8,
    bulge_width: float = 0.9,
    parent_path: str = "/World/Tendroids",
    get_height_fn=None
    # ) -> GenericDict | None:
  ) -> typing.TypedDict | None:
    """
    Create a complete V2 tendroid with all features.

    Args:
        stage: USD stage
        name: Unique tendroid name
        position: (x, y, z) world position
        radius: Cylinder radius
        length: Total height
        radial_segments: Circumference resolution
        height_segments: Vertical resolution
        flare_height_percent: Flare height as % (default from config)
        flare_radius_multiplier: Base radius multiplier (default from config)
        max_amplitude: Maximum deformation amplitude
        bulge_width: Deformation bulge width
        parent_path: USD parent path
        get_height_fn: Terrain height query function

    Returns:
        Dict with tendroid data:
        {
            'name': str,
            'position': tuple,
            'radius': float,
            'length': float,
            'mesh_prim': UsdGeom.Mesh,
            'mesh_path': str,
            'base_path': str,
            'base_points': list,
            'deform_start_height': float,
            'flare_height': float,
            'radial_segments': int,
            'height_segments': int,
        }
        Or None if creation failed.
    """
    try:
      # Load config defaults
      if flare_height_percent is None:
        flare_height_percent = get_config_value(
          "tendroid_geometry", "flare_height_percent", default=15.0
        )
      if flare_radius_multiplier is None:
        flare_radius_multiplier = get_config_value(
          "tendroid_geometry", "flare_radius_multiplier", default=2.0
        )

      # Adjust Y position to terrain if height function provided
      if get_height_fn:
        floor_height = get_height_fn(position[0], position[2])
        position = (position[0], floor_height, position[2])

      # Create base Xform
      base_path = f"{parent_path}/{name}"
      base_xform = UsdGeom.Xform.Define(stage, base_path)
      base_xform.ClearXformOpOrder()
      translate_op = base_xform.AddTranslateOp()
      translate_op.Set(Gf.Vec3d(*position))

      # Create mesh with flared base
      mesh_path = f"{base_path}/mesh"
      mesh_prim, points, deform_start = CylinderGenerator.create_mesh(
        stage=stage,
        path=mesh_path,
        radius=radius,
        length=length,
        radial_segments=radial_segments,
        height_segments=height_segments,
        flare_height_percent=flare_height_percent,
        flare_radius_multiplier=flare_radius_multiplier
      )

      flare_height = length * (flare_height_percent / 100.0)

      # Conform base to terrain if height function provided
      if get_height_fn:
        conformed_points = conform_base_to_terrain(
          vertices=points,
          base_position=position,
          flare_height=flare_height,
          radial_segments=radial_segments,
          height_segments=height_segments,
          get_height_fn=get_height_fn
        )
        mesh_prim.GetPointsAttr().Set(conformed_points)
        points = conformed_points

      # Apply material
      apply_material(stage, mesh_prim)

      carb.log_info(
        f"[V2TendroidBuilder] Created '{name}' at {position} "
        f"(r={radius}, L={length}, flare={flare_height_percent}%)"
      )

      return {
        'name': name,
        'position': position,
        'radius': radius,
        'length': length,
        'mesh_prim': mesh_prim,
        'mesh_path': mesh_path,
        'base_path': base_path,
        'base_points': points,
        'deform_start_height': deform_start,
        'flare_height': flare_height,
        'radial_segments': radial_segments,
        'height_segments': height_segments,
        'max_amplitude': max_amplitude,
        'bulge_width': bulge_width,
      }

    except Exception as e:
      carb.log_error(f"[V2TendroidBuilder] Failed to create '{name}': {e}")
      import traceback
      traceback.print_exc()
      return None

  @staticmethod
  def destroy_tendroid(stage, base_path: str):
    """
    Remove tendroid from stage.

    Args:
        stage: USD stage
        base_path: Base prim path of tendroid
    """
    if stage and base_path:
      prim = stage.GetPrimAtPath(base_path)
      if prim.IsValid():
        stage.RemovePrim(base_path)
