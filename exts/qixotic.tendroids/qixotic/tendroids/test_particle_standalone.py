"""
Standalone particle system comparison test

Tests Warp GPU particles vs sphere-based particles.
Run this after loading the Tendroids extension in USD Composer.
"""

import time

import carb
from qixotic.tendroids.bubbles.bubble_config import BubbleConfig
from qixotic.tendroids.scene import TendroidSceneManager


def run_particle_test(test_mode="warp", duration=30.0, num_tendroids=15):
  """
  Run particle system performance test.

  Args:
      test_mode: "warp" or "spheres"
      duration: Test duration in seconds
      num_tendroids: Number of tendroids to create
  """
  carb.log_warn("=" * 60)
  carb.log_warn(f"PARTICLE SYSTEM TEST - {test_mode.upper()}")
  carb.log_warn(f"Tendroids: {num_tendroids}, Duration: {duration}s")
  carb.log_warn("=" * 60)

  # Create scene manager with specified particle system
  use_warp = (test_mode == "warp")
  scene_manager = TendroidSceneManager(use_warp_particles=use_warp)

  # Configure bubble system for more particles (stress test)
  if scene_manager.bubble_config:
    scene_manager.bubble_config.particles_per_pop = 10  # More particles
    scene_manager.bubble_config.particle_lifetime = 3.0  # Longer life
    scene_manager.bubble_config.max_particles = 100  # Higher limit

  # Create test scene
  carb.log_info(f"Creating {num_tendroids} tendroids...")
  success = scene_manager.create_tendroids(
    count=num_tendroids,
    spawn_area=(200, 200),
    radius_range=(8, 12),
    num_segments=16  # Optimized for performance
  )

  if not success:
    carb.log_error("Failed to create tendroids")
    return None

  # Start animation with profiling
  scene_manager.start_animation(enable_profiling=True)

  # Track performance
  start_time = time.time()
  frame_count = 0
  fps_samples = []
  last_fps_time = time.time()
  last_log_time = time.time()

  carb.log_info("Test started. Monitoring performance...")

  # Run test
  while time.time() - start_time < duration:
    frame_count += 1
    current_time = time.time()

    # Calculate FPS every second
    time_delta = current_time - last_fps_time
    if time_delta >= 1.0:
      fps = frame_count / time_delta
      fps_samples.append(fps)
      frame_count = 0
      last_fps_time = current_time

    # Log status every 5 seconds
    if current_time - last_log_time >= 5.0:
      if fps_samples:
        recent_fps = fps_samples[-1]
        bubble_count = scene_manager.get_bubble_count()
        particle_count = scene_manager.get_particle_count()
        particle_type = scene_manager.get_particle_system_type()

        carb.log_warn(
          f"[{int(current_time - start_time)}s] "
          f"{particle_type} | FPS: {recent_fps:.1f} | "
          f"Bubbles: {bubble_count} | Particles: {particle_count}"
        )

      last_log_time = current_time

    # Small delay to not overwhelm the system
    time.sleep(0.01)

  # Stop animation
  scene_manager.stop_animation()

  # Report results
  if fps_samples:
    avg_fps: float = sum(fps_samples) / len(fps_samples)
    min_fps = min(fps_samples)
    max_fps = max(fps_samples)

    carb.log_warn("=" * 60)
    carb.log_warn(f"TEST COMPLETE - {test_mode.upper()}")
    carb.log_warn(f"Particle System: {scene_manager.get_particle_system_type()}")
    carb.log_warn(f"Average FPS: {avg_fps:.1f}")
    carb.log_warn(f"Min FPS: {min_fps:.1f}")
    carb.log_warn(f"Max FPS: {max_fps:.1f}")
    carb.log_warn(f"Samples: {len(fps_samples)}")
    carb.log_warn("=" * 60)

    # Write results to file
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"particle_test_{test_mode}_{timestamp}.log"
    filepath = f"C:\\Dev\\Omniverse\\fabric-tendroids\\exts\\qixotic.tendroids\\qixotic\\tendroids\\stress_test_results\\{filename}"

    with open(filepath, 'w') as f:
      f.write("=" * 60 + "\n")
      f.write(f"PARTICLE SYSTEM TEST - {test_mode.upper()}\n")
      f.write("=" * 60 + "\n")
      f.write(f"Date: {datetime.datetime.now()}\n")
      f.write(f"Particle System: {scene_manager.get_particle_system_type()}\n")
      f.write(f"Tendroids: {num_tendroids}\n")
      f.write(f"Duration: {duration}s\n")
      f.write("-" * 60 + "\n")
      f.write(f"Average FPS: {avg_fps:.2f}\n")
      f.write(f"Min FPS: {min_fps:.2f}\n")
      f.write(f"Max FPS: {max_fps:.2f}\n")
      f.write(f"Samples: {len(fps_samples)}\n")
      f.write("=" * 60 + "\n")

    carb.log_info(f"Results saved to {filename}")

  # Cleanup
  scene_manager.clear_tendroids()
  scene_manager.shutdown()

  return avg_fps if fps_samples else 0


def compare_particle_systems():
  """Run comparison between both particle systems."""
  carb.log_warn("\n" + "=" * 60)
  carb.log_warn("PARTICLE SYSTEM COMPARISON TEST")
  carb.log_warn("Testing both particle systems back-to-back")
  carb.log_warn("=" * 60 + "\n")

  results = { }

  # Test sphere-based particles first
  carb.log_warn("\n>>> TESTING SPHERE-BASED PARTICLES <<<\n")
  time.sleep(2)  # Brief pause
  sphere_fps = run_particle_test("spheres", duration=30.0, num_tendroids=15)
  results["spheres"] = sphere_fps

  # Brief pause between tests
  carb.log_warn("\n>>> SWITCHING TO WARP GPU PARTICLES <<<\n")
  time.sleep(5)

  # Test Warp GPU particles
  carb.log_warn("\n>>> TESTING WARP GPU PARTICLES <<<\n")
  time.sleep(2)  # Brief pause
  warp_fps = run_particle_test("warp", duration=30.0, num_tendroids=15)
  results["warp"] = warp_fps

  # Final comparison
  if results["spheres"] > 0 and results["warp"] > 0:
    improvement = ((results["warp"] - results["spheres"]) / results["spheres"]) * 100

    carb.log_warn("\n" + "=" * 60)
    carb.log_warn("FINAL COMPARISON")
    carb.log_warn(f"Sphere-based: {results['spheres']:.1f} FPS")
    carb.log_warn(f"Warp GPU:     {results['warp']:.1f} FPS")
    carb.log_warn(f"Improvement:  {improvement:+.1f}%")
    carb.log_warn("=" * 60 + "\n")


if __name__ == "__main__":
  # This won't work standalone - needs Omniverse context
  carb.log_error("This test must be run from within USD Composer")
  carb.log_info("Load the Tendroids extension first, then run:")
  carb.log_info("  from qixotic.tendroids.test_particle_standalone import compare_particle_systems")
  carb.log_info("  compare_particle_systems()")
