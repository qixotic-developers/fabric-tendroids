"""
Tendroid factory for creation and parameter setup

Handles spawning logic with position randomization and parameter variations.
"""

import carb
import random
from ..core.tendroid import Tendroid


class TendroidFactory:
  """
  Factory for creating Tendroids with randomized or specific parameters.
  
  Provides methods for both single and batch Tendroid creation
  with consistent parameter handling.
  """
  
  @staticmethod
  def create_single(
    stage,
    parent_path: str = "/World/Tendroids",
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    num_segments: int = 32,
    bulge_length_percent: float = 40.0,
    amplitude: float = 0.35,
    wave_speed: float = 40.0,
    cycle_delay: float = 2.0
  ) -> Tendroid | None:
    """
    Create a single Tendroid with custom parameters.
    
    Args:
        stage: USD stage
        parent_path: Parent prim path
        position: (x, y, z) world position
        radius: Cylinder radius
        length: Total length
        num_segments: Vertical resolution
        bulge_length_percent: Bulge size as % of length
        amplitude: Maximum radial expansion
        wave_speed: Wave travel speed
        cycle_delay: Pause between cycles
    
    Returns:
        Created Tendroid instance or None if failed
    """
    tendroid = Tendroid(
      name="Tendroid_Single",
      position=position,
      radius=radius,
      length=length,
      num_segments=num_segments
    )
    
    if tendroid.create(stage, parent_path):
      # Set custom breathing parameters
      if tendroid.breathing_animator:
        tendroid.breathing_animator.set_parameters(
          bulge_length_percent=bulge_length_percent,
          amplitude=amplitude,
          wave_speed=wave_speed,
          cycle_delay=cycle_delay
        )
      
      carb.log_info(
        f"[TendroidFactory] Created single: "
        f"R={radius:.1f}, L={length:.1f}, "
        f"Wave={bulge_length_percent:.0f}%, "
        f"Amp={amplitude:.2f}, Speed={wave_speed:.0f}"
      )
      return tendroid
    
    carb.log_error("[TendroidFactory] Failed to create single Tendroid")
    return None
  
  @staticmethod
  def create_batch(
    stage,
    count: int = 15,
    parent_path: str = "/World/Tendroids",
    spawn_area: tuple = (200, 200),
    radius_range: tuple = (8, 12),
    length_range: tuple = (80, 120),
    num_segments: int = 16
  ) -> list:
    """
    Create multiple Tendroids with randomized positions and sizes.
    
    Args:
        stage: USD stage
        count: Number of Tendroids to create
        parent_path: Parent prim path
        spawn_area: (width, depth) of spawning area
        radius_range: (min, max) radius for variation
        length_range: (min, max) length for variation
        num_segments: Segments per Tendroid
    
    Returns:
        List of created Tendroid instances
    """
    tendroids = []
    width, depth = spawn_area
    
    for i in range(count):
      # Random position within spawn area
      x = random.uniform(-width / 2, width / 2)
      z = random.uniform(-depth / 2, depth / 2)
      y = 0  # Ground level
      
      # Random size variation
      radius = random.uniform(*radius_range)
      length = random.uniform(*length_range)
      
      # Create Tendroid
      tendroid = Tendroid(
        name=f"Tendroid_{i:02d}",
        position=(x, y, z),
        radius=radius,
        length=length,
        num_segments=num_segments
      )
      
      if tendroid.create(stage, parent_path):
        tendroids.append(tendroid)
      else:
        carb.log_warn(f"[TendroidFactory] Failed to create Tendroid {i}")
    
    carb.log_info(f"[TendroidFactory] Created {len(tendroids)} Tendroids in batch")
    return tendroids
