"""
Animation controller for Tendroid and bubble updates

Manages animation lifecycle and update loop subscription with bubble system.
Optional performance profiling with periodic FPS logging.
"""

import carb
import omni.kit.app
import time


class AnimationController:
    """
    Controls animation lifecycle for Tendroids and bubbles.
    
    Manages update subscription and frame-by-frame animation updates
    separate from scene management concerns. Integrates bubble system
    updates when bubble manager is provided.
    """
    
    def __init__(self, bubble_manager=None):
        """
        Initialize animation controller.
        
        Args:
            bubble_manager: Optional BubbleManager instance
        """
        self.tendroids = []
        self.bubble_manager = bubble_manager
        self.update_subscription = None
        self.is_running = False
        self._frame_count = 0
        self._absolute_time = 0.0
        
        # Performance profiling
        self._profiling_enabled = False
        self._profile_samples = []
        self._last_profile_time = 0
        self._profile_interval = 1.0  # Log every 1 second
        self._profile_frame_start = 0
    
    def set_tendroids(self, tendroids: list):
        """
        Set the collection of Tendroids to animate.
        
        Args:
            tendroids: List of Tendroid instances
        """
        self.tendroids = tendroids
    
    def set_bubble_manager(self, bubble_manager):
        """
        Set bubble manager for animation updates.
        
        Args:
            bubble_manager: BubbleManager instance
        """
        self.bubble_manager = bubble_manager
    
    def start(self, enable_profiling: bool = False):
        """
        Start animating all Tendroids and bubbles.
        
        Args:
            enable_profiling: If True, log FPS samples every second
        """
        if self.is_running:
            return
        
        # Subscribe to update events
        update_stream = omni.kit.app.get_app().get_update_event_stream()
        self.update_subscription = update_stream.create_subscription_to_pop(
            self._on_update,
            name="AnimationController.Update"
        )
        
        self.is_running = True
        self._frame_count = 0
        self._absolute_time = 0.0
        
        # Setup profiling
        self._profiling_enabled = enable_profiling
        if enable_profiling:
            self._profile_samples = []
            self._last_profile_time = time.perf_counter()
            self._profile_frame_start = 0
    
    def stop(self):
        """Stop animating all Tendroids and bubbles."""
        if not self.is_running:
            return
        
        if self.update_subscription:
            self.update_subscription.unsubscribe()
            self.update_subscription = None
        
        self.is_running = False
        
        # Log profiling summary if enabled
        if self._profiling_enabled and self._profile_samples:
            self._log_profile_summary()
    
    def _on_update(self, event):
        """
        Update callback called every frame.
        
        Args:
            event: Update event with timing information
        """
        try:
            self._frame_count += 1
            
            # Periodic profiling (low overhead)
            if self._profiling_enabled:
                self._sample_performance()
            
            # Get delta time from event payload
            dt = 1.0 / 60.0  # Default fallback
            
            if event and hasattr(event, 'payload'):
                payload = event.payload
                if isinstance(payload, dict):
                    dt = payload.get('dt', dt)
                elif hasattr(payload, 'dt'):
                    dt = payload.dt
            
            # Update absolute time
            self._absolute_time += dt
            
            # Update all active Tendroids
            for tendroid in self.tendroids:
                if tendroid.is_animation_enabled():
                    tendroid.update(dt, self._absolute_time)
            
            # Update bubble system
            if self.bubble_manager:
                self.bubble_manager.update(dt)
        
        except Exception as e:
            carb.log_error(
                f"[AnimationController] Update error on frame {self._frame_count}: {e}"
            )
            import traceback
            traceback.print_exc()
    
    def _sample_performance(self):
        """Sample FPS every profiling interval (minimal overhead)."""
        current_time = time.perf_counter()
        elapsed = current_time - self._last_profile_time
        
        if elapsed >= self._profile_interval:
            # Calculate FPS over the interval
            frames_rendered = self._frame_count - self._profile_frame_start
            fps = frames_rendered / elapsed if elapsed > 0 else 0
            
            # Store sample
            sample = {
                'timestamp': current_time,
                'frame': self._frame_count,
                'fps': fps,
                'frame_time_ms': (elapsed / frames_rendered * 1000) if frames_rendered > 0 else 0
            }
            self._profile_samples.append(sample)
            
            # Log sample with bubble count
            bubble_info = ""
            if self.bubble_manager:
                bubble_count = self.bubble_manager.get_bubble_count()
                particle_count = self.bubble_manager.get_particle_count()
                bubble_info = f", {bubble_count} bubbles, {particle_count} particles"
            
            carb.log_info(
                f"[PROFILE] Frame {self._frame_count}: "
                f"{fps:.2f} fps ({sample['frame_time_ms']:.2f} ms){bubble_info}"
            )
            
            # Reset for next interval
            self._last_profile_time = current_time
            self._profile_frame_start = self._frame_count
    
    def _log_profile_summary(self):
        """Log summary statistics from profiling session."""
        if not self._profile_samples:
            return
        
        fps_values = [s['fps'] for s in self._profile_samples]
        frame_times = [s['frame_time_ms'] for s in self._profile_samples]
        
        avg_fps = sum(fps_values) / len(fps_values)
        min_fps = min(fps_values)
        max_fps = max(fps_values)
        avg_frame_time = sum(frame_times) / len(frame_times)
        
        carb.log_info("=" * 70)
        carb.log_info("[PROFILE SUMMARY]")
        carb.log_info("=" * 70)
        carb.log_info(f"Total Samples: {len(self._profile_samples)}")
        carb.log_info(f"Total Frames: {self._frame_count}")
        carb.log_info(f"Avg FPS: {avg_fps:.2f}")
        carb.log_info(f"Min FPS: {min_fps:.2f}")
        carb.log_info(f"Max FPS: {max_fps:.2f}")
        carb.log_info(f"Avg Frame Time: {avg_frame_time:.2f} ms")
        carb.log_info("=" * 70)
    
    def get_profile_data(self):
        """
        Get collected profile data.
        
        Returns:
            Dict with profile data or None if profiling not enabled
        """
        if not self._profiling_enabled:
            return None
        
        if not self._profile_samples:
            return None
        
        fps_values = [s['fps'] for s in self._profile_samples]
        
        return {
            'samples': self._profile_samples,
            'total_frames': self._frame_count,
            'avg_fps': sum(fps_values) / len(fps_values),
            'min_fps': min(fps_values),
            'max_fps': max(fps_values)
        }
    
    def set_all_active(self, active: bool):
        """Enable or disable animation for all Tendroids."""
        for tendroid in self.tendroids:
            tendroid.set_active(active)
    
    def is_animating(self) -> bool:
        """Check if animation is currently running."""
        return self.is_running
    
    def shutdown(self):
        """Cleanup when shutting down."""
        self.stop()
        self.tendroids.clear()
