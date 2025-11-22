"""
Wave controller for synchronized ocean current effects

Controls global wave state affecting tendroids and bubbles.
"""

import math
from dataclasses import dataclass


@dataclass
class WaveConfig:
    """Configuration for wave motion parameters."""
    
    amplitude: float = 8.0          # Max horizontal displacement at tip
    frequency: float = 0.15         # Waves per second
    direction: tuple = (1.0, 0.0, 0.3)  # Wave direction [x, y, z]
    
    base_response: float = 0.0      # No movement at base (anchored)
    tip_response: float = 1.0       # Full movement at tip
    
    debug_logging: bool = False


class WaveController:
    """
    Global wave controller for synchronized ocean current.
    
    Creates gentle back-and-forth motion for tendroids and bubbles.
    """
    
    def __init__(self, config: WaveConfig = None):
        """
        Initialize wave controller.
        
        Args:
            config: WaveConfig or None for defaults
        """
        self.config = config or WaveConfig()
        self.wave_time = 0.0
        self.enabled = True
        
        # Normalize direction
        dx, dy, dz = self.config.direction
        mag = math.sqrt(dx*dx + dy*dy + dz*dz)
        if mag > 0:
            self.config.direction = (dx/mag, dy/mag, dz/mag)
    
    def update(self, dt: float):
        """Update wave time."""
        if self.enabled:
            self.wave_time += dt
    
    def get_displacement(self, world_pos: tuple, tendroid_id: int = 0) -> tuple:
        """
        Calculate wave displacement at world position.
        
        Args:
            world_pos: (x, y, z) world position
            tendroid_id: Unique ID (unused, kept for API compatibility)
        
        Returns:
            (dx, dy, dz) displacement vector
        """
        if not self.enabled:
            return (0.0, 0.0, 0.0)
        
        x, y, z = world_pos
        
        # Spatial phase (wave traveling through field)
        spatial_phase = x * 0.005 + z * 0.003
        
        # Temporal phase
        temporal_phase = self.wave_time * self.config.frequency * 2 * math.pi
        
        phase = spatial_phase + temporal_phase
        wave_value = math.sin(phase)
        
        # Apply amplitude and direction
        dx = wave_value * self.config.amplitude * self.config.direction[0]
        dy = 0.0
        dz = wave_value * self.config.amplitude * self.config.direction[2]
        
        return (dx, dy, dz)
    
    def get_segment_factor(self, height_ratio: float) -> float:
        """
        Calculate wave influence factor for a height along tendroid.
        
        Args:
            height_ratio: 0.0 (base) to 1.0 (tip)
        
        Returns:
            Influence factor from base_response to tip_response
        """
        # Smooth cubic interpolation
        t = height_ratio
        factor = t * t * (3.0 - 2.0 * t)
        
        base = self.config.base_response
        tip = self.config.tip_response
        return base + factor * (tip - base)
    
    def reset(self):
        """Reset wave time to zero."""
        self.wave_time = 0.0
