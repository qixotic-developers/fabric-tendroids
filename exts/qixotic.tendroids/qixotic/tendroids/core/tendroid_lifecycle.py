"""
Tendroid lifecycle management

Handles activation, parameter updates, cleanup, and status queries.
"""

import carb


class TendroidLifecycle:
  """
  Manages Tendroid lifecycle operations separate from core animation logic.
  
  Provides methods for controlling Tendroid state, updating parameters,
  cleanup, and status reporting.
  """
  
  @staticmethod
  def set_active(tendroid, active: bool):
    """
    Enable/disable animation.
    
    Args:
        tendroid: Tendroid instance
        active: Whether to activate
    """
    if tendroid.material_safety and not tendroid.material_safety.is_safe_for_animation():
      carb.log_warn(
        f"[TendroidLifecycle] Cannot activate '{tendroid.name}' - "
        f"animation disabled for glass material"
      )
      return
    
    tendroid.is_active = active
  
  @staticmethod
  def set_breathing_parameters(tendroid, **kwargs):
    """
    Update breathing animation parameters.
    
    Args:
        tendroid: Tendroid instance
        **kwargs: Parameters to update
    """
    if tendroid.material_safety and not tendroid.material_safety.is_safe_for_animation():
      carb.log_warn(
        f"[TendroidLifecycle] Cannot update parameters for '{tendroid.name}' - "
        f"animation disabled for glass material"
      )
      return
    
    if tendroid.breathing_animator:
      tendroid.breathing_animator.set_parameters(**kwargs)
  
  @staticmethod
  def destroy(tendroid, stage):
    """
    Remove from stage and cleanup resources.
    
    Args:
        tendroid: Tendroid instance
        stage: USD stage
    """
    if tendroid.base_path:
      try:
        stage.RemovePrim(tendroid.base_path)
        carb.log_info(f"[TendroidLifecycle] Destroyed '{tendroid.name}'")
      except Exception as e:
        carb.log_error(f"[TendroidLifecycle] Destroy failed: {e}")
    
    if tendroid.warp_deformer:
      tendroid.warp_deformer.cleanup()
    
    tendroid.is_created = False
  
  @staticmethod
  def get_top_position(tendroid) -> tuple:
    """
    Get world position of top for bubble emission.
    
    Args:
        tendroid: Tendroid instance
    
    Returns:
        (x, y, z) position tuple
    """
    return (
      tendroid.position[0],
      tendroid.position[1] + tendroid.length,
      tendroid.position[2]
    )
  
  @staticmethod
  def is_animation_enabled(tendroid) -> bool:
    """
    Check if animation is enabled (not blocked by glass material).
    
    Args:
        tendroid: Tendroid instance
    
    Returns:
        True if animation enabled, False if blocked
    """
    if not tendroid.material_safety:
      return True
    return tendroid.material_safety.is_safe_for_animation()
  
  @staticmethod
  def get_status_message(tendroid) -> str:
    """
    Get human-readable status message.
    
    Args:
        tendroid: Tendroid instance
    
    Returns:
        Status string
    """
    if tendroid.material_safety and not tendroid.material_safety.is_safe_for_animation():
      return tendroid.material_safety.get_status_message()
    elif tendroid.is_active:
      return "✓ Active"
    else:
      return "Paused"
