"""
Test POC Bubble-Guided Deformation (Warp GPU Accelerated)

Run in Omniverse Script Editor (Window > Script Editor)
"""

import carb

poc = None

def run_poc():
    global poc
    
    if poc is not None:
        try:
            poc.cleanup()
        except:
            pass
    
    try:
        from qixotic.tendroids.poc import WarpController
        
        poc = WarpController()
        
        if poc.start():
            carb.log_warn("=" * 60)
            carb.log_warn("  POC: Warp GPU-Accelerated Deformation")
            carb.log_warn("=" * 60)
            carb.log_warn("  Performance: ~0.7ms/frame (1480 theoretical fps)")
            carb.log_warn("  Display capped by VSync at 75fps")
            carb.log_warn("")
            carb.log_warn("  Controls: poc.stop() / poc.reset_bubble() / poc.clear()")
            carb.log_warn("=" * 60)
            return True
        else:
            carb.log_error("Failed to start POC")
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

run_poc()
