"""
Individual bubble instance with two-phase physics

Represents a single bubble that:
1. Starts locked to deformation wave
2. Releases when wave contracts
3. Rises independently with squeeze-out acceleration
"""

import carb
from pxr import Gf
from .bubble_physics import BubblePhysics


class Bubble:
  """
  Single bubble with deformation-synchronized physics.
  
  Lifecycle:
  - Spawn: Created when deformation first becomes visible
  - Locked: Rises with deformation wave, diameter matches max deformation
  - Released: Wave contracts, bubble accelerates and breaks free
  - Free: Independent buoyant rise with drift/wobble
  """
  
  def __init__(
    self,
    bubble_id: str,
    initial_position: tuple,
    initial_diameter: float,
    deform_wave_speed: float,
    base_radius: float,
    config,
    stage
  ):
    """
    Initialize bubble.
    
    Args:
        bubble_id: Unique identifier
        initial_position: (x, y, z) spawn position
        initial_diameter: Starting diameter (grows with deformation)
        deform_wave_speed: Speed of deformation wave
        base_radius: Cylinder base radius
        config: BubbleConfig instance
        stage: USD stage
    """
    self.bubble_id = bubble_id
    self.config = config
    self.stage = stage
    
    # Physics controller
    self.physics = BubblePhysics(
      initial_position=initial_position,
      diameter=initial_diameter,
      deform_wave_speed=deform_wave_speed,
      base_radius=base_radius,
      config=config
    )
    
    # Lifecycle
    self.is_alive = True
    
    # USD reference
    self.prim_path = None
    self.prim = None
    
    if config.debug_logging:
      carb.log_info(
        f"[Bubble] Created '{bubble_id}' at {initial_position}, "
        f"initial_diameter={initial_diameter:.1f}, wave_speed={deform_wave_speed:.1f}"
      )
  
  def update_locked(self, dt: float, deform_center_y: float, deform_radius: float):
    """
    Update bubble in locked phase.
    
    Args:
        dt: Delta time
        deform_center_y: Current Y position of deformation center
        deform_radius: Target radius (deform_radius is actually target_diameter/2)
    """
    if not self.is_alive:
      return
    
    # Convert radius back to diameter for physics update
    target_diameter = deform_radius * 2.0
    self.physics.update_locked(dt, deform_center_y, target_diameter)
    
    # Check if expired
    if self.physics.is_expired(self.config.despawn_height):
      self.is_alive = False
      return
    
    # Update USD prim
    self._update_usd_transform()
  
  def release(self):
    """Transition to released state."""
    if self.physics.state == BubblePhysics.STATE_LOCKED:
      self.physics.release()
      
      if self.config.debug_logging:
        carb.log_info(
          f"[Bubble] Released '{self.bubble_id}' at y={self.physics.position[1]:.1f}"
        )
  
  def update_released(self, dt: float):
    """
    Update bubble in released phase.
    
    Args:
        dt: Delta time
    """
    if not self.is_alive:
      return
    
    self.physics.update_released(dt)
    
    # Check if expired
    if self.physics.is_expired(self.config.despawn_height):
      self.is_alive = False
      return
    
    # Update USD prim
    self._update_usd_transform()
  
  def _update_usd_transform(self):
    """Update USD prim position and scale."""
    if not self.prim or not self.stage:
      return
    
    try:
      from pxr import UsdGeom
      
      xform = UsdGeom.Xformable(self.prim)
      xform.ClearXformOpOrder()
      
      # Position
      translate_op = xform.AddTranslateOp()
      translate_op.Set(Gf.Vec3d(*self.physics.position))
      
      # Scale (non-uniform for elongation)
      scale_x, scale_y, scale_z = self.physics.get_scale()
      scale_op = xform.AddScaleOp()
      scale_op.Set(Gf.Vec3f(scale_x, scale_y, scale_z))
    
    except Exception as e:
      carb.log_error(f"[Bubble] Failed to update transform: {e}")
  
  def is_locked(self) -> bool:
    """Check if bubble is in locked phase."""
    return self.physics.state == BubblePhysics.STATE_LOCKED
  
  def is_released(self) -> bool:
    """Check if bubble is in released phase."""
    return self.physics.state == BubblePhysics.STATE_RELEASED
  
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
