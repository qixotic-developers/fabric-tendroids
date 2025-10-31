"""
Breathing animation for Tendroids using transform-based segment scaling

Implements traveling sine wave that creates radial expansion/contraction
as it moves up the Tendroid's length.
"""

import carb
from ..utils.math_helpers import calculate_wave_position, calculate_segment_scale


class BreathingAnimator:
    """
    Manages breathing animation for a single Tendroid.
    
    Uses transform-based scaling of cylinder segments to create a traveling
    wave effect without vertex-level deformation.
    """

    def __init__(
        self,
        length: float,
        num_segments: int,
        flare_height: float,
        wave_speed: float = 50.0,
        wave_length: float = 40.0,
        amplitude: float = 0.3,
        cycle_delay: float = 2.0
    ):
        """
        Initialize breathing animator.
        
        Args:
            length: Total length of the Tendroid
            num_segments: Number of segments in the cylinder
            flare_height: Height of flared base (wave starts above this)
            wave_speed: Speed of wave travel (units/second)
            wave_length: Wavelength of the breathing wave
            amplitude: Maximum scale multiplier (e.g., 0.3 = 30% expansion)
            cycle_delay: Delay between wave cycles (seconds)
        """
        self.length = length
        self.num_segments = num_segments
        self.flare_height = flare_height
        self.wave_speed = wave_speed
        self.wave_length = wave_length
        self.amplitude = amplitude
        self.cycle_delay = cycle_delay
        
        # Calculate segment positions
        self.segment_height = length / num_segments
        self.segment_y_positions = [
            i * self.segment_height + self.segment_height / 2
            for i in range(num_segments)
        ]
        
        # Timing state
        self.time = 0.0
        self.in_delay = False
        
        # Calculate cycle timing
        wave_gap = self.wave_length * 0.18 * 3.0  # Gap before wave starts
        self.wave_start_y = flare_height + wave_gap
        travel_distance = (length - self.wave_start_y) + self.wave_length
        self.travel_time = travel_distance / wave_speed
        self.cycle_duration = self.travel_time + cycle_delay
        
        carb.log_info(
            f"[BreathingAnimator] Initialized: "
            f"segments={num_segments}, wave_speed={wave_speed}, "
            f"cycle_duration={self.cycle_duration:.2f}s"
        )

    def update(self, dt: float) -> list:
        """
        Update animation and return scale factors for each segment.
        
        Args:
            dt: Delta time since last update (seconds)
            
        Returns:
            List of scale factors, one per segment (1.0 = no scaling)
        """
        self.time += dt
        
        # Calculate cycle time
        cycle_time = self.time % self.cycle_duration
        
        # Check if we're in delay period
        if cycle_time >= self.travel_time:
            # In delay - no wave, all segments at base scale
            return [1.0] * self.num_segments
        
        # Calculate wave center position
        wave_center = calculate_wave_position(
            cycle_time,
            self.wave_speed,
            self.wave_start_y
        )
        
        # Calculate scale for each segment
        scales = []
        for seg_y in self.segment_y_positions:
            # Below wave start - no scaling
            if seg_y < self.wave_start_y:
                scales.append(1.0)
            else:
                scale = calculate_segment_scale(
                    seg_y,
                    wave_center,
                    self.wave_length,
                    self.amplitude
                )
                scales.append(scale)
        
        return scales

    def reset(self):
        """Reset animation to beginning of cycle."""
        self.time = 0.0
        self.in_delay = False

    def set_parameters(
        self,
        wave_speed: float = None,
        wave_length: float = None,
        amplitude: float = None,
        cycle_delay: float = None
    ):
        """
        Update animation parameters at runtime.
        
        Args:
            wave_speed: New wave speed (if provided)
            wave_length: New wavelength (if provided)
            amplitude: New amplitude (if provided)
            cycle_delay: New cycle delay (if provided)
        """
        if wave_speed is not None:
            self.wave_speed = wave_speed
        if wave_length is not None:
            self.wave_length = wave_length
        if amplitude is not None:
            self.amplitude = amplitude
        if cycle_delay is not None:
            self.cycle_delay = cycle_delay
        
        # Recalculate timing
        wave_gap = self.wave_length * 0.18 * 3.0
        self.wave_start_y = self.flare_height + wave_gap
        travel_distance = (self.length - self.wave_start_y) + self.wave_length
        self.travel_time = travel_distance / self.wave_speed
        self.cycle_duration = self.travel_time + self.cycle_delay

    def should_emit_bubble(self) -> bool:
        """
        Check if wave has reached top (time to emit bubble).
        
        Returns:
            True if bubble should be emitted this frame
        """
        cycle_time = self.time % self.cycle_duration
        
        # Emit when wave center reaches near the top
        if cycle_time < self.travel_time:
            wave_center = calculate_wave_position(
                cycle_time,
                self.wave_speed,
                self.wave_start_y
            )
            
            # Check if wave just passed the top
            prev_time = max(0.0, cycle_time - 0.016)
            prev_wave_center = calculate_wave_position(
                prev_time,
                self.wave_speed,
                self.wave_start_y
            )
            
            top_threshold = self.length * 0.95
            return prev_wave_center < top_threshold <= wave_center
        
        return False
