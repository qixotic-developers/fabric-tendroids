"""
Test V2 Bubble-Guided Deformation (Warp GPU Accelerated)

Run in Omniverse Script Editor (Window > Script Editor)
"""

import carb

v2 = None

def run_v2():
    global v2
    
    if v2 is not None:
        try:
            v2.cleanup()
        except:
            pass
    
    try:
        from qixotic.tendroids.v2 import V2WarpController
        
        v2 = V2WarpController()
        
        if v2.start():
            carb.log_warn("=" * 60)
            carb.log_warn("  V2: Warp GPU-Accelerated Deformation")
            carb.log_warn("=" * 60)
            carb.log_warn("  Performance: ~0.7ms/frame (1480 theoretical fps)")
            carb.log_warn("  Display capped by VSync at 60fps")
            carb.log_warn("")
            carb.log_warn("  Controls: v2.stop() / v2.reset_bubble() / v2.clear()")
            carb.log_warn("=" * 60)
            return True
        else:
            carb.log_error("Failed to start V2")
            return False
            
    except ImportError as e:
        carb.log_error(f"Import error: {e}")
        carb.log_error("Ensure omni.warp.core extension is enabled")
        return False
    except Exception as e:
        carb.log_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

run_v2()
