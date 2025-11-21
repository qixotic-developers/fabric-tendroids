"""
Test script for Bubble-Guided Deformation POC

Run this in Omniverse Script Editor to test the proof of concept.

USAGE:
1. Open Script Editor in Omniverse (Window > Script Editor)
2. Paste this script
3. Run it (Ctrl+Enter or click Run)
4. Watch the bubble rise and the cylinder deform around it

CONTROLS (type in Script Editor after running):
  poc.stop()         - Stop animation
  poc.start()        - Resume animation  
  poc.reset_bubble() - Reset bubble to base
  poc.clear()        - Remove tendroid and bubble
  poc.cleanup()      - Same as clear()
"""

import carb

# Store reference globally for interactive control
poc = None

def run_poc():
    global poc
    
    # Clean up any existing POC
    if poc is not None:
        try:
            poc.cleanup()
        except:
            pass
    
    # Import and create POC controller
    try:
        from qixotic.tendroids.poc import POCController
        
        poc = POCController()
        
        if poc.start():
            carb.log_warn("=" * 60)
            carb.log_warn("  POC STARTED - Bubble-Guided Deformation")
            carb.log_warn("=" * 60)
            carb.log_warn("")
            carb.log_warn("  Watch the cylinder bulge follow the rising bubble")
            carb.log_warn("")
            carb.log_warn("  CONTROLS (type in Script Editor):")
            carb.log_warn("    poc.stop()         - Stop animation")
            carb.log_warn("    poc.start()        - Resume animation")
            carb.log_warn("    poc.reset_bubble() - Reset bubble to base")
            carb.log_warn("    poc.clear()        - Remove everything")
            carb.log_warn("")
            carb.log_warn("=" * 60)
            return True
        else:
            carb.log_error("Failed to start POC")
            return False
            
    except ImportError as e:
        carb.log_error(f"Import error: {e}")
        carb.log_error("Make sure the qixotic.tendroids extension is loaded")
        return False
    except Exception as e:
        carb.log_error(f"Error starting POC: {e}")
        import traceback
        traceback.print_exc()
        return False

# Run the POC
run_poc()
