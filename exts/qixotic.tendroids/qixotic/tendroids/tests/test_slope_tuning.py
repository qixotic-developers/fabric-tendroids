"""
Test script to find optimal bulge_width (deformation slope)

EDIT THE VALUE BELOW AND RE-RUN TO TEST DIFFERENT SLOPES:
"""

# ============================================
# EDIT THIS VALUE AND RE-RUN THE SCRIPT
BULGE_WIDTH = 1.2   # Try: 1.0, 0.9, 0.8, 0.7
VISUAL_SCALE = 0.95  # Try: 0.90, 0.85 if clipping
# ============================================

import carb

poc = None

def run_poc():
    global poc
    
    if poc is not None:
        try:
            poc.cleanup()
        except:
            pass
    
    from qixotic.tendroids.poc import POCController, POCDeformer
    
    poc = POCController()
    
    # Override visual scale before start
    poc.start()
    
    # Override deformer with custom bulge_width
    amplitude = (poc.max_bubble_radius - poc.cylinder_radius) / poc.cylinder_radius
    poc.deformer = POCDeformer(
        cylinder_radius=poc.cylinder_radius,
        cylinder_length=poc.cylinder_length,
        max_bulge_amplitude=amplitude,
        bulge_width=BULGE_WIDTH
    )
    
    # Override visual scale
    if poc._bubble_visual:
        poc._bubble_visual._visual_scale = VISUAL_SCALE
    
    poc.reset_bubble()
    
    carb.log_warn("=" * 60)
    carb.log_warn(f"  SLOPE TEST: bulge_width={BULGE_WIDTH}, visual_scale={VISUAL_SCALE}")
    carb.log_warn("=" * 60)
    carb.log_warn("  Edit BULGE_WIDTH at top of script and re-run")
    carb.log_warn("  Lower = steeper slope (more clipping risk)")
    carb.log_warn("=" * 60)

run_poc()
