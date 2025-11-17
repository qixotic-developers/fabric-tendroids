"""
Test script for Phase 2D bubble emission system

Tests single tendroid with bubble emission.
"""

import carb
import omni.ext
from qixotic.tendroids.scene import TendroidSceneManager


class TestPhase2DBubbles(omni.ext.IExt):
    """Test extension for Phase 2D bubble system."""
    
    def on_startup(self, ext_id):
        """Extension startup."""
        carb.log_info("[TestPhase2DBubbles] Starting Phase 2D bubble test")
        
        # Create scene manager
        self.scene_manager = TendroidSceneManager()
        
        # Create single tendroid with default parameters
        # Bubble system will be auto-initialized from JSON config
        success = self.scene_manager.create_single_tendroid(
            position=(0, 0, 0),
            radius=10.0,
            length=100.0,
            num_segments=32,
            bulge_length_percent=40.0,
            amplitude=0.35,
            wave_speed=40.0,
            cycle_delay=2.0
        )
        
        if success:
            carb.log_info("[TestPhase2DBubbles] Single tendroid created")
            
            # Start animation with profiling
            self.scene_manager.start_animation(enable_profiling=True)
            carb.log_info("[TestPhase2DBubbles] Animation started - watch for bubbles!")
        else:
            carb.log_error("[TestPhase2DBubbles] Failed to create tendroid")
    
    def on_shutdown(self):
        """Extension shutdown."""
        carb.log_info("[TestPhase2DBubbles] Shutting down")
        
        if hasattr(self, 'scene_manager'):
            self.scene_manager.shutdown()
