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
    rise_speed: float = 15.0            # Units per second while inside tendroid (TESTING: slowed from 40.0)
    released_rise_speed: float = 20.0   # Units per second after release (TESTING: slowed from 40.0)
    drift_speed: float = 3.0            # Lateral drift speed
    
    # === Pop Timing ===
    min_pop_height: float = 200.0       # Min height above tendroid before pop (TESTING: raised from 150.0)
    max_pop_height: float = 350.0       # Max height above tendroid before pop (TESTING: raised from 250.0)
    
    # === Visual ===
    color: tuple = (0.7, 0.9, 1.0)
    opacity: float = 0.25            # Restored to more transparent (was 0.35)
    resolution: int = 16
    
    # === Pop Particles ===
    particles_per_pop: int = 12          # Increased from 3 for more spray (TESTING: was 10 production)
    particle_speed: float = 35.0         # Increased from 18.0 for faster spray
    particle_lifetime: float = 1.2       # Slightly longer to see farther travel
    particle_size: float = 1.5           # Reduced from 3.0 for smaller particles
    particle_spread: float = 80.0        # Increased from 50.0 for wider spray
    
    # === Performance ===
    max_bubbles_per_tendroid: int = 1
    max_particles: int = 30              # Reduced from 100
    
    # === Behavior ===
    hide_until_clear: bool = False      # Show bubble immediately (was True)
    auto_respawn: bool = True           # Auto-spawn new bubble after pop
    respawn_delay: float = 3.0          # Seconds before respawn (TESTING: increased from 1.0)
    max_concurrent_active: int = 2      # Maximum bubbles rising/exiting/released at once
    
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
