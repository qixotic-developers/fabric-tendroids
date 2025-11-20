"""
Wave controller for synchronized ocean current effects

Controls global wave state that affects tendroids and bubbles.
"""

import math
import carb
from dataclasses import dataclass


@dataclass
class WaveConfig:
    """Configuration for wave motion parameters."""
    
    # Wave motion
    amplitude: float = 8.0          # Maximum horizontal displacement at tip
    frequency: float = 0.15         # Waves per second (slow, gentle)
    direction: tuple = (1.0, 0.0, 0.3)  # Normalized wave direction [x, y, z]
    
    # Tendroid response
    base_response: float = 0.0     # No movement at base (anchored)
    tip_response: float = 1.0      # Full movement at tip
    
    # Phase variation
    phase_offset_per_tendroid: float = 0.2  # Phase difference between tendroids
    
    # Debug
    debug_logging: bool = False


class WaveController:
    """
    Global wave controller for synchronized ocean current.
    
    Creates gentle back-and-forth motion affecting tendroids and bubbles.
    """
    
    def __init__(self, config: WaveConfig = None):
        """
        Initialize wave controller.
        
        Args:
            config: WaveConfig instance or None for defaults
        """
        self.config = config or WaveConfig()
        self.wave_time = 0.0
        self.enabled = True
        
        # Normalize direction vector
        dx, dy, dz = self.config.direction
        magnitude = math.sqrt(dx*dx + dy*dy + dz*dz)
        if magnitude > 0:
            self.config.direction = (dx/magnitude, dy/magnitude, dz/magnitude)
        
        if self.config.debug_logging:
            carb.log_info(f"[WaveController] Initialized with amplitude={self.config.amplitude}")
    
    def update(self, dt: float):
        """
        Update wave time.
        
        Args:
            dt: Delta time in seconds
        """
        if self.enabled:
            self.wave_time += dt
    
    def get_displacement(self, world_pos: tuple, tendroid_id: int = 0) -> tuple:
        """
        Calculate wave displacement at a world position.
        
        Args:
            world_pos: (x, y, z) world position
            tendroid_id: Unique ID for phase offset
            
        Returns:
            (dx, dy, dz) displacement vector
        """
        if not self.enabled:
            return (0.0, 0.0, 0.0)
        
        # Calculate phase based on position and time
        x, y, z = world_pos
        
        # Spatial phase (creates wave traveling through field)
        spatial_phase = x * 0.005 + z * 0.003
        
        # Temporal phase with per-tendroid offset
        temporal_phase = self.wave_time * self.config.frequency * 2 * math.pi
        tendroid_phase = tendroid_id * self.config.phase_offset_per_tendroid
        
        # Combined phase
        phase = spatial_phase + temporal_phase + tendroid_phase
        
        # Calculate displacement (sine wave)
        wave_value = math.sin(phase)
        
        # Apply amplitude and direction
        dx = wave_value * self.config.amplitude * self.config.direction[0]
        dy = 0.0  # No vertical displacement from waves
        dz = wave_value * self.config.amplitude * self.config.direction[2]
        
        return (dx, dy, dz)
    
    def get_segment_factor(self, segment_index: int, total_segments: int) -> float:
        """
        Calculate wave influence factor for a tendroid segment.
        
        Args:
            segment_index: Index of segment (0 = base)
            total_segments: Total number of segments
            
        Returns:
            Factor from 0.0 (base) to 1.0 (tip)
        """
        # Linear interpolation from base to tip
        factor = segment_index / (total_segments - 1) if total_segments > 1 else 0.0
        
        # Smooth curve (more natural bending)
        # Using cubic ease for more realistic flex
        factor = factor * factor * (3.0 - 2.0 * factor)
        
        return factor * self.config.tip_response + (1 - factor) * self.config.base_response
    
    def get_wave_angle(self) -> float:
        """
        Get current wave angle in radians.
        
        Useful for determining if tendroid is upright enough for bubble emission.
        
        Returns:
            Current wave angle (-pi to pi)
        """
        return self.wave_time * self.config.frequency * 2 * math.pi
    
    def is_emission_safe(self, threshold_angle: float = math.pi / 6) -> bool:
        """
        Check if tendroid is upright enough for bubble emission.
        
        Args:
            threshold_angle: Maximum tilt angle for emission (default 30 degrees)
            
        Returns:
            True if safe to emit bubbles
        """
        angle = abs(math.sin(self.get_wave_angle()))
        max_tilt = self.config.amplitude / 100.0  # Approximate tilt ratio
        return max_tilt * angle < threshold_angle
    
    def reset(self):
        """Reset wave time to zero."""
        self.wave_time = 0.0
        if self.config.debug_logging:
            carb.log_info("[WaveController] Wave time reset")
