"""
Animation controller for Tendroid updates

Manages animation lifecycle and update loop subscription.
"""

import carb
import omni.kit.app


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
    
    carb.log_info("[AnimationController] Initialized")
  
  def set_tendroids(self, tendroids: list):
    """
    Set the collection of Tendroids to animate.
    
    Args:
        tendroids: List of Tendroid instances
    """
    self.tendroids = tendroids
    carb.log_info(f"[AnimationController] Managing {len(tendroids)} Tendroids")
  
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
    carb.log_info(f"[AnimationController] Animation started for {len(self.tendroids)} Tendroids")
  
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
        carb.log_info(f"[AnimationController] Frame {self._frame_count}: Updating {len(self.tendroids)} Tendroids")
      
      # Get delta time from event payload
      dt = 1.0 / 60.0  # Default fallback
      
      if event and hasattr(event, 'payload'):
        payload = event.payload
        if isinstance(payload, dict):
          dt = payload.get('dt', dt)
        elif hasattr(payload, 'dt'):
          dt = payload.dt
      
      # Update all Tendroids
      active_count = 0
      for tendroid in self.tendroids:
        if tendroid.is_animation_enabled():
          tendroid.update(dt)
          active_count += 1
      
      # Log active count on first frame
      if self._frame_count == 1:
        carb.log_info(f"[AnimationController] {active_count}/{len(self.tendroids)} Tendroids active")
    
    except Exception as e:
      carb.log_error(f"[AnimationController] Update error on frame {self._frame_count}: {e}")
      import traceback
      traceback.print_exc()
  
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
    carb.log_info("[AnimationController] Shutdown complete")
