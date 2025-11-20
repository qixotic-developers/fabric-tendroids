"""
Bubble physics with deformation-locked and free-rise phases

Handles two-phase bubble movement:
1. Locked phase: Bubble grows with deformation, rises with wave
2. Release phase: Bubble converts to sphere and rises independently
"""

import math


class BubblePhysics:
  """
  Two-phase bubble physics with dynamic growth.
  
  Phase 1 (Locked): Bubble diameter grows to match deformation at center position
  Phase 2 (Released): Locks to sphere shape, independent physics
  """
  
  STATE_LOCKED = 0
  STATE_RELEASED = 1
  
  def __init__(
    self,
    initial_position: tuple,
    diameter: float,
    deform_wave_speed: float,
    base_radius: float,
    config
  ):
    """
    Initialize bubble physics.
    
    Args:
        initial_position: (x, y, z) spawn position
        diameter: Initial bubble diameter (will grow)
        deform_wave_speed: Speed of deformation wave
        base_radius: Cylinder base radius
        config: BubbleConfig instance
    """
    self.position = list(initial_position)
    self.diameter = diameter  # Current diameter (grows in locked phase)
    self.base_radius = base_radius
    self.deform_wave_speed = deform_wave_speed
    self.config = config
    
    # State
    self.state = self.STATE_LOCKED
    self.age = 0.0
    
    # Shape control (for elongation in locked phase)
    self.vertical_stretch = 1.5  # Locked bubbles are elongated
    self.horizontal_scale = 1.0
    
    # Release phase - independent motion
    self.velocity = [0.0, 0.0, 0.0]
    self.drift_phase = 0.0
    self.release_acceleration_time = 0.2
    self.release_timer = 0.0
    self.shape_transition_time = 0.3  # Time to transition to sphere
    self.final_diameter = diameter  # Lock diameter at release
  
  def update_locked(self, dt: float, deform_center_y: float, target_diameter: float, mouth_position: tuple = None):
    """
    Update bubble in locked phase.
    
    Bubble rises with deformation wave, follows mouth position, and diameter grows.
    
    Args:
        dt: Delta time
        deform_center_y: Current Y position of deformation center
        target_diameter: Target diameter from deformation tracker
        mouth_position: Current (x, y, z) position of tendroid mouth including wave displacement
    """
    self.age += dt
    
    # Update position to track mouth if provided
    if mouth_position:
      self.position[0] = mouth_position[0]  # Follow X sway
      self.position[1] = deform_center_y    # Track deformation center Y
      self.position[2] = mouth_position[2]  # Follow Z sway
    else:
      # Fallback: just update Y
      self.position[1] = deform_center_y
    
    # Grow diameter smoothly toward target
    # Use smooth interpolation to avoid sudden jumps
    growth_rate = 50.0  # Units per second
    diameter_diff = target_diameter - self.diameter
    
    if abs(diameter_diff) > 0.1:
      # Grow/shrink toward target
      max_change = growth_rate * dt
      change = max(-max_change, min(max_change, diameter_diff))
      self.diameter += change
  
  def release(self):
    """
    Transition from locked to released state.
    
    Locks diameter and initiates sphere shape transition.
    """
    if self.state == self.STATE_LOCKED:
      self.state = self.STATE_RELEASED
      self.release_timer = 0.0
      self.final_diameter = self.diameter  # Lock current diameter
      
      # Initial velocity from deformation wave speed
      self.velocity = [0.0, self.deform_wave_speed, 0.0]
  
  def update_released(self, dt: float, wave_controller=None, bubble_id=0):
    """
    Update bubble in released phase.
    
    Applies squeeze-out acceleration, shape transition to sphere,
    then standard buoyant rise with wave-synchronized drift.
    
    Args:
        dt: Delta time
        wave_controller: Optional wave controller for current effects
        bubble_id: Unique bubble identifier for phase offset
    """
    self.age += dt
    
    # Squeeze-out acceleration phase
    if self.release_timer < self.release_acceleration_time:
      self.release_timer += dt
      
      # Accelerate from wave speed to rise speed
      accel_progress = self.release_timer / self.release_acceleration_time
      accel_progress = min(1.0, accel_progress)
      
      # Smooth acceleration curve (ease-out)
      accel_factor = 1.0 - (1.0 - accel_progress) ** 2
      
      target_speed = self.config.rise_speed
      current_speed = self.deform_wave_speed
      
      self.velocity[1] = current_speed + (target_speed - current_speed) * accel_factor
    else:
      # Normal buoyant rise
      self.velocity[1] = self.config.rise_speed
    
    # Shape transition to sphere
    if self.release_timer < self.shape_transition_time:
      transition_progress = self.release_timer / self.shape_transition_time
      # Ease from elongated to sphere
      self.vertical_stretch = 1.5 - (0.5 * transition_progress)
      self.horizontal_scale = 1.0
    else:
      # Fully spherical
      self.vertical_stretch = 1.0
      self.horizontal_scale = 1.0
    
    # Calculate drift - either from wave controller or default pattern
    if wave_controller:
      # Use wave controller for synchronized drift
      wave_disp = wave_controller.get_displacement(self.position, bubble_id)
      # Released bubbles drift with current but at reduced intensity
      # They're lighter and more influenced by their own buoyancy
      drift_factor = 0.2  # Only 20% of wave motion after release (was 30%)
      drift_x = wave_disp[0] * drift_factor * dt
      drift_z = wave_disp[2] * drift_factor * dt
    else:
      # Fallback to original drift pattern
      # Update drift phase (constant frequency ~0.5 Hz)
      drift_frequency = 0.5  # cycles per second
      self.drift_phase += dt * drift_frequency * 2.0 * math.pi
      
      # Calculate drift
      drift_x = math.sin(self.drift_phase) * self.config.drift_speed * dt
      drift_z = math.cos(self.drift_phase * 0.7) * self.config.drift_speed * dt
    
    # Update position
    self.position[0] += drift_x
    self.position[1] += self.velocity[1] * dt
    self.position[2] += drift_z
  
  def get_radius(self) -> float:
    """
    Get current bubble radius.
    
    Returns:
        Bubble radius (diameter / 2)
    """
    if self.state == self.STATE_RELEASED:
      return self.final_diameter / 2.0
    else:
      return self.diameter / 2.0
  
  def get_scale(self) -> tuple:
    """
    Calculate scale factors for bubble rendering.
    
    Returns base diameter scale multiplied by shape factors.
    
    Returns:
        (scale_x, scale_y, scale_z) - absolute scale values
    """
    # Base scale from diameter
    if self.state == self.STATE_RELEASED:
      base_scale = self.final_diameter / 2.0  # Sphere was created with radius=1
    else:
      base_scale = self.diameter / 2.0
    
    # Apply shape stretching
    return (
      base_scale * self.horizontal_scale,
      base_scale * self.vertical_stretch,
      base_scale * self.horizontal_scale
    )
