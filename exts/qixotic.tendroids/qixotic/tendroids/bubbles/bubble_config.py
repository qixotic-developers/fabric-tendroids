"""
Bubble configuration and constants

Defines all tunable parameters for bubble system.
"""

from dataclasses import dataclass


@dataclass
class BubbleConfig:
  """
  Configuration for bubble emission and animation.
  
  All parameters are tunable for realistic appearance.
  """
  
  # === Emission & Release ===
  # When to start forming bubble (0.0-1.0, fraction of tendroid length)
  emission_threshold: float = 0.90
  
  # When to release bubble (0.0-1.0, fraction of tendroid length)
  release_threshold: float = 0.95
  
  # === Bubble Geometry ===
  # Bubble diameter as fraction of deformation diameter
  diameter_multiplier: float = 1.1
  
  # Minimum/maximum bubble diameter (world units)
  min_diameter: float = 5.0
  max_diameter: float = 20.0
  
  # Sphere resolution (vertices)
  resolution: int = 16
  
  # === Motion ===
  # Rise speed (units per second)
  rise_speed: float = 60.0
  
  # Lateral drift speed (units per second)
  drift_speed: float = 3.0
  
  # === Visual ===
  # Bubble color (R, G, B) 0.0-1.0
  color: tuple = (0.7, 0.9, 1.0)
  
  # Opacity (0.0-1.0)
  opacity: float = 0.35
  
  # Metallic (0.0-1.0)
  metallic: float = 0.0
  
  # Roughness (0.0-1.0)
  roughness: float = 0.15
  
  # === Pop Timing (Height-Based) ===
  # Minimum height above release point before bubble pops (world units)
  min_pop_height: float = 150.0
  
  # Maximum height above release point before bubble pops (world units)
  max_pop_height: float = 250.0
  
  # === Pop Effects ===
  # Number of spray particles per pop
  particles_per_pop: int = 7
  
  # Initial speed of spray particles (units/sec)
  particle_speed: float = 18.0
  
  # Particle lifetime (seconds)
  particle_lifetime: float = 2.0
  
  # Spray cone angle (degrees)
  particle_spread: float = 50.0
  
  # Particle size (world units)
  particle_size: float = 2.0
  
  # === Performance ===
  # Maximum active bubbles per tendroid
  max_bubbles_per_tendroid: int = 1
  
  # Maximum active particles total
  max_particles: int = 50
  
  # === Debug ===
  # Enable debug logging
  debug_logging: bool = False
  
  @staticmethod
  def from_json(config_dict: dict) -> 'BubbleConfig':
    """
    Create BubbleConfig from JSON configuration.
    
    Args:
        config_dict: Dictionary from JSON config
    
    Returns:
        BubbleConfig instance
    """
    return BubbleConfig(
      # Emission & Release
      emission_threshold=config_dict.get('emission_threshold', 0.90),
      release_threshold=config_dict.get('release_threshold', 0.95),
      
      # Geometry
      diameter_multiplier=config_dict.get('diameter_multiplier', 1.1),
      min_diameter=config_dict.get('min_diameter', 5.0),
      max_diameter=config_dict.get('max_diameter', 20.0),
      resolution=config_dict.get('resolution', 16),
      
      # Motion
      rise_speed=config_dict.get('rise_speed', 60.0),
      drift_speed=config_dict.get('drift_speed', 3.0),
      
      # Visual
      color=tuple(config_dict.get('color', [0.7, 0.9, 1.0])),
      opacity=config_dict.get('opacity', 0.35),
      metallic=config_dict.get('metallic', 0.0),
      roughness=config_dict.get('roughness', 0.15),
      
      # Pop Timing (Height-Based)
      min_pop_height=config_dict.get('min_pop_height', 150.0),
      max_pop_height=config_dict.get('max_pop_height', 250.0),
      
      # Pop Effects
      particles_per_pop=config_dict.get('particles_per_pop', 7),
      particle_speed=config_dict.get('particle_speed', 18.0),
      particle_lifetime=config_dict.get('particle_lifetime', 2.0),
      particle_spread=config_dict.get('particle_spread', 50.0),
      particle_size=config_dict.get('particle_size', 2.0),
      
      # Performance
      max_bubbles_per_tendroid=config_dict.get('max_bubbles_per_tendroid', 1),
      max_particles=config_dict.get('max_particles', 50),
      
      # Debug
      debug_logging=config_dict.get('debug_logging', False)
    )


# Default configuration instance
DEFAULT_BUBBLE_CONFIG = BubbleConfig()
