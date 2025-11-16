"""
Profiled Performance Test for Tendroids

Runs animation with detailed per-frame profiling to identify bottlenecks.
"""

import asyncio
import carb
import omni.usd
from qixotic.tendroids.scene import TendroidSceneManager


async def run_profiled_test(num_tendroids: int = 30, duration_seconds: float = 5.0):
    """
    Run profiled performance test.
    
    Args:
        num_tendroids: Number of Tendroids to spawn
        duration_seconds: How long to run the test
    """
    carb.log_info("=" * 70)
    carb.log_info(f"PROFILED PERFORMANCE TEST - {num_tendroids} Tendroids")
    carb.log_info("=" * 70)
    
    # Get current stage
    context = omni.usd.get_context()
    stage = context.get_stage()
    
    if not stage:
        carb.log_error("[ProfiledTest] No stage available")
        return
    
    # Create manager and spawn Tendroids
    manager = TendroidSceneManager()
    
    carb.log_info(f"[ProfiledTest] Creating {num_tendroids} Tendroids...")
    success = manager.create_tendroids(count=num_tendroids)
    
    if not success:
        carb.log_error("[ProfiledTest] Failed to create Tendroids")
        return
    
    # Enable profiling
    manager.animation_controller.enable_profiling(True)
    
    carb.log_info(f"[ProfiledTest] Starting profiled animation for {duration_seconds}s...")
    manager.start_animation()
    
    # Wait for test duration
    await asyncio.sleep(duration_seconds)
    
    # Stop animation (this will print the profile report)
    carb.log_info("[ProfiledTest] Stopping animation...")
    manager.stop_animation()
    
    # Cleanup
    carb.log_info("[ProfiledTest] Cleaning up...")
    manager.clear_tendroids()
    
    carb.log_info("=" * 70)
    carb.log_info("[ProfiledTest] Test Complete")
    carb.log_info("=" * 70)


def run_profiled_test_sync(num_tendroids: int = 30, duration_seconds: float = 5.0):
    """Synchronous wrapper for running profiled test from Script Editor."""
    asyncio.ensure_future(run_profiled_test(num_tendroids, duration_seconds))


if __name__ == "__main__":
    # Run with 30 Tendroids for 5 seconds
    run_profiled_test_sync(30, 5.0)
