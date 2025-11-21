"""
Test bubble spawn fix by updating existing scene

Run this after creating tendroids with the UI to apply the spawn fix.
"""

import omni
import carb


def apply_bubble_spawn_fix():
    """Apply bubble spawn fix to current scene."""
    
    print("\n" + "="*60)
    print("APPLYING BUBBLE SPAWN FIX")
    print("="*60)
    
    # Get the extension
    manager = omni.kit.app.get_app().get_extension_manager()
    ext = manager.get_enabled_extension_instance("qixotic.tendroids")
    
    if not ext or not hasattr(ext, '_scene_manager'):
        print("❌ No Tendroids scene found!")
        print("   Please create tendroids first using the UI panel")
        return
    
    scene_manager = ext._scene_manager
    
    # Check for bubble manager
    if not scene_manager.bubble_manager:
        print("❌ No bubble manager!")
        print("   Make sure bubbles are enabled in the scene")
        return
    
    # Check for tendroids
    if not scene_manager.tendroids:
        print("❌ No tendroids in scene!")
        print("   Create some tendroids first")
        return
    
    print(f"✅ Found {len(scene_manager.tendroids)} tendroids")
    print(f"✅ Bubble manager active")
    
    # The spawn fix is already in the modified files, but let's ensure
    # the bubble config has good test settings
    bubble_mgr = scene_manager.bubble_manager
    config = bubble_mgr.config
    
    # Update config for better visibility during testing
    config.opacity = 0.6  # More visible
    config.diameter_multiplier = 1.1  # Slightly larger
    config.debug_logging = True  # Enable debug output
    
    # Ensure proper thresholds
    config.emission_threshold = 0.80  # 80% height
    config.release_threshold = 0.95   # 95% height
    
    # Allow more bubbles for testing
    config.max_bubbles_per_tendroid = 3
    
    # Faster pop for testing
    config.min_pop_height = 80.0
    config.max_pop_height = 120.0
    
    print("\n📋 Bubble configuration:")
    print(f"   - Spawn at {config.emission_threshold*100:.0f}% height")
    print(f"   - Release at {config.release_threshold*100:.0f}% height") 
    print(f"   - Opacity: {config.opacity}")
    print(f"   - Size multiplier: {config.diameter_multiplier}")
    print(f"   - Max bubbles: {config.max_bubbles_per_tendroid}")
    
    # Make sure breathing is active
    activated = 0
    for tendroid in scene_manager.tendroids:
        if hasattr(tendroid, 'breathing_animator'):
            animator = tendroid.breathing_animator
            animator.set_enabled(True)
            
            # Speed up breathing for more bubbles
            animator.frequency = 0.3
            animator.amplitude = 0.5
            animator.wave_speed = 50.0
            
            activated += 1
    
    print(f"\n✅ Activated breathing on {activated} tendroids")
    
    # Enable wave motion if available
    if hasattr(scene_manager, 'wave_controller') and scene_manager.wave_controller:
        wave = scene_manager.wave_controller
        wave.enabled = True
        if hasattr(wave, 'config'):
            wave.config.amplitude = 8.0
            wave.config.frequency = 0.15
        print("✅ Wave motion enabled")
    
    # Check what spawn size is being used
    # The fix in deformation_tracker.py sets initial_diameter to 30% of cylinder
    print("\n🔧 Spawn fix details:")
    print("   - Initial bubble size: 30% of cylinder diameter")
    print("   - Spawn position: Slightly below wave center")
    print("   - Growth rate: 100 units/sec with 3x initial boost")
    print("   - Release: When bubble center reaches 95% height")
    
    print("\n" + "="*60)
    print("SPAWN FIX ACTIVE!")
    print("="*60)
    print("\n👀 WHAT TO WATCH FOR:")
    print("")
    print("1. 🔵 Bubbles START VERY SMALL")
    print("   - Should be ~30% of cylinder diameter")
    print("   - Completely inside the mouth opening")
    print("")
    print("2. 📈 Bubbles GROW RAPIDLY")
    print("   - 3x growth boost for first 0.2 seconds")
    print("   - Reach full size before release")
    print("")
    print("3. ✅ NO CLIPPING")
    print("   - Bubbles never appear outside cylinder")
    print("   - Clean emergence from mouth")
    print("")
    print("4. 🎯 RELEASE AT TOP")
    print("   - Happens at 95% of cylinder height")
    print("   - Bubble mostly emerged before release")
    print("")
    print("💡 TIP: Zoom in close to a tendroid mouth!")
    print("        Watch the first few breathing cycles.")
    print("="*60)


if __name__ == "__main__":
    apply_bubble_spawn_fix()
