"""
Stop animation - Run this to pause all tendroid and bubble animation
"""

import carb

# If you have a scene reference from a previous test
if '_scene' in globals():
  _scene.stop_animation()
  carb.log_warn("✓ Animation stopped")
elif 'scene' in globals():
  globals.scene.stop_animation()
  carb.log_warn("✓ Animation stopped")
else:
  # Create a new scene manager to stop any running animation
  from qixotic.tendroids.scene.manager import TendroidSceneManager

scene = TendroidSceneManager()
scene.stop_animation()
carb.log_warn("✓ Animation stopped")
carb.log_info("Scene manager created as 'scene'")
