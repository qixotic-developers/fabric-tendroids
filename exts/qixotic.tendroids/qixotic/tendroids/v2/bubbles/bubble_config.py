"""
V2 Bubble Configuration

Dataclass with all tunable parameters for bubble system.
Loads defaults from JSON config if available.
"""

from dataclasses import dataclass
from ..config import get_config_value


@dataclass
class V2BubbleConfig:
    """Configuration for V2 bubble system."""
    
    # === Spawn & Growth ===
    spawn_height_pct: float = 0.10      # % of length where bubble spawns
    max_diameter_pct: float = 0.60      # % of length where bubble reaches max size
    diameter_multiplier: float = 1.15   # Deformation bulge size relative to bubble
                                        # > 1.0 = bulge bigger than bubble (hidden inside)
                                        # < 1.0 = bubble bigger than bulge (pokes through)
    
    # === Motion ===
    rise_speed: float = 40.0            # Units per second while inside tendroid (was 60)
    released_rise_speed: float = 40.0   # Units per second after release
    drift_speed: float = 3.0            # Lateral drift speed
    
    # === Pop Timing ===
    min_pop_height: float = 150.0       # Min height above tendroid before pop
    max_pop_height: float = 250.0       # Max height above tendroid before pop
    
    # === Visual ===
    color: tuple = (0.7, 0.9, 1.0)
    opacity: float = 0.35
    resolution: int = 16
    
    # === Pop Particles ===
    particles_per_pop: int = 10
    particle_speed: float = 18.0
    particle_lifetime: float = 2.0
    particle_size: float = 3.0
    particle_spread: float = 50.0
    
    # === Performance ===
    max_bubbles_per_tendroid: int = 1
    max_particles: int = 100
    
    # === Behavior ===
    hide_until_clear: bool = False      # Show bubble immediately (was True)
    auto_respawn: bool = True           # Auto-spawn new bubble after pop
    respawn_delay: float = 1.0          # Seconds before respawn
    
    # === Debug ===
    debug_logging: bool = False
    
    @classmethod
    def from_json_config(cls) -> 'V2BubbleConfig':
        """Create config from JSON file values."""
        def get(key, default):
            return get_config_value(f"bubble_system.{key}", default)
        
        return cls(
            diameter_multiplier=get("diameter_multiplier", 1.1),
            rise_speed=get("rise_speed", 40.0),
            drift_speed=get("drift_speed", 3.0),
            min_pop_height=get("min_pop_height", 150.0),
            max_pop_height=get("max_pop_height", 250.0),
            color=tuple(get("color", [0.7, 0.9, 1.0])),
            opacity=get("opacity", 0.35),
            resolution=get("resolution", 16),
            particles_per_pop=get("particles_per_pop", 10),
            particle_speed=get("particle_speed", 18.0),
            particle_lifetime=get("particle_lifetime", 2.0),
            particle_size=get("particle_size", 3.0),
            particle_spread=get("particle_spread", 50.0),
            max_bubbles_per_tendroid=get("max_bubbles_per_tendroid", 1),
            max_particles=get("max_particles", 100),
            hide_until_clear=get("hide_until_clear", False),
            debug_logging=get("debug_logging", False),
        )


# Default instance
DEFAULT_V2_BUBBLE_CONFIG = V2BubbleConfig()
