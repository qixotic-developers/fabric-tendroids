r"""
Performance Diagnostics for Tendroids + Creature

Measures initialization and runtime performance to identify bottlenecks.

Usage in Omniverse Script Editor:
    exec(open(r'C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids\diagnose_performance.py').read())
"""

import carb
import time
from qixotic.tendroids.scene import V2SceneManager


carb.log_info("=" * 70)
carb.log_info("PERFORMANCE DIAGNOSTICS - Tendroids with Creature")
carb.log_info("=" * 70)

# Track timing
timings = {}

# Create manager
t0 = time.perf_counter()
manager = V2SceneManager()
timings['manager_init'] = time.perf_counter() - t0

# Create scene
t0 = time.perf_counter()
success = manager.create_tendroids(
    count=15,
    radial_segments=16,
    height_segments=32
)
timings['scene_creation'] = time.perf_counter() - t0

if not success:
    carb.log_error("❌ Scene creation failed!")
else:
    # Start animation
    t0 = time.perf_counter()
    manager.start_animation(enable_profiling=True)
    timings['animation_start'] = time.perf_counter() - t0
    
    # Report
    carb.log_info("")
    carb.log_info("⏱️  INITIALIZATION TIMINGS:")
    carb.log_info(f"   Manager init:     {timings['manager_init']*1000:6.2f} ms")
    carb.log_info(f"   Scene creation:   {timings['scene_creation']*1000:6.2f} ms")
    carb.log_info(f"   Animation start:  {timings['animation_start']*1000:6.2f} ms")
    carb.log_info(f"   TOTAL:            {sum(timings.values())*1000:6.2f} ms")
    carb.log_info("")
    
    # Check components
    carb.log_info("📦 ACTIVE COMPONENTS:")
    carb.log_info(f"   Tendroids:        {len(manager.tendroids)}")
    carb.log_info(f"   GPU bubbles:      {'✅ Yes' if manager.gpu_bubble_adapter else '❌ No'}")
    carb.log_info(f"   Batch deformer:   {'✅ Yes' if manager.batch_deformer else '❌ No'}")
    carb.log_info(f"   Creature:         {'✅ Yes' if manager.creature_controller else '❌ No'}")
    carb.log_info("")
    
    carb.log_info("📊 Profiling is enabled - watch console for FPS reports")
    carb.log_info("")
    carb.log_info("🎮 Test creature movement now - hold W/A/S/D keys")
    carb.log_info("")
    carb.log_info("🛑 To stop: manager.stop_animation()")

carb.log_info("=" * 70)
