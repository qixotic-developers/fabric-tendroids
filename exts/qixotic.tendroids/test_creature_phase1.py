r"""
Test Script for Creature Controller Phase 1

Tests basic keyboard-controlled creature movement.

Usage in Omniverse Script Editor:
    exec(open(r'C:\Dev\Omniverse\fabric-tendroids\exts\qixotic.tendroids\test_creature_phase1.py').read())
"""

import carb
from qixotic.tendroids.v2.scene import V2SceneManager


# Create scene manager
carb.log_info("=" * 60)
carb.log_info("Creating Tendroids scene with interactive creature...")
carb.log_info("=" * 60)

manager = V2SceneManager()

# Create tendroids with creature
success = manager.create_tendroids(
    count=15,
    radial_segments=16,
    height_segments=32
)

if success:
    carb.log_info("✅ Scene created successfully")
    carb.log_info(f"   Tendroids: {manager.get_tendroid_count()}")
    
    # Start animation with profiling
    manager.start_animation(enable_profiling=True)
    carb.log_info("✅ Animation started with profiling")
    
    # Print instructions
    carb.log_info("")
    carb.log_info("🎮 CREATURE CONTROLS (KEYBOARD):")
    carb.log_info("   W or Up Arrow:    Move forward (Z-)")
    carb.log_info("   S or Down Arrow:  Move backward (Z+)")
    carb.log_info("   A or Left Arrow:  Move left (X-)")
    carb.log_info("   D or Right Arrow: Move right (X+)")
    carb.log_info("   Space:            Move up (Y+)")
    carb.log_info("   Left Shift:       Move down (Y-)")
    carb.log_info("")
    carb.log_info("   Note: Mouse is free for camera control!")
    carb.log_info("")
    carb.log_info("📊 MONITORING:")
    carb.log_info("   FPS will be logged every second")
    carb.log_info("   Look for cyan cylinder creature in scene")
    carb.log_info("")
    carb.log_info("🛑 TO STOP:")
    carb.log_info("   manager.stop_animation()")
    carb.log_info("   manager.clear_tendroids()")
    carb.log_info("")
else:
    carb.log_error("❌ Failed to create scene")

carb.log_info("=" * 60)
