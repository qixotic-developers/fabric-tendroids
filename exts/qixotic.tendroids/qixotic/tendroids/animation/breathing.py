"""
Breathing animation controller for Tendroids

Manages traveling wave timing and parameters for smooth breathing effect.
Wave starts above the flared base and travels upward.
"""

import carb
from ..utils.math_helpers import calculate_wave_position


class BreathingAnimator:
    """
    Controls breathing wave animation timing and parameters.
    
    Calculates wave center position and determines when to emit bubbles
    as the wave reaches the top of the Tendroid.
    """

    def __init__(
        self,
        length: float,
        deform_start_height: float,
        wave_speed: float = 40.0,
        wave_length: float = 30.0,
        amplitude: float = 0.25,
        cycle_delay: float = 2.0
    ):
        """
        Initialize breathing animator.
        
        Args:
            length: Total Tendroid length
            deform_start_height: Y position where wave deformation begins
            wave_speed: Wave travel speed (units/second)
            wave_length: Wavelength for falloff calculation
            amplitude: Maximum radial expansion (0.25 = 25%)
            cycle_delay: Pause between breathing cycles (seconds)
        """
        self.length = length
        self.deform_start_height = deform_start_height
        self.wave_speed = wave_speed
        self.wave_length = wave_length
        self.amplitude = amplitude
        self.cycle_delay = cycle_delay
        
        # Calculate timing
        travel_distance = (length - deform_start_height) + wave_length
        self.travel_time = travel_distance / wave_speed
        self.cycle_duration = self.travel_time + cycle_delay
        
        # State
        self.time = 0.0
        self.last_bubble_time = -999.0
        
        carb.log_info(
            f"[BreathingAnimator] Initialized: speed={wave_speed}, "
            f"length={wave_length}, cycle={self.cycle_duration:.2f}s"
        )

    def update(self, dt: float) -> dict:
        """
        Update animation and return wave parameters.
        
        Args:
            dt: Delta time since last update (seconds)
            
        Returns:
            Dictionary with:
                - wave_center: Current Y position of wave center
                - wave_length: Wavelength
                - amplitude: Expansion amplitude
                - active: Whether wave is currently traveling
        """
        self.time += dt
        cycle_time = self.time % self.cycle_duration
        
        # Check if in delay period
        if cycle_time >= self.travel_time:
            return {
                'wave_center': -1000.0,  # Wave off-screen
                'wave_length': self.wave_length,
                'amplitude': 0.0,  # No deformation during delay
                'active': False
            }
        
        # Calculate active wave position
        wave_center = calculate_wave_position(
            cycle_time,
            self.wave_speed,
            self.deform_start_height
        )
        
        return {
            'wave_center': wave_center,
            'wave_length': self.wave_length,
            'amplitude': self.amplitude,
            'active': True
        }

    def should_emit_bubble(self) -> bool:
        """
        Check if wave has reached top (bubble emission trigger).
        
        Returns:
            True if bubble should be emitted this frame
        """
        cycle_time = self.time % self.cycle_duration
        
        # Only emit during active wave
        if cycle_time >= self.travel_time:
            return False
        
        wave_center = calculate_wave_position(
            cycle_time,
            self.wave_speed,
            self.deform_start_height
        )
        
        # Emit when wave passes 95% of length
        top_threshold = self.length * 0.95
        
        # Prevent duplicate emissions in same cycle
        if self.time - self.last_bubble_time < self.cycle_duration * 0.5:
            return False
        
        if wave_center >= top_threshold:
            self.last_bubble_time = self.time
            return True
        
        return False

    def reset(self):
        """Reset animation to start of cycle."""
        self.time = 0.0
        self.last_bubble_time = -999.0

    def set_parameters(
        self,
        wave_speed: float = None,
        wave_length: float = None,
        amplitude: float = None,
        cycle_delay: float = None
    ):
        """Update animation parameters at runtime."""
        if wave_speed is not None:
            self.wave_speed = wave_speed
        if wave_length is not None:
            self.wave_length = wave_length
        if amplitude is not None:
            self.amplitude = amplitude
        if cycle_delay is not None:
            self.cycle_delay = cycle_delay
        
        # Recalculate timing
        travel_distance = (self.length - self.deform_start_height) + self.wave_length
        self.travel_time = travel_distance / self.wave_speed
        self.cycle_duration = self.travel_time + self.cycle_delay
