"""
Mathematical helper functions for Tendroid animations

Provides wave calculations and utility functions used across animation systems.
"""

import math


def smooth_step(edge0: float, edge1: float, x: float) -> float:
    """
    Smooth interpolation function (smoothstep).
    
    Args:
        edge0: Lower edge of transition
        edge1: Upper edge of transition
        x: Value to interpolate
        
    Returns:
        Smoothly interpolated value between 0 and 1
    """
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def ease_out_quartic(t: float) -> float:
    """
    Ease-out quartic easing function.
    
    Args:
        t: Input value (0 to 1)
        
    Returns:
        Eased value (0 to 1)
    """
    return 1.0 - pow(1.0 - t, 4.0)


def calculate_flare_radius(
    y: float,
    base_radius: float,
    max_radius: float,
    flare_height: float
) -> float:
    """
    Calculate radius at a given height for flared base.
    
    Uses ease-out quartic for smooth mechanical flange profile.
    
    Args:
        y: Height position
        base_radius: Normal cylinder radius
        max_radius: Maximum radius at base (y=0)
        flare_height: Height where flare transitions to cylinder
        
    Returns:
        Radius at the given height
    """
    if y >= flare_height:
        return base_radius
    
    t = y / flare_height if flare_height > 0 else 1.0
    blend = ease_out_quartic(t)
    return max_radius + (base_radius - max_radius) * blend


def calculate_wave_displacement(
    y: float,
    wave_center: float,
    wave_length: float,
    amplitude: float,
    deform_start_y: float
) -> float:
    """
    Calculate radial displacement for breathing wave at a given height.
    
    Args:
        y: Vertex height position
        wave_center: Current center position of the wave
        wave_length: Length of the wave (controls falloff)
        amplitude: Maximum displacement factor
        deform_start_y: Height where deformation begins
        
    Returns:
        Radial displacement multiplier (1.0 = no change)
    """
    # Below deformation zone - no displacement
    if y < deform_start_y:
        return 1.0
    
    # Distance from wave center
    distance = abs(y - wave_center)
    
    # Gaussian-like falloff
    falloff = wave_length / 2.0
    if distance > falloff * 2.0:
        return 1.0
    
    # Sine wave with smooth falloff
    phase = (distance / falloff) * math.pi
    wave_value = math.cos(phase)
    
    # Only positive lobe (expansion)
    if wave_value < 0:
        return 1.0
    
    return 1.0 + (wave_value * amplitude)


def calculate_wave_position(
    time: float,
    speed: float,
    start_y: float
) -> float:
    """
    Calculate wave center position at a given time.
    
    Args:
        time: Current animation time
        speed: Wave travel speed (units/second)
        start_y: Starting Y position of wave
        
    Returns:
        Current Y position of wave center
    """
    return start_y + (time * speed)
