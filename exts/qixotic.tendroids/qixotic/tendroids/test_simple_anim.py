"""
Simple Animation Test - Verify update loop works
=================================================

Quick test to confirm Tendroids can animate.
Just creates a few Tendroids and starts animation.

Usage:
    Run from Script Editor, then watch the scene for 10+ seconds
"""

import carb
from qixotic.tendroids.scene.manager import TendroidSceneManager

# Create scene manager
scene_manager = TendroidSceneManager()

# Create 5 Tendroids for visual verification
carb.log_info("[AnimTest] Creating 5 Tendroids...")
success = scene_manager.create_tendroids(
    count=5,
    spawn_area=(200, 200),
    radius_range=(10, 15),
    num_segments=16
)

if success:
    carb.log_info("[AnimTest] Starting animation...")
    scene_manager.start_animation()
    carb.log_info("[AnimTest] ✅ Animation running - watch the scene!")
    carb.log_info("[AnimTest] Run `scene_manager.stop_animation()` to stop")
else:
    carb.log_error("[AnimTest] ❌ Failed to create Tendroids")
