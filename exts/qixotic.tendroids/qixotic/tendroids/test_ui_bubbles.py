"""
Test script to verify bubble system works with UI controls

Tests that bubbles and particle effects are properly initialized
when using the Tendroid Controls UI.
"""

import carb
from qixotic.tendroids.scene import TendroidSceneManager


def test_ui_bubble_system():
  """Test bubble system initialization through UI workflow."""

  carb.log_info("=" * 60)
  carb.log_info("Testing Bubble System with UI Controls")
  carb.log_info("=" * 60)

  # Create scene manager as the UI would
  manager = TendroidSceneManager(use_warp_particles=True)

  # Create tendroids with default parameters
  success = manager.create_tendroids(
    count=3,  # Small number for testing
    spawn_area=(200, 200),
    radius_range=(8, 12),
    num_segments=16
  )

  if not success:
    carb.log_error("Failed to create tendroids")
    return False

  carb.log_info(f"✓ Created {len(manager.tendroids)} tendroids")

  # Check bubble manager
  if manager.bubble_manager:
    carb.log_info("✓ Bubble manager initialized")

    # Check particle system type
    particle_type = manager.get_particle_system_type()
    carb.log_info(f"✓ Using particle system: {particle_type}")

    # Verify bubble config
    config = manager.bubble_config
    if config:
      carb.log_info(f"  - Particles per pop: {config.particles_per_pop}")
      carb.log_info(f"  - Particle size: {config.particle_size}")
      carb.log_info(f"  - Max particles: {config.max_particles}")
  else:
    carb.log_error("✗ Bubble manager not initialized!")
    return False

  # Start animation
  manager.start_animation()
  carb.log_info("✓ Animation started")

  # Check animation controller
  if manager.animation_controller:
    if manager.animation_controller.bubble_manager:
      carb.log_info("✓ Bubble manager connected to animation controller")
    else:
      carb.log_error("✗ Bubble manager not connected to animation!")

  carb.log_info("=" * 60)
  carb.log_info("Test complete! Use UI controls to:")
  carb.log_info("1. Click 'Stop Animation' to stop")
  carb.log_info("2. Adjust bubble settings in the Bubble Controls section")
  carb.log_info("3. Click 'Start Animation' to see bubbles with particles")
  carb.log_info("=" * 60)

  return True


if __name__ == "__main__":
  test_ui_bubble_system()
