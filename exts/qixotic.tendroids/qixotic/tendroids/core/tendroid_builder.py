"""
Tendroid USD builder for geometry creation

Handles all USD stage creation, mesh generation, and component initialization.
"""

import carb
from pxr import Gf, UsdGeom
from .cylinder_generator import CylinderGenerator
from .warp_deformer import WarpDeformer
from .material_safety import MaterialSafetyChecker
from .mesh_updater import MeshVertexUpdater
from .terrain_conform import conform_base_to_terrain
from ..animation.breathing import BreathingAnimator
from ..sea_floor import get_height_at
from ..config import get_config_value


class TendroidBuilder:
  """
  Builder for creating Tendroid USD geometry and initializing components.
  
  Separates complex creation logic from the main Tendroid class,
  following the Builder pattern for clean separation of concerns.
  """
  
  @staticmethod
  def create_in_stage(
    tendroid,
    stage,
    parent_path: str = "/World/Tendroids"
  ) -> bool:
    """
    Create Tendroid geometry in USD stage and initialize all components.
    
    Args:
        tendroid: Tendroid instance to build for
        stage: USD stage
        parent_path: Parent prim path
    
    Returns:
        Success status
    """
    try:
      # Query sea floor height at tendroid position
      floor_height = get_height_at(tendroid.position[0], tendroid.position[1])
      
      # Adjust position to sit on floor
      adjusted_position = (
        tendroid.position[0],
        floor_height,
        tendroid.position[2]
      )
      tendroid.position = adjusted_position
      
      # Create USD geometry
      if not TendroidBuilder._create_usd_geometry(tendroid, stage, parent_path):
        return False
      
      # Conform base to terrain AFTER geometry creation
      if not TendroidBuilder._conform_base_to_terrain(tendroid):
        return False
      
      # Initialize all components
      if not TendroidBuilder._initialize_components(tendroid):
        return False
      
      # Log creation status
      TendroidBuilder._log_creation_status(tendroid)
      
      tendroid.is_created = True
      return True
    
    except Exception as e:
      carb.log_error(f"[TendroidBuilder] Failed to create '{tendroid.name}': {e}")
      import traceback
      traceback.print_exc()
      return False
  
  @staticmethod
  def _create_usd_geometry(tendroid, stage, parent_path: str) -> bool:
    """Create USD Xform and mesh geometry."""
    try:
      # Load flare config from JSON
      flare_height_pct = get_config_value(
        "tendroid_geometry", "flare_height_percent", default=15.0
      )
      flare_radius_mult = get_config_value(
        "tendroid_geometry", "flare_radius_multiplier", default=2.0
      )
      
      # Create base Xform
      tendroid.base_path = f"{parent_path}/{tendroid.name}"
      base_xform = UsdGeom.Xform.Define(stage, tendroid.base_path)
      
      # Use GetOrAdd to handle both new creation and re-creation
      base_xform.ClearXformOpOrder()
      translate_op = base_xform.AddTranslateOp()
      translate_op.Set(Gf.Vec3d(*tendroid.position))
      
      # Create cylinder mesh with flared base
      tendroid.mesh_path = f"{tendroid.base_path}/mesh"
      mesh_prim, vertices, num_segs, rad_res, deform_start = \
        CylinderGenerator.create_tendroid_cylinder(
          stage=stage,
          path=tendroid.mesh_path,
          radius=tendroid.radius,
          length=tendroid.length,
          num_segments=tendroid.num_segments,
          radial_resolution=tendroid.radial_resolution,
          flare_height_percent=flare_height_pct,
          flare_radius_multiplier=flare_radius_mult
        )
      
      tendroid.mesh_prim = mesh_prim
      tendroid.deform_start_height = deform_start
      tendroid._initial_vertices = vertices
      
      # Store flare info for terrain conforming
      tendroid._flare_height = tendroid.length * (flare_height_pct / 100.0)
      
      return True
    
    except Exception as e:
      carb.log_error(f"[TendroidBuilder] USD geometry creation failed: {e}")
      return False
  
  @staticmethod
  def _conform_base_to_terrain(tendroid) -> bool:
    """Conform base vertices to terrain contours."""
    try:
      # Conform vertices to terrain
      conformed_vertices = conform_base_to_terrain(
        vertices=tendroid._initial_vertices,
        base_position=tendroid.position,
        flare_height=tendroid._flare_height,
        num_segments=tendroid.num_segments,
        radial_resolution=tendroid.radial_resolution
      )
      
      # Update mesh with conformed vertices
      mesh_geom = UsdGeom.Mesh(tendroid.mesh_prim)
      mesh_geom.GetPointsAttr().Set(conformed_vertices)
      
      # Update stored vertices for deformation system
      tendroid._initial_vertices = conformed_vertices
      
      return True
    
    except Exception as e:
      carb.log_error(f"[TendroidBuilder] Terrain conforming failed: {e}")
      import traceback
      traceback.print_exc()
      return False
  
  @staticmethod
  def _initialize_components(tendroid) -> bool:
    """Initialize all Tendroid components (safety, updater, deformer, animator)."""
    try:
      # Material safety checker
      tendroid.material_safety = MaterialSafetyChecker(tendroid.mesh_path)
      tendroid.material_safety.check_material()
      
      # Mesh updater
      tendroid.mesh_updater = MeshVertexUpdater(tendroid.mesh_prim)
      if not tendroid.mesh_updater.is_valid():
        carb.log_error("[TendroidBuilder] Mesh updater initialization failed")
        return False
      
      # Warp deformer
      tendroid.warp_deformer = WarpDeformer(
        tendroid._initial_vertices,
        tendroid.deform_start_height
      )
      
      # Load animation config from JSON
      wave_speed = get_config_value(
        "tendroid_animation", "wave_speed", default=40.0
      )
      bulge_pct = get_config_value(
        "tendroid_animation", "bulge_length_percent", default=40.0
      )
      amplitude = get_config_value(
        "tendroid_animation", "amplitude", default=0.35
      )
      cycle_delay = get_config_value(
        "tendroid_animation", "cycle_delay", default=2.0
      )
      
      # Breathing animator with config values
      tendroid.breathing_animator = BreathingAnimator(
        length=tendroid.length,
        deform_start_height=tendroid.deform_start_height,
        wave_speed=wave_speed,
        bulge_length_percent=bulge_pct,
        amplitude=amplitude,
        cycle_delay=cycle_delay
      )
      
      return True
    
    except Exception as e:
      carb.log_error(f"[TendroidBuilder] Component initialization failed: {e}")
      return False
  
  @staticmethod
  def _log_creation_status(tendroid):
    """Log creation status based on material safety."""
    if not tendroid.material_safety.is_safe_for_animation():
      carb.log_error(
        f"[TendroidBuilder] ❌ '{tendroid.name}' has GLASS material - "
        f"animation will be blocked"
      )
    else:
      carb.log_info(
        f"[TendroidBuilder] Created '{tendroid.name}' with animation enabled"
      )
