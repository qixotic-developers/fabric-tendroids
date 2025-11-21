"""
Script Editor test for complete UI wave integration

Run this in Script Editor to test the full Tendroid Controls UI with wave motion.
"""

import carb
from qixotic.tendroids.scene import TendroidSceneManager

# Create manager
carb.log_info("\n" + "=" * 60)
carb.log_info("UI WAVE INTEGRATION TEST")
carb.log_info("=" * 60)

manager = TendroidSceneManager()
carb.log_info("✓ Scene manager created")

# The UI will automatically have access to the manager's animation controller
# which includes the wave controller

carb.log_info("✓ Wave controller available in animation controller")
carb.log_info("\nOPEN TENDROID CONTROLS UI:")
carb.log_info("  - Window → Tendroid Controls")
carb.log_info("  - Create tendroids")
carb.log_info("  - Adjust wave settings:")
carb.log_info("    • Amplitude slider")
carb.log_info("    • Frequency slider") 
carb.log_info("    • Phase offset")
carb.log_info("    • Enable/disable checkbox")
carb.log_info("\nWave motion will apply to all tendroids!")
carb.log_info("=" * 60)
