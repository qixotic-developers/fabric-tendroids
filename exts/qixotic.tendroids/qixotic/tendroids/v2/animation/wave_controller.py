"""
Wave controller for realistic tidal ocean current effects

Implements asymmetric shore surge → rest → ebb cycle with randomization.
Replaces simple sinusoidal motion with multi-phase tidal behavior.
"""

import math
import random
from dataclasses import dataclass
from enum import Enum


class WavePhase(Enum):
    """Wave cycle phases."""
    SHORE_SURGE = "shore_surge"  # Strong push toward shore (left)
    REST = "rest"                 # Return to neutral
    EBB = "ebb"                   # Gentle push seaward (right)


@dataclass
class WaveConfig:
    """Configuration for wave motion parameters."""
    
    # Global controls (exposed in UI)
    amplitude: float = 8.0          # Max horizontal displacement at tip
    frequency: float = 0.15         # Overall cycle frequency multiplier
    direction: tuple = (1.0, 0.0, 0.3)  # Wave direction [x, y, z]
    
    base_response: float = 0.0      # No movement at base (anchored)
    tip_response: float = 1.0       # Full movement at tip
    
    # Tidal phase parameters (internal)
    shore_force_min: float = 0.8    # Min force multiplier for shore surge
    shore_force_max: float = 1.2    # Max force multiplier for shore surge
    shore_duration_min: float = 1.0  # Min seconds for shore surge
    shore_duration_max: float = 2.0  # Max seconds for shore surge
    
    rest_duration_min: float = 0.5   # Min seconds for rest phase
    rest_duration_max: float = 1.5   # Max seconds for rest phase
    
    # Ebb force calculated from energy conservation
    # ebb_force * ebb_duration = shore_force * shore_duration
    
    debug_logging: bool = False


class WaveController:
    """
    Global wave controller for realistic tidal motion.
    
    Implements three-phase cycle:
    1. Shore surge - strong, quick push toward shore (left)
    2. Rest - return to neutral position
    3. Ebb - gentle, sustained push seaward (right)
    
    Each cycle uses randomized parameters for natural variation.
    """
    
    def __init__(self, config: WaveConfig = None):
        """Initialize wave controller with phase-based system."""
        self.config = config or WaveConfig()
        self.enabled = True
        
        # Normalize direction
        dx, dy, dz = self.config.direction
        mag = math.sqrt(dx*dx + dy*dy + dz*dz)
        if mag > 0:
            self.config.direction = (dx/mag, dy/mag, dz/mag)
        
        # Phase state
        self.current_phase = WavePhase.SHORE_SURGE
        self.phase_time = 0.0  # Time in current phase
        
        # Current cycle parameters (randomized each cycle)
        self.shore_force = 1.0
        self.shore_duration = 1.5
        self.rest_duration = 1.0
        self.ebb_force = 0.5
        self.ebb_duration = 3.0
        
        # Initialize first cycle
        self._randomize_cycle()
        
        # Current displacement value (-1 to +1, where -1 is shore, +1 is sea)
        self.current_displacement = 0.0

    
    def _randomize_cycle(self):
        """Generate random parameters for next cycle."""
        # Shore surge parameters
        self.shore_force = random.uniform(
            self.config.shore_force_min,
            self.config.shore_force_max
        )
        self.shore_duration = random.uniform(
            self.config.shore_duration_min,
            self.config.shore_duration_max
        )
        
        # Rest duration
        self.rest_duration = random.uniform(
            self.config.rest_duration_min,
            self.config.rest_duration_max
        )
        
        # Energy conservation: shore_force * shore_duration = ebb_force * ebb_duration
        # We want ebb to be gentler, so use lower force and longer duration
        shore_energy = self.shore_force * self.shore_duration
        
        # Target ebb force is 40-60% of shore force
        self.ebb_force = self.shore_force * random.uniform(0.4, 0.6)
        
        # Calculate ebb duration from energy balance
        if self.ebb_force > 0:
            self.ebb_duration = shore_energy / self.ebb_force
        else:
            self.ebb_duration = 3.0  # Fallback
        
        if self.config.debug_logging:
            import carb
            carb.log_info(
                f"[Wave] New cycle: shore_f={self.shore_force:.2f} "
                f"shore_t={self.shore_duration:.1f}s, "
                f"rest_t={self.rest_duration:.1f}s, "
                f"ebb_f={self.ebb_force:.2f} ebb_t={self.ebb_duration:.1f}s"
            )
    
    def update(self, dt: float):
        """Update wave phase and displacement."""
        if not self.enabled:
            return
        
        self.phase_time += dt
        
        # Phase state machine
        if self.current_phase == WavePhase.SHORE_SURGE:
            self._update_shore_surge()
        elif self.current_phase == WavePhase.REST:
            self._update_rest()
        elif self.current_phase == WavePhase.EBB:
            self._update_ebb()
    
    def _update_shore_surge(self):
        """Update shore surge phase - strong push toward shore."""
        if self.phase_time >= self.shore_duration:
            # Transition to rest
            self.current_phase = WavePhase.REST
            self.phase_time = 0.0
            return
        
        # Smooth acceleration and deceleration using sine curve
        t = self.phase_time / self.shore_duration
        # Use half sine wave for smooth start and end
        progress = math.sin(t * math.pi)
        
        # Negative displacement = toward shore (left)
        self.current_displacement = -progress * self.shore_force

    
    def _update_rest(self):
        """Update rest phase - return to neutral position."""
        if self.phase_time >= self.rest_duration:
            # Transition to ebb
            self.current_phase = WavePhase.EBB
            self.phase_time = 0.0
            return
        
        # Smooth return to zero using ease-out
        t = self.phase_time / self.rest_duration
        ease_out = 1.0 - (1.0 - t) * (1.0 - t)
        
        # Interpolate from current position to zero
        start_displacement = -self.shore_force if self.phase_time == 0 else self.current_displacement
        self.current_displacement = start_displacement * (1.0 - ease_out)
    
    def _update_ebb(self):
        """Update ebb phase - gentle push seaward."""
        if self.phase_time >= self.ebb_duration:
            # Transition to new shore surge cycle
            self.current_phase = WavePhase.SHORE_SURGE
            self.phase_time = 0.0
            self._randomize_cycle()  # New random parameters
            return
        
        # Smooth acceleration and deceleration using sine curve
        t = self.phase_time / self.ebb_duration
        progress = math.sin(t * math.pi)
        
        # Positive displacement = seaward (right)
        self.current_displacement = progress * self.ebb_force
    
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
        
        # Spatial variation - slight phase offset based on position
        # This creates gentle variation across the field for natural appearance
        spatial_phase = (x * 0.003 + z * 0.002)
        spatial_factor = 1.0 + math.sin(spatial_phase) * 0.15  # ±15% variation
        
        # Apply current displacement with spatial variation
        displacement_value = self.current_displacement * spatial_factor
        
        # Scale by amplitude and apply direction
        dx = displacement_value * self.config.amplitude * self.config.direction[0]
        dy = 0.0
        dz = displacement_value * self.config.amplitude * self.config.direction[2]
        
        return (dx, dy, dz)
    
    def get_wave_state(self) -> dict:
        """
        Get raw wave state for GPU computation.
        
        Returns dict with all values needed to compute wave displacement
        on GPU, avoiding per-tendroid Python calls.
        
        Returns:
            {
                'displacement': float,  # Current -1 to +1 value
                'amplitude': float,     # Max displacement
                'dir_x': float,         # Direction X component
                'dir_z': float,         # Direction Z component  
                'enabled': bool
            }
        """
        return {
            'displacement': self.current_displacement,
            'amplitude': self.config.amplitude,
            'dir_x': self.config.direction[0],
            'dir_z': self.config.direction[2],
            'enabled': self.enabled
        }
    
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
        """Reset to start of shore surge with new random parameters."""
        self.current_phase = WavePhase.SHORE_SURGE
        self.phase_time = 0.0
        self.current_displacement = 0.0
        self._randomize_cycle()
    
    def get_phase_info(self) -> dict:
        """Get current phase information for debugging/UI."""
        return {
            'phase': self.current_phase.value,
            'phase_time': self.phase_time,
            'displacement': self.current_displacement,
            'shore_force': self.shore_force,
            'shore_duration': self.shore_duration,
            'ebb_force': self.ebb_force,
            'ebb_duration': self.ebb_duration,
        }
