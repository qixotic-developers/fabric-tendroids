"""
Test that Hide Until Clear is accessible from UI
Run this to verify UI integration
"""

import carb
from qixotic.tendroids.scene.manager import TendroidSceneManager
from qixotic.tendroids.ui.control_panel import TendroidControlPanel

# Create scene and spawn tendroids
scene = TendroidSceneManager()
scene.clear_tendroids()
scene.create_tendroids(count=2)
scene.start_animation()

# Create control panel
panel = TendroidControlPanel(scene)
panel.create_window()

carb.log_warn("="*60)
carb.log_warn("UI INTEGRATION TEST")
carb.log_warn("="*60)
carb.log_warn("✓ Tendroids Controls panel created")
carb.log_warn("✓ Look for 'Bubble Controls' section")
carb.log_warn("✓ 'Hide Until Clear' checkbox should be at the top")
carb.log_warn("")
carb.log_warn("The checkbox controls bubble visibility:")
carb.log_warn("  CHECKED = No clipping (bubbles hidden until clear)")
carb.log_warn("  UNCHECKED = Original behavior (visible clipping)")
carb.log_warn("="*60)

# Store references
_scene = scene
_panel = panel

carb.log_info("References: _scene, _panel")
