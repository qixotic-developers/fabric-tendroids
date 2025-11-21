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
    
    # Growth control - even faster initial growth
    self.growth_rate = 150.0  # Units per second (increased from 100)
    self.initial_growth_boost = 5.0  # Extra speed multiplier (increased from 3.0)
    self.initial_growth_duration = 0.3  # Duration of growth boost (increased from 0.2)
    
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
    
    # Grow diameter smoothly toward target with initial boost
    diameter_diff = target_diameter - self.diameter
    
    if abs(diameter_diff) > 0.01:  # Only grow if difference is significant
      # Apply growth boost in first moments
      boost = 1.0
      if self.age < self.initial_growth_duration:
        # Smooth boost that fades out
        boost_progress = self.age / self.initial_growth_duration
        boost = self.initial_growth_boost * (1.0 - boost_progress) + 1.0
      
      # Grow/shrink toward target
      effective_growth_rate = self.growth_rate * boost
      max_change = effective_growth_rate * dt
      change = max(-max_change, min(max_change, diameter_diff))
      self.diameter += change
  
  def release(self, wave_controller=None, bubble_id=0):
    """
    Transition from locked to released state.
    
    Locks diameter and initiates sphere shape transition.
    Inherits wave momentum for realistic throw effect.
    
    Args:
        wave_controller: Optional wave controller for initial momentum
        bubble_id: Unique bubble identifier for phase offset
    """
    if self.state == self.STATE_LOCKED:
      self.state = self.STATE_RELEASED
      self.release_timer = 0.0
      self.final_diameter = self.diameter  # Lock current diameter
      
      # Initial velocity from deformation wave speed (upward)
      self.velocity = [0.0, self.deform_wave_speed, 0.0]
      
      # Add horizontal "throw" velocity from wave if available
      if wave_controller:
        wave_disp = wave_controller.get_displacement(self.position, bubble_id)
        # Convert wave displacement to initial throw velocity
        # Stronger initial throw for realistic ejection
        wave_period = 1.0 / wave_controller.config.frequency
        throw_strength = 2.0  # Strong initial throw
        self.velocity[0] = (wave_disp[0] * throw_strength) / wave_period
        self.velocity[2] = (wave_disp[2] * throw_strength) / wave_period
  
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
      
      # Bubbles get "thrown" by wave motion initially, then drift with current
      # Initial throw effect (first 0.5 seconds after release)
      throw_duration = 0.5
      throw_factor = 1.0
      if self.release_timer < throw_duration:
        # Strong initial throw that fades out
        throw_factor = 1.0 - (self.release_timer / throw_duration) * 0.5  # Fade from 1.0 to 0.5
      else:
        # After throw, gentle drift with current
        throw_factor = 0.3  # Reduced ongoing drift
      
      # Wave displacement is already a position offset, convert to velocity
      # by treating it as the desired displacement over a characteristic time
      wave_period = 1.0 / wave_controller.config.frequency  # Time for one wave cycle
      drift_velocity_x = (wave_disp[0] * throw_factor) / wave_period
      drift_velocity_z = (wave_disp[2] * throw_factor) / wave_period
      
      # Apply as velocity-based movement (add to existing velocity for momentum)
      drift_x = (self.velocity[0] * 0.95 + drift_velocity_x * 0.05) * dt  # Smooth blending
      drift_z = (self.velocity[2] * 0.95 + drift_velocity_z * 0.05) * dt
      
      # Update velocities with damping for natural deceleration
      self.velocity[0] = self.velocity[0] * 0.98 + drift_velocity_x * 0.02
      self.velocity[2] = self.velocity[2] * 0.98 + drift_velocity_z * 0.02
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
