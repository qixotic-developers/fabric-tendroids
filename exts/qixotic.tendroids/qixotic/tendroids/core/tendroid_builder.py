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
from ..animation.breathing import BreathingAnimator


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
      # Create USD geometry
      if not TendroidBuilder._create_usd_geometry(tendroid, stage, parent_path):
        return False
      
      # Initialize all components
      if not TendroidBuilder._initialize_components(tendroid):
        return False
      
      # Log creation success
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
      # Create base Xform
      tendroid.base_path = f"{parent_path}/{tendroid.name}"
      base_xform = UsdGeom.Xform.Define(stage, tendroid.base_path)
      base_xform.AddTranslateOp().Set(Gf.Vec3d(*tendroid.position))
      
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
          flare_height_percent=15.0,
          flare_radius_multiplier=2.0
        )
      
      tendroid.mesh_prim = mesh_prim
      tendroid.deform_start_height = deform_start
      tendroid._initial_vertices = vertices
      
      return True
    
    except Exception as e:
      carb.log_error(f"[TendroidBuilder] USD geometry creation failed: {e}")
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
      
      # Breathing animator with defaults
      tendroid.breathing_animator = BreathingAnimator(
        length=tendroid.length,
        deform_start_height=tendroid.deform_start_height,
        wave_speed=40.0,
        bulge_length_percent=40.0,
        amplitude=0.35,
        cycle_delay=2.0
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
