"""
Phase 2A Integration Test - FastMeshUpdater with Warp Deformation

Tests vertex deformation animation mode with C++ FastMeshUpdater.
"""

import carb
from qixotic.tendroids.animation import AnimationMode
from qixotic.tendroids.core import Tendroid
from qixotic.tendroids.scene import EnvironmentSetup
from qixotic.tendroids.scene.animation_controller import AnimationController


def test_vertex_deform_integration(stage):
  """
  Test VERTEX_DEFORM animation mode integration.
  
  Creates 3 Tendroids using the new vertex deformation system:
  - WarpDeformer for GPU vertex computation
  - FastMeshUpdater for high-performance USD writes (or Python fallback)
  
  Args:
      stage: USD stage
      
  Returns:
      AnimationController instance (keep this alive to maintain animation!)
  """
  carb.log_info("=" * 80)
  carb.log_info("Phase 2A Integration Test - Vertex Deformation Mode")
  carb.log_info("=" * 80)
  
  # Setup environment
  carb.log_info("[Test] Setting up environment...")
  EnvironmentSetup.setup_environment(stage)
  
  # Create test Tendroids with VERTEX_DEFORM mode
  carb.log_info("[Test] Creating Tendroids with VERTEX_DEFORM animation...")
  
  test_tendroids = []
  positions = [
    (-50, 0, -50),
    (0, 0, 0),
    (50, 0, 50)
  ]
  
  for i, pos in enumerate(positions):
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
        f"[Test] ✅ Created '{tendroid.name}' at {pos} "
        f"({tendroid.get_animation_mode_name()} mode)"
      )
    else:
      carb.log_error(f"[Test] ❌ Failed to create tendroid at {pos}")
  
  carb.log_info("=" * 80)
  carb.log_info(f"[Test] Created {len(test_tendroids)}/3 Tendroids")
  
  # Check updater status (C++ or Python fallback)
  if test_tendroids:
    first = test_tendroids[0]
    if first.vertex_deform_helper and first.vertex_deform_helper.is_initialized():
      carb.log_info("[Test] ✅ Using FastMeshUpdater (C++ high-performance)")
    elif first.mesh_updater and first.mesh_updater.is_valid():
      carb.log_info("[Test] ✅ Using Python fallback (functional, FastMeshUpdater unavailable)")
    else:
      carb.log_error("[Test] ❌ No mesh updater available")
  
  # Start animation!
  carb.log_info("[Test] Starting animation controller...")
  anim_controller = AnimationController()
  anim_controller.set_tendroids(test_tendroids)
  anim_controller.start()
  
  carb.log_info("=" * 80)
  carb.log_info("[Test] Integration test complete!")
  carb.log_info("[Test] 🎬 Tendroids are now animating with GPU vertex deformation!")
  carb.log_info("[Test] ⚠️  IMPORTANT: Store the returned controller to keep animation running")
  carb.log_info("=" * 80)
  
  return anim_controller


# Export for easy import
__all__ = ['test_vertex_deform_integration']
