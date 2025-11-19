"""
Idle motion animation for Tendroids

Adds subtle swaying and undulation when Tendroid is not interacting.
Uses simple sine waves for organic appearance.
"""

import math


class IdleMotionAnimator:
    """
    Manages idle swaying motion for a Tendroid.
    
    Creates gentle side-to-side and rotational motion to make
    the Tendroid appear alive even when not breathing or interacting.
    """

    def __init__(
        self,
        sway_frequency: float = 0.5,
        sway_amplitude: float = 5.0,
        rotation_frequency: float = 0.3,
        rotation_amplitude: float = 10.0
    ):
        """
        Initialize idle motion animator.
        
        Args:
            sway_frequency: Frequency of side-to-side sway (Hz)
            sway_amplitude: Amplitude of sway in world units
            rotation_frequency: Frequency of rotation oscillation (Hz)
            rotation_amplitude: Amplitude of rotation in degrees
        """
        self.sway_frequency = sway_frequency
        self.sway_amplitude = sway_amplitude
        self.rotation_frequency = rotation_frequency
        self.rotation_amplitude = rotation_amplitude
        
        self.time = 0.0
        self.enabled = True

    def update(self, dt: float) -> dict:
        """
        Update idle motion and return transformation parameters.
        
        Args:
            dt: Delta time since last update (seconds)
            
        Returns:
            Dictionary with keys:
                - 'offset': (x, y, z) translation offset
                - 'rotation': (rx, ry, rz) rotation in degrees
        """
        if not self.enabled:
            return {'offset': (0.0, 0.0, 0.0), 'rotation': (0.0, 0.0, 0.0)}
        
        self.time += dt
        
        # Calculate sway (primarily in X direction)
        sway_phase = 2 * math.pi * self.sway_frequency * self.time
        sway_x = self.sway_amplitude * math.sin(sway_phase)
        
        # Add slight Z sway at different frequency for more organic motion
        sway_z_phase = 2 * math.pi * self.sway_frequency * 0.7 * self.time
        sway_z = self.sway_amplitude * 0.3 * math.sin(sway_z_phase)
        
        # Calculate rotation (around Y axis - twist)
        rotation_phase = 2 * math.pi * self.rotation_frequency * self.time
        rotation_y = self.rotation_amplitude * math.sin(rotation_phase)
        
        return {
            'offset': (sway_x, 0.0, sway_z),
            'rotation': (0.0, rotation_y, 0.0)
        }

    def reset(self):
        """Reset animation to initial state."""
        self.time = 0.0

    def set_enabled(self, enabled: bool):
        """Enable or disable idle motion."""
        self.enabled = enabled
        if not enabled:
            self.time = 0.0

    def set_parameters(
        self,
        sway_frequency: float = None,
        sway_amplitude: float = None,
        rotation_frequency: float = None,
        rotation_amplitude: float = None
    ):
        """
        Update animation parameters at runtime.
        
        Args:
            sway_frequency: New sway frequency (if provided)
            sway_amplitude: New sway amplitude (if provided)
            rotation_frequency: New rotation frequency (if provided)
            rotation_amplitude: New rotation amplitude (if provided)
        """
        if sway_frequency is not None:
            self.sway_frequency = sway_frequency
        if sway_amplitude is not None:
            self.sway_amplitude = sway_amplitude
        if rotation_frequency is not None:
            self.rotation_frequency = rotation_frequency
        if rotation_amplitude is not None:
            self.rotation_amplitude = rotation_amplitude
