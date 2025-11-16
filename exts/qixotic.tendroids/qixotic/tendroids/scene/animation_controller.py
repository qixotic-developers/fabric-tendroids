"""
Animation controller for Tendroid updates

Manages animation lifecycle and update loop subscription.
"""

import carb
import omni.kit.app
from ..core.batch_manager import TendroidBatchManager


class AnimationController:
  """
  Controls animation lifecycle for a collection of Tendroids.
  
  Manages update subscription and frame-by-frame animation updates
  separate from scene management concerns.
  """
  
  def __init__(self):
    """Initialize animation controller."""
    self.tendroids = []
    self.update_subscription = None
    self.is_running = False
    self._frame_count = 0
    self._use_batching = False
    self._batch_manager = None
    
    carb.log_info("[AnimationController] Initialized")
  
  def set_tendroids(self, tendroids: list):
    """
    Set the collection of Tendroids to animate.
    
    Args:
        tendroids: List of Tendroid instances
    """
    self.tendroids = tendroids
    
    # If batching enabled and we have batch metadata, create batch manager
    if self._use_batching and tendroids and hasattr(tendroids[0], 'batch_metadata'):
      self._batch_manager = TendroidBatchManager(tendroids)
      carb.log_info(
        f"[AnimationController] Managing {len(tendroids)} Tendroids "
        f"in BATCHED mode"
      )
    else:
      self._batch_manager = None
      carb.log_info(
        f"[AnimationController] Managing {len(tendroids)} Tendroids "
        f"in INDIVIDUAL mode"
      )
  
  def enable_batching(self, enable: bool = True):
    """
    Enable or disable batched rendering mode.
    
    Args:
        enable: Whether to use batched rendering
    """
    self._use_batching = enable
    mode = "BATCHED" if enable else "INDIVIDUAL"
    carb.log_info(f"[AnimationController] Rendering mode set to {mode}")
  
  def start(self):
    """Start animating all Tendroids."""
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
    
    mode = "BATCHED" if self._batch_manager else "INDIVIDUAL"
    carb.log_info(
      f"[AnimationController] Animation started for {len(self.tendroids)} Tendroids "
      f"in {mode} mode"
    )
  
  def stop(self):
    """Stop animating all Tendroids."""
    if not self.is_running:
      return
    
    if self.update_subscription:
      self.update_subscription.unsubscribe()
      self.update_subscription = None
    
    self.is_running = False
    carb.log_info(f"[AnimationController] Animation stopped after {self._frame_count} frames")
  
  def _on_update(self, event):
    """
    Update callback called every frame.
    
    Args:
        event: Update event with timing information
    """
    try:
      self._frame_count += 1
      
      # Log first few frames for debugging
      if self._frame_count <= 3:
        mode = "BATCHED" if self._batch_manager else "INDIVIDUAL"
        carb.log_info(
          f"[AnimationController] Frame {self._frame_count}: "
          f"Updating {len(self.tendroids)} Tendroids ({mode} mode)"
        )
      
      # Get delta time from event payload
      dt = 1.0 / 60.0  # Default fallback
      
      if event and hasattr(event, 'payload'):
        payload = event.payload
        if isinstance(payload, dict):
          dt = payload.get('dt', dt)
        elif hasattr(payload, 'dt'):
          dt = payload.dt
      
      # Choose update path based on batching mode
      if self._batch_manager:
        self._update_batched(dt)
      else:
        self._update_individual(dt)
    
    except Exception as e:
      carb.log_error(f"[AnimationController] Update error on frame {self._frame_count}: {e}")
      import traceback
      traceback.print_exc()
  
  def _update_individual(self, dt: float):
    """
    Update Tendroids individually (original path).
    
    Args:
        dt: Delta time in seconds
    """
    active_count = 0
    for tendroid in self.tendroids:
      if tendroid.is_animation_enabled():
        tendroid.update(dt)
        active_count += 1
    
    # Log active count on first frame
    if self._frame_count == 1:
      carb.log_info(
        f"[AnimationController] {active_count}/{len(self.tendroids)} "
        f"Tendroids active (INDIVIDUAL mode)"
      )
  
  def _update_batched(self, dt: float):
    """
    Update Tendroids using batched operations.
    
    Args:
        dt: Delta time in seconds
    """
    self._batch_manager.update_all_batches(dt)
    
    # Log on first frame
    if self._frame_count == 1:
      carb.log_info(
        f"[AnimationController] Updated {len(self.tendroids)} Tendroids "
        f"using size-class batching"
      )
  
  def set_all_active(self, active: bool):
    """Enable or disable animation for all Tendroids."""
    for tendroid in self.tendroids:
      tendroid.set_active(active)
    
    status = "enabled" if active else "disabled"
    carb.log_info(f"[AnimationController] Animation {status} for all Tendroids")
  
  def is_animating(self) -> bool:
    """Check if animation is currently running."""
    return self.is_running
  
  def shutdown(self):
    """Cleanup when shutting down."""
    self.stop()
    self.tendroids.clear()
    self._batch_manager = None
    carb.log_info("[AnimationController] Shutdown complete")
