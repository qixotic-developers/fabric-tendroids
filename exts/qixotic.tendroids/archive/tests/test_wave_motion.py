"""
Test script for wave motion effects on Tendroids

Tests ocean current simulation with single Tendroid for development.
"""

import carb
from qixotic.tendroids.scene import TendroidSceneManager


def test_wave_motion():
  """Test wave motion with single Tendroid."""

  carb.log_info("=" * 60)
  carb.log_info("Testing Wave Motion Effects")
  carb.log_info("=" * 60)

  # Create scene manager
  manager = TendroidSceneManager(use_warp_particles=False)  # Disable bubbles for now

  # Create single tendroid for testing
  success = manager.create_tendroids(
    count=1,  # Single tendroid for clear observation
    spawn_area=(50, 50),  # Small area
    radius_range=(10, 10),  # Consistent size
    num_segments=32  # Higher resolution for smooth bending
  )

  if not success:
    carb.log_error("Failed to create tendroid")
    return False

  carb.log_info("✓ Created test tendroid")

  # Configure wave controller
  if manager.animation_controller and manager.animation_controller.wave_controller:
    wave = manager.animation_controller.wave_controller
    wave.config.amplitude = 15.0  # Stronger motion for visibility
    wave.config.frequency = 0.2  # Slower for observation
    wave.enabled = True

    carb.log_info(f"✓ Wave controller configured:")
    carb.log_info(f"  - Amplitude: {wave.config.amplitude}")
    carb.log_info(f"  - Frequency: {wave.config.frequency}")
    carb.log_info(f"  - Direction: {wave.config.direction}")

  # Start animation with profiling
  manager.start_animation(enable_profiling=True)
  carb.log_info("✓ Animation started with wave effects")

  carb.log_info("=" * 60)
  carb.log_info("Wave Test Running!")
  carb.log_info("Watch for:")
  carb.log_info("1. Base should remain anchored (no movement)")
  carb.log_info("2. Tip should sway back and forth")
  carb.log_info("3. Smooth graduated bending along body")
  carb.log_info("=" * 60)
  carb.log_info("Use 'Stop Animation' in UI to stop test")

  return True


if __name__ == "__main__":
  test_wave_motion()
