"""
Minimal test - just run this to see the Hide Until Clear fix
"""

import carb
from qixotic.tendroids.scene.manager import TendroidSceneManager

# Create and setup
scene = TendroidSceneManager()
scene.clear_tendroids()
scene.create_tendroids(count=2)
scene.start_animation()

carb.log_warn("="*50)
carb.log_warn("BUBBLE VISIBILITY FIX ACTIVE")
carb.log_warn("="*50)
carb.log_warn("Bubbles will POP INTO VIEW at cylinder mouths")
carb.log_warn("(They're invisible while inside the cylinder)")
carb.log_warn("")

if scene.bubble_manager:
    carb.log_warn("TO TOGGLE:")
    carb.log_warn("OFF: scene.bubble_manager.config.hide_until_clear = False")
    carb.log_warn("ON:  scene.bubble_manager.config.hide_until_clear = True")
