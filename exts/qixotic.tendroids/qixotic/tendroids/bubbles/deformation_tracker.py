"""
Deformation wave tracker for bubble synchronization

Monitors breathing wave state to coordinate bubble spawning and movement.
"""

import math


class DeformationWaveTracker:
  """
  Tracks deformation wave properties for bubble synchronization.
  
  Provides wave center position, growth state, and contraction detection
  to coordinate bubble lifecycle phases.
  """
  
  def __init__(
    self,
    cylinder_length: float,
    deform_start_height: float
  ):
    """
    Initialize wave tracker.
    
    Args:
        cylinder_length: Total cylinder length
        deform_start_height: Y position where deformation begins
    """
    self.cylinder_length = cylinder_length
    self.deform_start_height = deform_start_height
    
    # Current wave state (updated each frame)
    self.wave_center = 0.0
    self.wave_is_active = False
    self.distance_traveled = 0.0
    self.bulge_length = 0.0
    self.wave_growth_distance = 0.0
    self.max_deformation_radius = 0.0
    self.base_radius = 0.0
    self.amplitude = 0.0
  
  def update(self, wave_params: dict, base_radius: float):
    """
    Update wave state from breathing animator.
    
    Args:
        wave_params: Dict from BreathingAnimator.update()
        base_radius: Cylinder base radius
    """
    self.wave_center = wave_params['wave_center']
    self.wave_is_active = wave_params['active']
    self.distance_traveled = wave_params.get('distance_traveled', 0.0)
    self.bulge_length = wave_params['bulge_length']
    self.wave_growth_distance = wave_params['wave_growth_distance']
    self.base_radius = base_radius
    self.amplitude = wave_params['amplitude']
    
    # Calculate current max deformation radius
    growth_factor = self._calculate_growth_factor()
    self.max_deformation_radius = base_radius * (1.0 + self.amplitude * growth_factor)
  
  def _calculate_growth_factor(self) -> float:
    """
    Calculate wave growth factor (0.0 to 1.0).
    
    Wave grows from 0 to full size over wave_growth_distance.
    
    Returns:
        Growth factor (0.0 = not grown, 1.0 = full size)
    """
    if self.distance_traveled <= 0.0:
      return 0.0
    
    if self.distance_traveled >= self.wave_growth_distance:
      return 1.0
    
    # Smooth growth curve
    progress = self.distance_traveled / self.wave_growth_distance
    return progress ** 0.5  # Square root for gradual start
  
  def should_spawn_bubble(self) -> tuple:
    """
    Check if bubble should spawn at current wave position.
    
    Spawns when wave is in upper portion of cylinder.
    Bubble starts small (cylinder diameter) and will grow.
    
    Returns:
        (should_spawn, spawn_y_position, initial_diameter)
    """
    if not self.wave_is_active:
      return (False, 0.0, 0.0)
    
    # Spawn when wave reaches upper 20% of cylinder (80% height)
    spawn_threshold = self.cylinder_length * 0.80
    
    if self.wave_center >= spawn_threshold:
      # Start with cylinder diameter - bubble will grow
      initial_diameter = self.base_radius * 2.0
      return (True, self.wave_center, initial_diameter)
    
    return (False, 0.0, 0.0)
  
  def get_bubble_diameter_at_position(self, bubble_center_y: float) -> float:
    """
    Calculate conservative bubble diameter that fits inside cylinder at given Y position.
    
    Returns a base diameter (slightly smaller than cylinder interior).
    Caller applies diameter_multiplier for final sizing.
    
    Args:
        bubble_center_y: Y position of bubble center
    
    Returns:
        Conservative base bubble diameter before multiplier
    """
    if not self.wave_is_active:
      return self.base_radius * 2.0
    
    # Get deformation radius at bubble center
    deform_radius = self.get_deformation_at_height(bubble_center_y, self.base_radius)
    
    # Return conservative diameter (80% of deformation diameter)
    # This leaves room for diameter_multiplier to tune up to ~1.25x
    # Base: 0.8 * deform_diameter = safe
    # With multiplier 1.25: 0.8 * 1.25 = 1.0 (perfect fit)
    return deform_radius * 2.0 * 0.8
  
  def should_release_bubble(self, bubble_center_y: float, bubble_radius: float) -> bool:
    """
    Check if bubble should be released (convert to sphere).
    
    Release when TOP of bubble clears cylinder top.
    
    Args:
        bubble_center_y: Y position of bubble center
        bubble_radius: Current bubble radius
    
    Returns:
        True if bubble top is above cylinder top
    """
    bubble_top = bubble_center_y + bubble_radius
    cylinder_top = self.deform_start_height + self.cylinder_length
    
    return bubble_top >= cylinder_top
  
  def is_wave_contracting(self) -> bool:
    """
    Detect if wave is contracting (past peak).
    
    Returns:
        True if wave is shrinking back toward minimum diameter
    """
    if not self.wave_is_active:
      return False
    
    # Wave contracts when it's traveled beyond growth distance
    # and approaching cylinder top (where it shrinks to zero)
    top_approach_distance = self.cylinder_length - self.wave_center
    
    # If wave is within 1 bulge_length of top, it's contracting
    return top_approach_distance < self.bulge_length
  
  def get_deformation_at_height(self, y_position: float, base_radius: float) -> float:
    """
    Calculate deformation radius at specific Y position.
    
    Args:
        y_position: Y coordinate to check
        base_radius: Cylinder base radius
    
    Returns:
        Deformed radius at that height
    """
    if not self.wave_is_active:
      return base_radius
    
    # Distance from wave center
    distance_from_center = abs(y_position - self.wave_center)
    
    # Check if within bulge influence
    half_bulge = self.bulge_length / 2.0
    
    if distance_from_center > half_bulge:
      return base_radius
    
    # Smooth falloff using cosine
    normalized_distance = distance_from_center / half_bulge
    falloff = (math.cos(normalized_distance * math.pi) + 1.0) / 2.0
    
    # Apply growth factor
    growth_factor = self._calculate_growth_factor()
    
    # Calculate deformed radius
    max_radius = base_radius * (1.0 + self.amplitude * growth_factor)
    deformed_radius = base_radius + (max_radius - base_radius) * falloff
    
    return deformed_radius
