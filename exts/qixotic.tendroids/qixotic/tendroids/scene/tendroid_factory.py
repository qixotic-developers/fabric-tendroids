"""
Tendroid factory for creation and parameter setup

Handles spawning logic with position randomization, interference checking, and parameter variations.
"""

import carb
import random
import math
from ..core.tendroid import Tendroid


class TendroidFactory:
  """
  Factory for creating Tendroids with randomized or specific parameters.
  
  Provides methods for both single and batch Tendroid creation
  with consistent parameter handling and interference checking.
  """
  
  # Flare multiplier matches cylinder_generator settings
  FLARE_RADIUS_MULTIPLIER = 2.0
  
  @staticmethod
  def create_single(
    stage,
    parent_path: str = "/World/Tendroids",
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    num_segments: int = 32,
    bulge_length_percent: float = 40.0,
    amplitude: float = 0.5,
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
    num_segments: int = 16,
    max_attempts: int = 200
  ) -> list:
    """
    Create multiple Tendroids with randomized positions and sizes.
    Uses 8:1 aspect ratio (±0.5 variation) and interference checking.
    
    Args:
        stage: USD stage
        count: Number of Tendroids to create
        parent_path: Parent prim path
        spawn_area: (width, depth) of spawning area
        radius_range: (min, max) radius for variation
        num_segments: Segments per Tendroid
        max_attempts: Maximum position attempts per Tendroid
    
    Returns:
        List of created Tendroid instances
    """
    tendroids = []
    positions = []  # Track (x, z, base_radius) for interference checking
    width, depth = spawn_area
    
    for i in range(count):
      # Initialize variables before loop to satisfy IDE warnings
      x = 0.0
      z = 0.0
      radius = radius_range[0]  # Default to minimum radius
      length = radius * 2.0 * 8.0  # Default to 8:1 aspect ratio
      base_radius = radius * TendroidFactory.FLARE_RADIUS_MULTIPLIER
      
      attempt = 0
      position_found = False
      
      while attempt < max_attempts and not position_found:
        # Random position within spawn area
        x = random.uniform(-width / 2, width / 2)
        z = random.uniform(-depth / 2, depth / 2)
        
        # Random radius
        radius = random.uniform(*radius_range)
        
        # Calculate actual base radius (flared)
        base_radius = radius * TendroidFactory.FLARE_RADIUS_MULTIPLIER
        
        # 8:1 aspect ratio with ±0.5 variation (7.5:1 to 8.5:1)
        aspect_ratio = random.uniform(7.5, 8.5)
        length = radius * 2.0 * aspect_ratio  # diameter * aspect_ratio
        
        # Check interference using base radius
        if TendroidFactory._check_interference(x, z, base_radius, positions):
          position_found = True
          positions.append((x, z, base_radius))
        else:
          attempt += 1
      
      if not position_found:
        carb.log_warn(
          f"[TendroidFactory] Skipping Tendroid {i} - could not find "
          f"non-interfering position after {max_attempts} attempts. "
          f"Try increasing spawn_area or reducing count."
        )
        continue  # Skip this tendroid instead of forcing placement
      
      # Create Tendroid with valid position
      tendroid = Tendroid(
        name=f"Tendroid_{i:02d}",
        position=(x, 0, z),  # y=0 is ground level
        radius=radius,
        length=length,
        num_segments=num_segments
      )
      
      if tendroid.create(stage, parent_path):
        tendroids.append(tendroid)
        carb.log_info(
          f"[TendroidFactory] Tendroid_{i:02d}: "
          f"R={radius:.1f}, Base={base_radius:.1f}, L={length:.1f} "
          f"(aspect={length/(radius*2):.1f}:1)"
        )
      else:
        # Failed to create - remove from positions list
        positions.pop()
        carb.log_warn(f"[TendroidFactory] Failed to create Tendroid {i}")
    
    carb.log_info(
      f"[TendroidFactory] Created {len(tendroids)}/{count} Tendroids in batch"
    )
    return tendroids
  
  @staticmethod
  def _check_interference(
    x: float,
    z: float,
    base_radius: float,
    existing_positions: list,
    spacing_multiplier: float = 1.2
  ) -> bool:
    """
    Check if position interferes with existing Tendroids.
    
    Uses base (flared) radius for accurate spacing calculation.
    Requires minimum separation of spacing_multiplier * (base_radius1 + base_radius2).
    
    Args:
        x: X position of new Tendroid
        z: Z position of new Tendroid
        base_radius: Flared base radius of new Tendroid
        existing_positions: List of (x, z, base_radius) tuples
        spacing_multiplier: Spacing factor (1.2 = 20% gap between bases)
    
    Returns:
        True if position is valid (no interference), False if interferes
    """
    for ex, ez, existing_base_radius in existing_positions:
      # Calculate distance between centers
      dx = x - ex
      dz = z - ez
      distance = math.sqrt(dx * dx + dz * dz)
      
      # Minimum separation based on flared base radii
      min_separation = spacing_multiplier * (base_radius + existing_base_radius)
      
      if distance < min_separation:
        return False  # Interference detected
    
    return True  # No interference
