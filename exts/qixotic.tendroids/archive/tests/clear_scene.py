"""
Clear everything - Run this to remove all tendroids and bubbles from the scene
"""

import carb

# If you have a scene reference from a previous test
if '_scene' in globals():
    _scene.clear_tendroids()
    carb.log_warn("✓ Cleared all tendroids and bubbles")
    carb.log_info(f"Tendroids: {_scene.get_tendroid_count()}")
    carb.log_info(f"Bubbles: {_scene.get_bubble_count()}")
elif 'scene' in globals():
    globals().scene.clear_tendroids()
    carb.log_warn("✓ Cleared all tendroids and bubbles")
    carb.log_info(f"Tendroids: {globals().scene.get_tendroid_count()}")
    carb.log_info(f"Bubbles: {globals().scene.get_bubble_count()}")
else:
    # Create a new scene manager to clear any existing tendroids
    from qixotic.tendroids.scene.manager import TendroidSceneManager
    scene = TendroidSceneManager()
    scene.clear_tendroids()
    carb.log_warn("✓ Cleared all tendroids and bubbles")
    carb.log_info("Scene manager created as 'scene'")
