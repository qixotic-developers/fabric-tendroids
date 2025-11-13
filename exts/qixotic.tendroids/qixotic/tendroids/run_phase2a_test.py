"""
Phase 2A Test Runner - Add button to UI for easy testing

Run from USD Composer Script Editor:
    from qixotic.tendroids.run_phase2a_test import run_test
    anim_controller = run_test()
    
To stop animation:
    anim_controller.stop()
"""

import carb
import omni.usd
from qixotic.tendroids.test_phase2a_integration import test_vertex_deform_integration


def run_test():
    """
    Run Phase 2A integration test.
    
    Creates 3 Tendroids with VERTEX_DEFORM animation mode and starts animation.
    
    Returns:
        AnimationController instance - IMPORTANT: Store this to keep animation running!
    """
    try:
        carb.log_info("=" * 80)
        carb.log_info("Starting Phase 2A Integration Test...")
        carb.log_info("=" * 80)
        
        # Get current stage
        stage = omni.usd.get_context().get_stage()
        
        if not stage:
            carb.log_error("No stage found! Create or open a stage first.")
            return None
        
        # Run test
        anim_controller = test_vertex_deform_integration(stage)
        
        carb.log_info("🎬 Test complete! Tendroids should be breathing now!")
        carb.log_info("To stop animation: anim_controller.stop()")
        
        return anim_controller
    
    except Exception as e:
        carb.log_error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# Make it easy to run from console
if __name__ == "__main__":
    run_test()
