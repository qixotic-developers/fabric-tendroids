"""
Test script to verify wave motion integration with UI controls

Creates tendroids through UI workflow and tests wave controls.
"""

import carb
import omni.usd
from qixotic.tendroids.scene import TendroidSceneManager


def test_ui_wave_integration():
    """Test complete UI + wave integration."""
    carb.log_info("=" * 60)
    carb.log_info("TESTING UI WAVE INTEGRATION")
    carb.log_info("=" * 60)
    
    # Get current stage
    ctx = omni.usd.get_context()
    stage = ctx.get_stage()
    
    if not stage:
        carb.log_error("No USD stage available!")
        return
    
    # Create manager with animation controller
    carb.log_info("Creating scene manager with wave support...")
    manager = TendroidSceneManager()
    
    # Create test tendroids
    carb.log_info("Creating 3 test tendroids...")
    success, message = manager.spawn_tendroids(stage, count=3)
    
    if success:
        carb.log_info("✓ Created tendroids with bubble systems")
        
        # Start animation (this should initialize wave)
        manager.start_animation()
        carb.log_info("✓ Animation started")
        
        # Access wave controller
        anim = manager.animation_controller
        if anim and hasattr(anim, 'wave_controller'):
            wave = anim.wave_controller
            
            # Test wave configuration
            carb.log_info("\n--- Testing Wave Controls ---")
            
            # Test amplitude change
            original_amp = wave.config.amplitude
            wave.config.amplitude = 25.0
            carb.log_info(f"✓ Changed amplitude: {original_amp} → {wave.config.amplitude}")
            
            # Test frequency change
            original_freq = wave.config.frequency
            wave.config.frequency = 0.3
            carb.log_info(f"✓ Changed frequency: {original_freq} → {wave.config.frequency}")
            
            # Test phase offset change
            original_phase = wave.config.phase_offset
            wave.config.phase_offset = 1.5
            carb.log_info(f"✓ Changed phase: {original_phase} → {wave.config.phase_offset}")
            
            # Test enable/disable
            wave.enabled = False
            carb.log_info(f"✓ Wave disabled: {wave.enabled}")
            
            wave.enabled = True
            carb.log_info(f"✓ Wave enabled: {wave.enabled}")
            
            # Test decay rate
            original_decay = wave.config.vertical_decay_rate
            wave.config.vertical_decay_rate = 0.8
            carb.log_info(f"✓ Changed decay rate: {original_decay} → {wave.config.vertical_decay_rate}")
            
            # Final configuration
            carb.log_info("\n--- Final Wave Configuration ---")
            carb.log_info(f"  Amplitude: {wave.config.amplitude}")
            carb.log_info(f"  Frequency: {wave.config.frequency}")
            carb.log_info(f"  Phase Offset: {wave.config.phase_offset}")
            carb.log_info(f"  Decay Rate: {wave.config.vertical_decay_rate}")
            carb.log_info(f"  Enabled: {wave.enabled}")
            
        else:
            carb.log_error("✗ Wave controller not found in animation controller!")
    else:
        carb.log_error(f"Failed to create tendroids: {message}")
    
    carb.log_info("\n" + "=" * 60)
    carb.log_info("TEST COMPLETE - Wave controls should update in real-time")
    carb.log_info("=" * 60)


if __name__ == "__main__":
    test_ui_wave_integration()
