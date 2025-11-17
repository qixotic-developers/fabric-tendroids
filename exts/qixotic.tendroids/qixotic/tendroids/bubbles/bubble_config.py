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
  # Bubble diameter as fraction of max deformation diameter
  diameter_multiplier: float = 1.0
  
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
  
  # === Lifecycle ===
  # Maximum bubble lifetime (seconds)
  max_lifetime: float = 10.0
  
  # Despawn height (world units above tendroid top)
  despawn_height: float = 200.0
  
  # === Performance ===
  # Maximum active bubbles per tendroid
  max_bubbles_per_tendroid: int = 5
  
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
      diameter_multiplier=config_dict.get('diameter_multiplier', 1.0),
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
      max_lifetime=config_dict.get('max_lifetime', 10.0),
      despawn_height=config_dict.get('despawn_height', 200.0),
      max_bubbles_per_tendroid=config_dict.get('max_bubbles_per_tendroid', 5),
      debug_logging=config_dict.get('debug_logging', False)
    )


# Default configuration instance
DEFAULT_BUBBLE_CONFIG = BubbleConfig()
