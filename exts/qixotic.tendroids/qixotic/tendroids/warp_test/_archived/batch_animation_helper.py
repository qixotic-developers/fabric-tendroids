"""
Batch Animation Helper

Manages per-tube wave parameters for batch deformation.
Handles timing, phase offsets, and parameter variations.
"""

import carb
import random


class TubeAnimation:
  """Parameters for a single tube's animation"""
  
  def __init__(
    self,
    tube_id: int,
    wave_speed: float = 40.0,
    amplitude: float = 0.35,
    cycle_delay: float = 2.0,
    phase_offset: float = 0.0
  ):
    """
    Initialize tube animation parameters.
    
    Args:
        tube_id: Unique tube identifier
        wave_speed: Wave travel speed
        amplitude: Radial expansion factor
        cycle_delay: Pause between cycles
        phase_offset: Time offset for staggered animation
    """
    self.tube_id = tube_id
    self.wave_speed = wave_speed
    self.amplitude = amplitude
    self.cycle_delay = cycle_delay
    self.phase_offset = phase_offset
    
    # Animation state
    self.time = phase_offset
    self.active = True


class BatchAnimationHelper:
  """
  Manages animation parameters for multiple tubes.
  
  Handles timing updates and provides wave parameters
  for batch GPU kernel execution.
  """
  
  def __init__(self, tube_count: int, tube_height: float):
    """
    Initialize animation manager.
    
    Args:
        tube_count: Number of tubes to animate
        tube_height: Height of each tube (uniform)
    """
    self.tube_count = tube_count
    self.tube_height = tube_height
    self.tubes = []
    
    carb.log_info(
      f"[BatchAnimationHelper] Initializing for {tube_count} tubes, "
      f"height={tube_height:.1f}"
    )
  
  def create_animations(
    self,
    vary_parameters: bool = True,
    stagger_start: bool = True
  ):
    """
    Create animation parameters for all tubes.
    
    Args:
        vary_parameters: Add slight variation to speed/amplitude
        stagger_start: Offset start times for wave effect
    """
    self.tubes.clear()
    
    for i in range(self.tube_count):
      # Base parameters
      wave_speed = 40.0
      amplitude = 0.35
      cycle_delay = 2.0
      
      # Add variation if requested
      if vary_parameters:
        wave_speed += random.uniform(-5.0, 5.0)
        amplitude += random.uniform(-0.05, 0.05)
        cycle_delay += random.uniform(-0.3, 0.3)
      
      # Stagger start times
      phase_offset = 0.0
      if stagger_start:
        phase_offset = (i / self.tube_count) * 3.0  # Spread over 3 seconds
      
      tube_anim = TubeAnimation(
        tube_id=i,
        wave_speed=wave_speed,
        amplitude=amplitude,
        cycle_delay=cycle_delay,
        phase_offset=phase_offset
      )
      
      self.tubes.append(tube_anim)
    
    carb.log_info(
      f"[BatchAnimationHelper] Created {len(self.tubes)} animations, "
      f"vary={vary_parameters}, stagger={stagger_start}"
    )
  
  def update(self, dt: float):
    """
    Update all tube animations.
    
    Args:
        dt: Delta time since last update
    """
    for tube in self.tubes:
      if tube.active:
        tube.time += dt
  
  def get_wave_parameters(self) -> tuple:
    """
    Get current wave parameters for all tubes.
    
    Returns arrays suitable for batch GPU kernel:
        (wave_centers, amplitudes, bulge_lengths, active_flags)
    """
    wave_centers = []
    amplitudes = []
    bulge_lengths = []
    active_flags = []
    
    # Fixed bulge parameters (40% of height)
    bulge_length = self.tube_height * 0.4
    
    for tube in self.tubes:
      if not tube.active:
        wave_centers.append(-1000.0)  # Off-screen
        amplitudes.append(0.0)
        bulge_lengths.append(bulge_length)
        active_flags.append(0)
        continue
      
      # Calculate wave position and cycle state
      travel_time = self.tube_height / tube.wave_speed
      cycle_duration = travel_time + tube.cycle_delay
      cycle_time = tube.time % cycle_duration
      
      if cycle_time >= travel_time:
        # In delay period
        wave_centers.append(-1000.0)
        amplitudes.append(0.0)
        active_flags.append(0)
      else:
        # Active wave
        wave_center = cycle_time * tube.wave_speed
        wave_centers.append(wave_center)
        amplitudes.append(tube.amplitude)
        active_flags.append(1)
      
      bulge_lengths.append(bulge_length)
    
    return (wave_centers, amplitudes, bulge_lengths, active_flags)
  
  def set_all_active(self, active: bool):
    """Enable/disable all animations"""
    for tube in self.tubes:
      tube.active = active
  
  def reset_all(self):
    """Reset all animations to start"""
    for tube in self.tubes:
      tube.time = tube.phase_offset
