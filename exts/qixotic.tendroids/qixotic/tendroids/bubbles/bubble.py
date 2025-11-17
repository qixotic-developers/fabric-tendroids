"""
Individual bubble instance

Represents a single bubble with position, velocity, and lifecycle.
"""

import carb
from pxr import Gf
import math


class Bubble:
  """
  Single bubble instance with physics and lifecycle.
  
  Tracks position, velocity, age, and handles USD prim creation/updates.
  """
  
  def __init__(
    self,
    bubble_id: str,
    initial_position: tuple,
    diameter: float,
    config,
    stage
  ):
    """
    Initialize bubble.
    
    Args:
        bubble_id: Unique identifier
        initial_position: (x, y, z) spawn position
        diameter: Bubble diameter
        config: BubbleConfig instance
        stage: USD stage
    """
    self.bubble_id = bubble_id
    self.position = list(initial_position)
    self.diameter = diameter
    self.config = config
    self.stage = stage
    
    # Physics state
    self.velocity = [0.0, config.rise_speed, 0.0]
    self.drift_phase = 0.0
    self.wobble_phase = 0.0
    
    # Lifecycle
    self.age = 0.0
    self.is_alive = True
    
    # USD reference
    self.prim_path = None
    self.prim = None
    
    if config.debug_logging:
      carb.log_info(
        f"[Bubble] Created '{bubble_id}' at {initial_position}, "
        f"diameter={diameter:.1f}"
      )
  
  def update(self, dt: float):
    """
    Update bubble physics and position.
    
    Args:
        dt: Delta time (seconds)
    """
    if not self.is_alive:
      return
    
    self.age += dt
    
    # Check lifetime
    if self.age >= self.config.max_lifetime:
      self.is_alive = False
      return
    
    # Update drift phase
    self.drift_phase += dt * self.config.wobble_frequency * 2.0 * math.pi
    
    # Update wobble phase
    self.wobble_phase += dt * self.config.wobble_frequency * 2.0 * math.pi
    
    # Calculate drift
    drift_x = math.sin(self.drift_phase) * self.config.drift_speed * dt
    drift_z = math.cos(self.drift_phase * 0.7) * self.config.drift_speed * dt
    
    # Calculate wobble (size variation)
    wobble_scale = 1.0 + math.sin(self.wobble_phase) * self.config.wobble_amplitude
    
    # Update position
    self.position[0] += drift_x
    self.position[1] += self.velocity[1] * dt
    self.position[2] += drift_z
    
    # Check despawn height
    if self.position[1] >= self.config.despawn_height:
      self.is_alive = False
      return
    
    # Update USD prim if it exists
    if self.prim and self.stage:
      from pxr import UsdGeom
      
      # Update transform
      xform = UsdGeom.Xformable(self.prim)
      xform.ClearXformOpOrder()
      
      translate_op = xform.AddTranslateOp()
      translate_op.Set(Gf.Vec3d(*self.position))
      
      scale_op = xform.AddScaleOp()
      scale_op.Set(Gf.Vec3f(wobble_scale, wobble_scale, wobble_scale))
  
  def destroy(self):
    """Remove bubble from USD stage."""
    if self.prim and self.stage:
      try:
        self.stage.RemovePrim(self.prim_path)
        if self.config.debug_logging:
          carb.log_info(f"[Bubble] Destroyed '{self.bubble_id}'")
      except Exception as e:
        carb.log_error(f"[Bubble] Failed to destroy '{self.bubble_id}': {e}")
    
    self.prim = None
    self.prim_path = None
    self.is_alive = False
