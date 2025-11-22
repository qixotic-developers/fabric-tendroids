"""
V2 Animation Controller - Update loop for tendroids and bubbles

Manages per-frame updates with wave effects and bubble system integration.
"""
from _typeshed import SupportsDunderGT, SupportsDunderLT

import carb
import time
import omni.kit.app

from ..animation import WaveController, WaveConfig


class V2AnimationController:
    """
    Controls animation lifecycle for V2 tendroids and bubbles.
    
    Manages update subscription and coordinates deformation updates.
    """
    
    def __init__(self):
        """Initialize animation controller."""
        self.tendroids = []  # List of V2Tendroid instances
        self.tendroid_data = []  # List of tendroid data dicts
        self.bubble_manager = None
        self.update_subscription = None
        self.is_running = False
        
        self._frame_count = 0
        self._absolute_time = 0.0
        
        # Wave controller
        self.wave_controller = WaveController(WaveConfig())
        
        # Profiling
        self._profiling_enabled = False
        self._profile_samples = []
        self._last_profile_time = 0
        self._profile_interval = 1.0
        self._profile_frame_start = 0
    
    def set_tendroids(self, tendroids: list, tendroid_data: list = None):
        """
        Set tendroids to animate.
        
        Args:
            tendroids: List of V2WarpTendroid instances
            tendroid_data: List of tendroid data dicts (from builder)
        """
        self.tendroids = tendroids
        self.tendroid_data = tendroid_data or []
    
    def set_bubble_manager(self, bubble_manager):
        """Set bubble manager for animation updates."""
        self.bubble_manager = bubble_manager
    
    def start(self, enable_profiling: bool = False):
        """
        Start animation loop.
        
        Args:
            enable_profiling: Enable FPS logging
        """
        if self.is_running:
            return
        
        update_stream = omni.kit.app.get_app().get_update_event_stream()
        self.update_subscription = update_stream.create_subscription_to_pop(
            self._on_update,
            name="V2AnimationController.Update"
        )
        
        self.is_running = True
        self._frame_count = 0
        self._absolute_time = 0.0
        
        self._profiling_enabled = enable_profiling
        if enable_profiling:
            self._profile_samples = []
            self._last_profile_time = time.perf_counter()
            self._profile_frame_start = 0
        
        carb.log_info("[V2AnimationController] Started")
    
    def stop(self):
        """Stop animation loop."""
        if not self.is_running:
            return
        
        if self.update_subscription:
            self.update_subscription.unsubscribe()
            self.update_subscription = None
        
        self.is_running = False
        
        if self._profiling_enabled and self._profile_samples:
            self._log_profile_summary()
        
        carb.log_info("[V2AnimationController] Stopped")
    
    def _on_update(self, event):
        """Per-frame update callback."""
        try:
            self._frame_count += 1
            
            if self._profiling_enabled:
                self._sample_performance()
            
            # Get delta time
            dt = 1.0 / 60.0
            if event and hasattr(event, 'payload'):
                payload = event.payload
                if isinstance(payload, dict):
                    dt = payload.get('dt', dt)
            
            self._absolute_time += dt
            
            # Update wave controller
            self.wave_controller.update(dt)
            
            # Update bubble manager (drives deformation)
            if self.bubble_manager:
                self.bubble_manager.update(
                    dt, 
                    self.tendroids,
                    self.wave_controller
                )
            
        except Exception as e:
            carb.log_error(f"[V2AnimationController] Update error: {e}")
            import traceback
            traceback.print_exc()
    
    def _sample_performance(self):
        """Sample FPS for profiling."""
        current_time = time.perf_counter()
        elapsed = current_time - self._last_profile_time
        
        if elapsed >= self._profile_interval:
            frames = self._frame_count - self._profile_frame_start
            fps = frames / elapsed if elapsed > 0 else 0
            
            sample = {
                'frame': self._frame_count,
                'fps': fps,
                'frame_time_ms': (elapsed / frames * 1000) if frames > 0 else 0
            }
            self._profile_samples.append(sample)
            
            bubble_info = ""
            if self.bubble_manager:
                bubble_info = f", {self.bubble_manager.get_bubble_count()} bubbles"
            
            carb.log_info(
                f"[PROFILE] Frame {self._frame_count}: "
                f"{fps:.1f} fps ({sample['frame_time_ms']:.2f} ms){bubble_info}"
            )
            
            self._last_profile_time = current_time
            self._profile_frame_start = self._frame_count
    
    def _log_profile_summary(self):
        """Log profiling summary."""
        if not self._profile_samples:
            return
        
        fps_values = [s['fps'] for s in self._profile_samples]
        avg_fps = sum(fps_values) / len(fps_values)
        min_fps = min(fps_values)
        max_fps = max(fps_values)
        
        carb.log_info("=" * 50)
        carb.log_info(f"[PROFILE] Avg: {avg_fps:.1f}, Min: {min_fps:.1f}, Max: {max_fps:.1f}")
        carb.log_info("=" * 50)
    
    def get_profile_data(self) -> dict[str, list[Any] | float | SupportsDunderLT[Any] | SupportsDunderGT[
      Any] | Any] | None:
        """Get profiling data."""
        if not self._profile_samples:
            return None
        
        fps_values = [s['fps'] for s in self._profile_samples]
        return {
            'samples': self._profile_samples,
            'avg_fps': sum(fps_values) / len(fps_values),
            'min_fps': min(fps_values),
            'max_fps': max(fps_values)
        }
    
    def shutdown(self):
        """Cleanup on shutdown."""
        self.stop()
        self.tendroids.clear()
        self.tendroid_data.clear()
