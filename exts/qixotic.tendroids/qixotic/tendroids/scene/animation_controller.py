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
    
    carb.log_info("[AnimationController] Initialized")
  
  def set_tendroids(self, tendroids: list):
    """
    Set the collection of Tendroids to animate.
    
    Args:
        tendroids: List of Tendroid instances
    """
    self.tendroids = tendroids
  
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
    carb.log_info("[AnimationController] Animation started")
  
  def stop(self):
    """Stop animating all Tendroids."""
    if not self.is_running:
      return
    
    if self.update_subscription:
      self.update_subscription.unsubscribe()
      self.update_subscription = None
    
    self.is_running = False
    carb.log_info("[AnimationController] Animation stopped")
  
  def _on_update(self, event):
    """
    Update callback called every frame.
    
    Args:
        event: Update event with timing information
    """
    try:
      # Get delta time (assume 60fps if not available)
      dt = 1.0 / 60.0
      if hasattr(event.payload, 'dt'):
        dt = event.payload['dt']
      
      # Update all Tendroids
      for tendroid in self.tendroids:
        tendroid.update(dt)
    
    except Exception as e:
      carb.log_error(f"[AnimationController] Update error: {e}")
  
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
    carb.log_info("[AnimationController] Shutdown complete")
