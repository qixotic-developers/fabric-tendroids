"""
Tendroid factory for creation and parameter setup

Handles spawning logic with position randomization, interference checking, and parameter variations.
"""

import carb
import random
import math
from ..core.tendroid import Tendroid
from ..config import get_config_value


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
    radius: float = None,
    length: float = None,
    num_segments: int = None,
    bulge_length_percent: float = None,
    amplitude: float = None,
    wave_speed: float = None,
    cycle_delay: float = None
  ) -> Tendroid | None:
    """
    Create a single Tendroid with custom parameters.
    Uses JSON config defaults when parameters are None.
    
    Args:
        stage: USD stage
        parent_path: Parent prim path
        position: (x, y, z) world position
        radius: Cylinder radius (uses JSON default if None)
        length: Total length (uses JSON default if None)
        num_segments: Vertical resolution (uses JSON default if None)
        bulge_length_percent: Bulge size as % of length (uses JSON default if None)
        amplitude: Maximum radial expansion (uses JSON default if None)
        wave_speed: Wave travel speed (uses JSON default if None)
        cycle_delay: Pause between cycles (uses JSON default if None)
    
    Returns:
        Created Tendroid instance or None if failed
    """
    # Load defaults from JSON config
    if radius is None:
      radius = get_config_value("tendroid_geometry", "default_radius", default=10.0)
    if length is None:
      length = get_config_value("tendroid_geometry", "default_length", default=100.0)
    if num_segments is None:
      num_segments = get_config_value("tendroid_geometry", "default_num_segments", default=16)
    if bulge_length_percent is None:
      bulge_length_percent = get_config_value("tendroid_animation", "bulge_length_percent", default=40.0)
    if amplitude is None:
      amplitude = get_config_value("tendroid_animation", "amplitude", default=0.35)
    if wave_speed is None:
      wave_speed = get_config_value("tendroid_animation", "wave_speed", default=40.0)
    if cycle_delay is None:
      cycle_delay = get_config_value("tendroid_animation", "cycle_delay", default=2.0)
    
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
    count: int = None,
    parent_path: str = "/World/Tendroids",
    spawn_area: tuple = None,
    radius_range: tuple = None,
    num_segments: int = None,
    max_attempts: int = None
  ) -> list:
    """
    Create multiple Tendroids with randomized positions and sizes.
    Uses 8:1 aspect ratio (±0.5 variation) and interference checking.
    Uses JSON config defaults when parameters are None.
    
    Args:
        stage: USD stage
        count: Number of Tendroids to create (uses JSON default if None)
        parent_path: Parent prim path
        spawn_area: (width, depth) of spawning area (uses JSON default if None)
        radius_range: (min, max) radius for variation (uses JSON default if None)
        num_segments: Segments per Tendroid (uses JSON default if None)
        max_attempts: Maximum position attempts per Tendroid (uses JSON default if None)
    
    Returns:
        List of created Tendroid instances
    """
    # Load defaults from JSON config
    if count is None:
      count = get_config_value("tendroid_spawning", "default_count", default=15)
    if spawn_area is None:
      spawn_area = tuple(get_config_value("tendroid_spawning", "spawn_area", default=[200.0, 200.0]))
    if radius_range is None:
      radius_range = tuple(get_config_value("tendroid_spawning", "radius_range", default=[8.0, 12.0]))
    if num_segments is None:
      num_segments = get_config_value("tendroid_geometry", "default_num_segments", default=16)
    if max_attempts is None:
      max_attempts = get_config_value("tendroid_spawning", "max_placement_attempts", default=200)
    
    # Load flare multiplier
    flare_radius_mult = get_config_value("tendroid_geometry", "flare_radius_multiplier", default=2.0)
    
    # Load aspect ratio range
    aspect_range = get_config_value("tendroid_spawning", "aspect_ratio_range", default=[7.5, 8.5])
    
    # Load spacing multiplier
    spacing_mult = get_config_value("tendroid_spawning", "spacing_multiplier", default=1.2)
    
    tendroids = []
    positions = []  # Track (x, z, base_radius) for interference checking
    width, depth = spawn_area
    
    for i in range(count):
      # Initialize variables before loop to satisfy IDE warnings
      x = 0.0
      z = 0.0
      radius = radius_range[0]  # Default to minimum radius
      length = radius * 2.0 * 8.0  # Default to 8:1 aspect ratio
      base_radius = radius * flare_radius_mult
      
      attempt = 0
      position_found = False
      
      while attempt < max_attempts and not position_found:
        # Random position within spawn area
        x = random.uniform(-width / 2, width / 2)
        z = random.uniform(-depth / 2, depth / 2)
        
        # Random radius
        radius = random.uniform(*radius_range)
        
        # Calculate actual base radius (flared)
        base_radius = radius * flare_radius_mult
        
        # Aspect ratio with variation
        aspect_ratio = random.uniform(aspect_range[0], aspect_range[1])
        length = radius * 2.0 * aspect_ratio  # diameter * aspect_ratio
        
        # Check interference using base radius
        if TendroidFactory._check_interference(x, z, base_radius, positions, spacing_mult):
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
    spacing_multiplier: float
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
        spacing_multiplier: Spacing factor (e.g., 1.2 = 20% gap between bases)
    
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
