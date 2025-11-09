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
    max_attempts: int = 100
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
    positions = []  # Track (x, z, radius) for interference checking
    width, depth = spawn_area
    
    for i in range(count):
      # Initialize variables before loop to satisfy IDE warnings
      x = 0.0
      z = 0.0
      radius = radius_range[0]  # Default to minimum radius
      length = radius * 2.0 * 8.0  # Default to 8:1 aspect ratio
      
      attempt = 0
      position_found = False
      
      while attempt < max_attempts and not position_found:
        # Random position within spawn area
        x = random.uniform(-width / 2, width / 2)
        z = random.uniform(-depth / 2, depth / 2)
        
        # Random radius
        radius = random.uniform(*radius_range)
        
        # 8:1 aspect ratio with ±0.5 variation (7.5:1 to 8.5:1)
        aspect_ratio = random.uniform(7.5, 8.5)
        length = radius * 2.0 * aspect_ratio  # diameter * aspect_ratio
        
        # Check interference with existing Tendroids
        if TendroidFactory._check_interference(x, z, radius, positions):
          position_found = True
          positions.append((x, z, radius))
        else:
          attempt += 1
      
      if not position_found:
        carb.log_warn(
          f"[TendroidFactory] Could not find non-interfering position for Tendroid {i} "
          f"after {max_attempts} attempts"
        )
        # Place anyway with last attempted position
        positions.append((x, z, radius))
      
      # Create Tendroid
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
          f"R={radius:.1f}, L={length:.1f} (aspect={length/(radius*2):.1f}:1)"
        )
      else:
        carb.log_warn(f"[TendroidFactory] Failed to create Tendroid {i}")
    
    carb.log_info(
      f"[TendroidFactory] Created {len(tendroids)}/{count} Tendroids in batch"
    )
    return tendroids
  
  @staticmethod
  def _check_interference(
    x: float,
    z: float,
    radius: float,
    existing_positions: list,
    proximity_threshold: float = 100.0
  ) -> bool:
    """
    Check if position interferes with existing Tendroids.
    
    Only checks pairs within proximity_threshold for efficiency.
    Requires minimum separation of 1.5 * (radius1 + radius2).
    
    Args:
        x: X position of new Tendroid
        z: Z position of new Tendroid
        radius: Radius of new Tendroid
        existing_positions: List of (x, z, radius) tuples
        proximity_threshold: Only check interference within this distance
    
    Returns:
        True if position is valid (no interference), False if interferes
    """
    for ex, ez, er in existing_positions:
      # Calculate distance between centers
      dx = x - ex
      dz = z - ez
      distance = math.sqrt(dx * dx + dz * dz)
      
      # Only check interference if within proximity threshold
      if distance < proximity_threshold:
        # Minimum separation: 1.5 * sum of radii
        min_separation = 1.5 * (radius + er)
        
        if distance < min_separation:
          return False  # Interference detected
    
    return True  # No interference
