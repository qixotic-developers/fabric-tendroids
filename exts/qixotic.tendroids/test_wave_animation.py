"""
Test script for Phase 3: Wave Animation

Run this in Omniverse Script Editor to verify wave displacement.

Usage:
    1. Open Script Editor (Window > Script Editor)
    2. Paste this script
    3. Run it
    4. Watch tendroids sway in sync
    5. Run stop_test() to clean up
"""

from qixotic.tendroids.v2.scene.manager import V2SceneManager

# Global reference for cleanup
_test_manager = None


def run_test(count: int = 5):
    """
    Create tendroids and start wave animation.
    
    Args:
        count: Number of tendroids to create
    """
    global _test_manager
    
    # Cleanup any existing test
    if _test_manager:
        stop_test()
    
    print(f"[WaveTest] Creating {count} tendroids...")
    _test_manager = V2SceneManager()
    
    success = _test_manager.create_tendroids(count=count)
    if not success:
        print("[WaveTest] ERROR: Failed to create tendroids")
        return
    
    print(f"[WaveTest] Created {_test_manager.get_tendroid_count()} tendroids")
    print("[WaveTest] Starting animation with profiling...")
    
    _test_manager.start_animation(enable_profiling=True)
    print("[WaveTest] Animation running - watch tendroids sway!")
    print("[WaveTest] Run stop_test() to stop")


def stop_test():
    """Stop animation and cleanup."""
    global _test_manager
    
    if _test_manager:
        print("[WaveTest] Stopping animation...")
        _test_manager.stop_animation()
        
        profile = _test_manager.get_profile_data()
        if profile:
            print(f"[WaveTest] Performance: {profile['avg_fps']:.1f} avg fps")
        
        print("[WaveTest] Clearing tendroids...")
        _test_manager.clear_tendroids()
        _test_manager.shutdown()
        _test_manager = None
        print("[WaveTest] Cleanup complete")
    else:
        print("[WaveTest] No active test to stop")


# Auto-run with 5 tendroids
if __name__ == "__main__":
    run_test(5)
