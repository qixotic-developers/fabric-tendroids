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
  
  # === Emission Timing ===
  # When to start forming bubble (0.0-1.0, fraction of tendroid length)
  emission_threshold: float = 0.90
  
  # When to release bubble (0.0-1.0, fraction of tendroid length)
  release_threshold: float = 0.95
  
  # === Bubble Geometry ===
  # Bubble diameter as fraction of deformation diameter
  # NOTE: Actual value loaded from tendroids_config.json (this is just fallback)
  # Typical range: 0.5-1.5 depending on number of Tendroids
  diameter_multiplier: float = 1.2
  
  # Minimum bubble diameter (world units)
  min_diameter: float = 5.0
  
  # Maximum bubble diameter (world units)
  max_diameter: float = 20.0
  
  # Sphere resolution (vertices)
  resolution: int = 16
  
  # === Animation ===
  # Rise speed (units per second)
  rise_speed: float = 30.0
  
  # Lateral drift speed (units per second)
  drift_speed: float = 2.0
  
  # Wobble frequency (cycles per second)
  wobble_frequency: float = 0.5
  
  # Wobble amplitude (fraction of diameter)
  wobble_amplitude: float = 0.1
  
  # === Visual ===
  # Bubble color (R, G, B) 0.0-1.0
  color: tuple = (0.7, 0.9, 1.0)  # Light cyan
  
  # Opacity (0.0-1.0)
  opacity: float = 0.4
  
  # Metallic (0.0-1.0)
  metallic: float = 0.0
  
  # Roughness (0.0-1.0)
  roughness: float = 0.2
  
  # === Pop Timing ===
  # Minimum time before bubble pops (seconds)
  min_pop_time: float = 10.0
  
  # Maximum time before bubble pops (seconds)
  max_pop_time: float = 25.0
  
  # === Pop Effects ===
  # Number of spray particles per pop
  particles_per_pop: int = 6
  
  # Initial speed of spray particles (units/sec)
  particle_speed: float = 15.0
  
  # Particle lifetime (seconds)
  particle_lifetime: float = 0.5
  
  # Spray cone angle (degrees)
  particle_spread: float = 45.0
  
  # Particle size (world units)
  particle_size: float = 0.3
  
  # === Lifecycle ===
  # Maximum bubble lifetime (seconds) - now used as fallback
  max_lifetime: float = 30.0
  
  # Despawn height (world units above tendroid top)
  despawn_height: float = 200.0
  
  # === Performance ===
  # Maximum active bubbles per tendroid
  max_bubbles_per_tendroid: int = 5
  
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
      emission_threshold=config_dict.get('emission_threshold', 0.90),
      release_threshold=config_dict.get('release_threshold', 0.95),
      diameter_multiplier=config_dict.get('diameter_multiplier', 1.2),
      min_diameter=config_dict.get('min_diameter', 5.0),
      max_diameter=config_dict.get('max_diameter', 20.0),
      resolution=config_dict.get('resolution', 16),
      rise_speed=config_dict.get('rise_speed', 30.0),
      drift_speed=config_dict.get('drift_speed', 2.0),
      wobble_frequency=config_dict.get('wobble_frequency', 0.5),
      wobble_amplitude=config_dict.get('wobble_amplitude', 0.1),
      color=tuple(config_dict.get('color', [0.7, 0.9, 1.0])),
      opacity=config_dict.get('opacity', 0.4),
      metallic=config_dict.get('metallic', 0.0),
      roughness=config_dict.get('roughness', 0.2),
      min_pop_time=config_dict.get('min_pop_time', 10.0),
      max_pop_time=config_dict.get('max_pop_time', 25.0),
      particles_per_pop=config_dict.get('particles_per_pop', 6),
      particle_speed=config_dict.get('particle_speed', 15.0),
      particle_lifetime=config_dict.get('particle_lifetime', 0.5),
      particle_spread=config_dict.get('particle_spread', 45.0),
      particle_size=config_dict.get('particle_size', 0.3),
      max_lifetime=config_dict.get('max_lifetime', 30.0),
      despawn_height=config_dict.get('despawn_height', 200.0),
      max_bubbles_per_tendroid=config_dict.get('max_bubbles_per_tendroid', 5),
      max_particles=config_dict.get('max_particles', 50),
      debug_logging=config_dict.get('debug_logging', False)
    )


# Default configuration instance
DEFAULT_BUBBLE_CONFIG = BubbleConfig()
