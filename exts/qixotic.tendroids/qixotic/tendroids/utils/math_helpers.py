"""
Mathematical helper functions for Tendroid animation

These functions handle the sine wave calculations for breathing animation,
segment scaling, and flare interpolation.
"""

import math


def calculate_wave_position(time: float, wave_speed: float, base_height: float) -> float:
    """
    Calculate the current position of the traveling wave along the Tendroid's length.
    
    Args:
        time: Current simulation time in seconds
        wave_speed: Speed of wave travel in units/second
        base_height: Height of the flared base (wave starts above this)
        
    Returns:
        Current Y position of the wave center
    """
    return base_height + (wave_speed * time)


def calculate_segment_scale(
    segment_y: float,
    wave_center: float,
    wave_length: float,
    amplitude: float,
    base_scale: float = 1.0
) -> float:
    """
    Calculate the radial scale factor for a segment based on wave position.
    
    Uses a Gaussian envelope with positive-only sine wave to create smooth,
    organic breathing effect.
    
    Args:
        segment_y: Y position of the segment center
        wave_center: Current Y position of wave center
        wave_length: Wavelength (controls wave spread)
        amplitude: Maximum scale multiplier (e.g., 0.3 = 30% expansion)
        base_scale: Base scale to multiply by (default 1.0)
        
    Returns:
        Scale factor to apply to segment radius (1.0 = no change)
    """
    # Distance from wave center
    distance = segment_y - wave_center
    
    # Gaussian envelope (controls how focused the wave is)
    envelope_width = wave_length * 0.18  # Tuned for smooth appearance
    env_factor = distance / envelope_width
    envelope = math.exp(-(env_factor * env_factor))
    
    # Sine wave phase
    k = 2.0 * math.pi / wave_length
    phase = k * segment_y
    spatial = max(math.sin(phase), 0.0)  # Positive only
    
    # Combined displacement
    displacement = amplitude * spatial * envelope
    
    return base_scale * (1.0 + displacement)


def interpolate_flare_radius(
    y_position: float,
    base_radius: float,
    flare_height: float,
    flare_radius_multiplier: float
) -> float:
    """
    Calculate radius at a given height for flared base using ease-out quartic.
    
    This creates a mechanical flange profile: rapid radius change near ground,
    then curves vertically as it approaches the cylinder body.
    
    Args:
        y_position: Y position to calculate radius at
        base_radius: Normal cylinder radius
        flare_height: Height over which flare occurs
        flare_radius_multiplier: Maximum radius multiplier at base (e.g., 1.5 = 50% larger)
        
    Returns:
        Radius at the given height
    """
    if flare_height <= 0 or y_position >= flare_height:
        return base_radius
        
    max_flare_radius = base_radius * flare_radius_multiplier
    
    # Ease-out quartic for mechanical profile
    t = y_position / flare_height  # 0 at base, 1 at top of flare
    blend = 1.0 - pow(1.0 - t, 4)
    
    return max_flare_radius + (base_radius - max_flare_radius) * blend
