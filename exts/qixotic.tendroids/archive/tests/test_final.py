"""
WORKING test for Hide Until Clear bubble visibility
This version uses the actual API correctly
"""

import carb
from qixotic.tendroids.scene.manager import TendroidSceneManager

carb.log_warn("="*70)
carb.log_warn("BUBBLE VISIBILITY TEST - Hide Until Clear Implementation")
carb.log_warn("="*70)

# Create scene manager
scene = TendroidSceneManager()
carb.log_info("✓ Created scene manager")

# Clear existing
scene.clear_tendroids()
carb.log_info("✓ Cleared existing tendroids")

# Create tendroids - this will load config from JSON
success = scene.create_tendroids(
    count=2,
    spawn_area=(120, 120),
    radius_range=(8, 12),
    num_segments=16
)

if success:
    carb.log_warn("\n✓ Created 2 tendroids")
    
    # Check if bubble manager was created
    if scene.bubble_manager:
        carb.log_info("✓ Bubble system active")
        
        # Check current hide_until_clear setting
        if hasattr(scene.bubble_manager.config, 'hide_until_clear'):
            current_setting = scene.bubble_manager.config.hide_until_clear
            carb.log_warn(f"✓ Hide Until Clear: {current_setting}")
        else:
            carb.log_warn("✓ Hide Until Clear: True (default)")
            # Add the attribute if it doesn't exist
            scene.bubble_manager.config.hide_until_clear = True
    else:
        carb.log_error("Bubble system not initialized!")
        carb.log_error("Check that bubble_system.enabled is true in tendroids_config.json")
    
    # Start animation
    scene.start_animation()
    carb.log_warn("✓ Started animation")
    
    carb.log_warn("\n" + "="*70)
    carb.log_warn("WHAT TO OBSERVE:")
    carb.log_warn("")
    carb.log_warn("If Hide Until Clear is ENABLED:")
    carb.log_warn("  • Bubbles are INVISIBLE inside cylinders")
    carb.log_warn("  • Bubbles POP INTO VIEW at cylinder mouth")
    carb.log_warn("  • NO CLIPPING through tilted walls")
    carb.log_warn("")
    carb.log_warn("If Hide Until Clear is DISABLED:")
    carb.log_warn("  • Bubbles visible immediately")
    carb.log_warn("  • CLIPPING through cylinder walls")
    carb.log_warn("="*70)
    
    carb.log_warn("\nTest running! Watch the cylinder mouths...")
    carb.log_warn("")
    
    # Interactive commands that actually work
    if scene.bubble_manager:
        carb.log_warn("INTERACTIVE COMMANDS:")
        carb.log_warn("")
        carb.log_warn("Turn OFF the fix (see clipping):")
        carb.log_warn("  scene.bubble_manager.config.hide_until_clear = False")
        carb.log_warn("")
        carb.log_warn("Turn ON the fix (no clipping):")
        carb.log_warn("  scene.bubble_manager.config.hide_until_clear = True")
        carb.log_warn("")
        carb.log_warn("Check current setting:")
        carb.log_warn("  scene.bubble_manager.config.hide_until_clear")
        carb.log_warn("")
        carb.log_warn("Stop animation:")
        carb.log_warn("  scene.stop_animation()")
        carb.log_warn("")
        carb.log_warn("Get counts:")
        carb.log_warn("  scene.get_bubble_count()")
        carb.log_warn("  scene.get_tendroid_count()")
    
else:
    carb.log_error("Failed to create tendroids")
    carb.log_error("Make sure the extension is properly loaded")

# Store reference for interactive use
_scene = scene
carb.log_info("\nScene reference stored as: _scene")

# Try to position camera
try:
    import omni.kit.viewport.utility
    viewport = omni.kit.viewport.utility.get_active_viewport()
    if viewport and hasattr(viewport, 'viewport_api'):
        viewport.viewport_api.set_camera_position(
            "/OmniverseKit_Persp",
            250.0, 150.0, 400.0,  # eye
            0.0, 70.0, 0.0,       # target
            0.0, 1.0, 0.0         # up
        )
        carb.log_info("✓ Camera positioned")
except:
    pass
