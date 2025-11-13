"""
Phase 2A Comparison Test - Transform vs Vertex Deform

Creates Tendroids with both animation modes for side-by-side comparison.
"""

import carb
from qixotic.tendroids.animation import AnimationMode
from qixotic.tendroids.core import Tendroid
from qixotic.tendroids.scene import EnvironmentSetup


def test_animation_mode_comparison(stage):
  """
  Create Tendroids with both animation modes for comparison.
  
  Left side: TRANSFORM mode (Phase 1 - not yet implemented)
  Right side: VERTEX_DEFORM mode (Phase 2A - GPU accelerated)
  
  Args:
      stage: USD stage
  """
  carb.log_info("=" * 80)
  carb.log_info("Phase 2A Comparison Test - Animation Modes")
  carb.log_info("=" * 80)
  
  # Setup environment
  carb.log_info("[Test] Setting up environment...")
  EnvironmentSetup.setup_environment(stage)  # FIXED: static method call
  
  # Create Tendroids with different animation modes
  carb.log_info("[Test] Creating Tendroids for comparison...")
  
  test_tendroids = []
  
  # TRANSFORM mode tendroids (left side) - placeholder for future
  carb.log_info("[Test] Transform mode (Phase 1 - not implemented):")
  # transform_positions = [
  #   (-100, 0, -50),
  #   (-100, 0, 0),
  #   (-100, 0, 50)
  # ]
  # for i, pos in enumerate(transform_positions):
  #   ...TRANSFORM mode creation...
  
  # VERTEX_DEFORM mode tendroids (right side)
  carb.log_info("[Test] Vertex Deform mode (Phase 2A - active):")
  vertex_deform_positions = [
    (0, 0, -50),
    (0, 0, 0),
    (0, 0, 50)
  ]
  
  for i, pos in enumerate(vertex_deform_positions):
    tendroid = Tendroid(
      name=f"tendroid_vd_{i:03d}",
      position=pos,
      radius=10.0,
      length=100.0,
      num_segments=32,
      radial_resolution=16,
      animation_mode=AnimationMode.VERTEX_DEFORM
    )
    
    if tendroid.create(stage):
      test_tendroids.append(tendroid)
      carb.log_info(
        f"  ✅ Created '{tendroid.name}' at {pos} "
        f"({tendroid.get_animation_mode_name()})"
      )
    else:
      carb.log_error(f"  ❌ Failed to create tendroid at {pos}")
  
  carb.log_info("=" * 80)
  carb.log_info(f"[Test] Created {len(test_tendroids)} Tendroids")
  carb.log_info(f"[Test] VERTEX_DEFORM mode: {len(test_tendroids)}")
  carb.log_info(f"[Test] TRANSFORM mode: 0 (not yet implemented)")
  carb.log_info("=" * 80)
  
  return test_tendroids


__all__ = ['test_animation_mode_comparison']
