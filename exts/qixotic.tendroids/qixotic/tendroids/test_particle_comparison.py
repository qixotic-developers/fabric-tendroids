"""
Particle system performance comparison test

Tests sphere-based vs Warp GPU particle systems side-by-side.
"""

import carb
import omni.ext
import time
from qixotic.tendroids.scene import TendroidSceneManager
from qixotic.tendroids.bubbles.bubble_manager import BubbleManager
from qixotic.tendroids.bubbles.bubble_manager_enhanced import BubbleManagerEnhanced


class ParticleComparisonTest(omni.ext.IExt):
    """Test extension for comparing particle systems."""
    
    def on_startup(self, ext_id):
        """Extension startup."""
        carb.log_info("[ParticleComparison] Starting particle system comparison")
        
        # Test configuration
        self.test_mode = "warp"  # "spheres", "warp", or "both"
        self.num_tendroids = 15
        self.test_duration = 60.0  # seconds
        
        # Performance tracking
        self.start_time = None
        self.frame_count = 0
        self.fps_samples = []
        self.last_fps_time = time.time()
        
        # Create scene manager
        self.scene_manager = TendroidSceneManager()
        
        # Override bubble manager based on test mode
        self._setup_particle_system()
        
        # Create tendroids
        self._create_test_scene()
        
        # Start animation with profiling
        self.scene_manager.start_animation(enable_profiling=True)
        self.start_time = time.time()
        
        # Subscribe to update events
        import omni.kit.app
        self._update_sub = omni.kit.app.get_app().get_update_event_stream().create_subscription_to_pop(
            self._on_update, name="particle_comparison_update"
        )
        
        carb.log_warn(f"[ParticleComparison] Testing {self.test_mode.upper()} particles with {self.num_tendroids} tendroids")
    
    def _setup_particle_system(self):
        """Configure which particle system to use."""
        import omni.usd
        stage = omni.usd.get_context().get_stage()
        
        if self.test_mode == "warp":
            # Replace default bubble manager with Warp-enabled version
            if hasattr(self.scene_manager, 'bubble_manager'):
                self.scene_manager.bubble_manager.clear_all_bubbles()
                
            self.scene_manager.bubble_manager = BubbleManagerEnhanced(
                stage=stage,
                config=self.scene_manager.bubble_config,
                use_warp_particles=True
            )
            carb.log_info("[ParticleComparison] Using Warp GPU particles")
            
        elif self.test_mode == "spheres":
            # Use original sphere-based system
            if hasattr(self.scene_manager, 'bubble_manager'):
                self.scene_manager.bubble_manager.clear_all_bubbles()
                
            self.scene_manager.bubble_manager = BubbleManagerEnhanced(
                stage=stage,
                config=self.scene_manager.bubble_config,
                use_warp_particles=False
            )
            carb.log_info("[ParticleComparison] Using sphere-based particles")
    
    def _create_test_scene(self):
        """Create test tendroids in a grid."""
        grid_size = int(self.num_tendroids ** 0.5) + 1
        spacing = 50.0
        
        created = 0
        for i in range(grid_size):
            for j in range(grid_size):
                if created >= self.num_tendroids:
                    break
                
                x = (i - grid_size/2) * spacing
                z = (j - grid_size/2) * spacing
                
                success = self.scene_manager.create_single_tendroid(
                    position=(x, 0, z),
                    radius=10.0,
                    length=100.0,
                    num_segments=16,  # Reduced for performance
                    bulge_length_percent=40.0,
                    amplitude=0.35,
                    wave_speed=40.0,
                    cycle_delay=2.0 + created * 0.2  # Stagger breathing
                )
                
                if success:
                    created += 1
        
        carb.log_info(f"[ParticleComparison] Created {created} tendroids")
    
    def _on_update(self, e):
        """Update callback for performance tracking."""
        if not self.start_time:
            return
        
        # Track frames
        self.frame_count += 1
        current_time = time.time()
        
        # Calculate FPS every second
        time_delta = current_time - self.last_fps_time
        if time_delta >= 1.0:
            fps = self.frame_count / time_delta
            self.fps_samples.append(fps)
            
            # Log performance
            bubble_count = self.scene_manager.bubble_manager.get_bubble_count()
            particle_count = self.scene_manager.bubble_manager.get_particle_count()
            particle_type = self.scene_manager.bubble_manager.get_particle_system_type()
            
            carb.log_warn(
                f"[ParticleComparison] {particle_type} | "
                f"FPS: {fps:.1f} | Bubbles: {bubble_count} | Particles: {particle_count}"
            )
            
            # Reset counters
            self.frame_count = 0
            self.last_fps_time = current_time
        
        # Check test duration
        elapsed = current_time - self.start_time
        if elapsed >= self.test_duration:
            self._finish_test()
    
    def _finish_test(self):
        """Complete test and report results."""
        if not self.fps_samples:
            carb.log_error("[ParticleComparison] No FPS samples collected")
            return
        
        # Calculate statistics
        avg_fps = sum(self.fps_samples) / len(self.fps_samples)
        min_fps = min(self.fps_samples)
        max_fps = max(self.fps_samples)
        
        # Log results
        particle_type = self.scene_manager.bubble_manager.get_particle_system_type()
        
        carb.log_warn("=" * 60)
        carb.log_warn(f"PARTICLE SYSTEM COMPARISON RESULTS")
        carb.log_warn(f"System: {particle_type}")
        carb.log_warn(f"Tendroids: {self.num_tendroids}")
        carb.log_warn(f"Test Duration: {self.test_duration}s")
        carb.log_warn(f"Average FPS: {avg_fps:.1f}")
        carb.log_warn(f"Min FPS: {min_fps:.1f}")
        carb.log_warn(f"Max FPS: {max_fps:.1f}")
        carb.log_warn("=" * 60)
        
        # Write results to file
        self._write_results(particle_type, avg_fps, min_fps, max_fps)
        
        # Stop animation
        self.scene_manager.stop_animation()
    
    def _write_results(self, particle_type, avg_fps, min_fps, max_fps):
        """Write test results to file."""
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"particle_test_{self.test_mode}_{timestamp}.log"
        filepath = f"C:\\Dev\\Omniverse\\fabric-tendroids\\exts\\qixotic.tendroids\\qixotic\\tendroids\\stress_test_results\\{filename}"
        
        with open(filepath, 'w') as f:
            f.write("=" * 60 + "\n")
            f.write("PARTICLE SYSTEM PERFORMANCE TEST\n")
            f.write("=" * 60 + "\n")
            f.write(f"Date: {datetime.datetime.now()}\n")
            f.write(f"Particle System: {particle_type}\n")
            f.write(f"Tendroids: {self.num_tendroids}\n")
            f.write(f"Test Duration: {self.test_duration}s\n")
            f.write("-" * 60 + "\n")
            f.write(f"Average FPS: {avg_fps:.2f}\n")
            f.write(f"Min FPS: {min_fps:.2f}\n")
            f.write(f"Max FPS: {max_fps:.2f}\n")
            f.write(f"Samples: {len(self.fps_samples)}\n")
            f.write("=" * 60 + "\n")
        
        carb.log_info(f"[ParticleComparison] Results written to {filename}")
    
    def on_shutdown(self):
        """Extension shutdown."""
        carb.log_info("[ParticleComparison] Shutting down")
        
        # Unsubscribe from updates
        if hasattr(self, '_update_sub'):
            self._update_sub = None
        
        if hasattr(self, 'scene_manager'):
            self.scene_manager.shutdown()
