# Test Phase 2: Bubble drift with wave motion
import carb
from qixotic.tendroids.scene import TendroidSceneManager

carb.log_info("=" * 60)
carb.log_info("PHASE 2 TEST: Bubble Drift with Wave Motion")
carb.log_info("=" * 60)

# Create scene manager with bubbles
manager = TendroidSceneManager(use_warp_particles=True)

# Create single tendroid
success = manager.create_tendroids(
    count=1,
    spawn_area=(50, 50),
    radius_range=(10, 10),
    num_segments=32
)

if success:
    carb.log_info("✓ Created tendroid with bubble system")
    
    # Configure wave for visible motion
    if manager.animation_controller and manager.animation_controller.wave_controller:
        wave = manager.animation_controller.wave_controller
        wave.config.amplitude = 20.0  # Strong wave
        wave.config.frequency = 0.25   # Moderate speed for observation
        wave.enabled = True
        carb.log_info(f"✓ Wave configured: amplitude={wave.config.amplitude}, freq={wave.config.frequency}")
    
    # Configure bubbles for easier observation
    if manager.bubble_config:
        manager.bubble_config.rise_speed = 40.0  # Slower rise for better observation
        manager.bubble_config.min_pop_height = 200.0  # Higher pop for longer observation
        manager.bubble_config.max_pop_height = 300.0
        carb.log_info(f"✓ Bubble config: rise_speed={manager.bubble_config.rise_speed}")
    
    # Start animation
    manager.start_animation()
    carb.log_info("✓ Animation started")
    
    carb.log_info("\n" + "=" * 60)
    carb.log_info("EXPECTED PHASE 2 BEHAVIOR:")
    carb.log_info("1. Tendroid sways back and forth (base anchored)")
    carb.log_info("2. Bubbles spawn at swaying mouth position")
    carb.log_info("3. As bubbles rise, they DRIFT with the wave current")
    carb.log_info("4. Bubble drift is ~30% of tendroid sway intensity")
    carb.log_info("5. Creates natural 'underwater current' effect")
    carb.log_info("=" * 60)
    carb.log_info("\nWatch bubbles - they should sway side-to-side as they rise!")
else:
    carb.log_error("Failed to create tendroid")
