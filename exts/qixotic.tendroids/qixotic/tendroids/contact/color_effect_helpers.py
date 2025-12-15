"""
Color Effect Helpers - Pure logic for shock color state management

Provides color state tracking, interpolation, and transition logic
without USD dependencies for testability.

Implements TEND-26: Implement shock color change effect.
Implements TEND-101: Implement instant color change on contact.
Implements TEND-102: Implement color persistence until approach_minimum.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple


class ColorEffectState(Enum):
    """State of the color effect system."""
    NORMAL = auto()      # Default color, no contact
    SHOCKED = auto()     # Contact occurred, showing shock color
    RECOVERING = auto()  # Fading back to normal (used in TEND-27)


@dataclass
class ColorConfig:
    """Configuration for color effects."""
    # Default creature color (cyan)
    normal_color: Tuple[float, float, float] = (0.2, 0.8, 0.9)
    
    # Shock color on contact (bright red/orange)
    shock_color: Tuple[float, float, float] = (1.0, 0.3, 0.1)
    
    # Distance threshold to exit shocked state
    approach_minimum: float = 15.0
    
    # Recovery fade duration in seconds (for TEND-27)
    recovery_duration: float = 0.5


@dataclass
class ColorEffectStatus:
    """Current status of color effect system."""
    state: ColorEffectState = ColorEffectState.NORMAL
    current_color: Tuple[float, float, float] = (0.2, 0.8, 0.9)
    shock_count: int = 0  # Total shocks received
    recovery_progress: float = 0.0  # 0.0 to 1.0 for fade


def trigger_shock(
    status: ColorEffectStatus,
    config: ColorConfig = None,
) -> ColorEffectStatus:
    """
    Trigger shock color effect on contact.
    
    Instantly changes to shock color regardless of current state.
    
    Args:
        status: Current color effect status
        config: Color configuration
    
    Returns:
        Updated status with shock color applied
    """
    if config is None:
        config = ColorConfig()
    
    return ColorEffectStatus(
        state=ColorEffectState.SHOCKED,
        current_color=config.shock_color,
        shock_count=status.shock_count + 1,
        recovery_progress=0.0,
    )


def check_shock_exit(
    status: ColorEffectStatus,
    distance_to_tendroid: float,
    config: ColorConfig = None,
) -> ColorEffectStatus:
    """
    Check if creature should exit shocked state based on distance.
    
    Color persists until creature moves beyond approach_minimum.
    
    Args:
        status: Current color effect status
        distance_to_tendroid: Current horizontal distance to nearest tendroid
        config: Color configuration
    
    Returns:
        Updated status (may transition to NORMAL or RECOVERING)
    """
    if config is None:
        config = ColorConfig()
    
    # Only process if currently shocked
    if status.state != ColorEffectState.SHOCKED:
        return status
    
    # Check if beyond approach_minimum
    if distance_to_tendroid >= config.approach_minimum:
        # For now, return to normal immediately
        # TEND-27 will add RECOVERING state with fade
        return ColorEffectStatus(
            state=ColorEffectState.NORMAL,
            current_color=config.normal_color,
            shock_count=status.shock_count,
            recovery_progress=1.0,
        )
    
    # Still within range, stay shocked
    return status


def reset_to_normal(
    status: ColorEffectStatus,
    config: ColorConfig = None,
) -> ColorEffectStatus:
    """
    Reset color to normal state immediately.
    
    Args:
        status: Current color effect status
        config: Color configuration
    
    Returns:
        Status reset to normal
    """
    if config is None:
        config = ColorConfig()
    
    return ColorEffectStatus(
        state=ColorEffectState.NORMAL,
        current_color=config.normal_color,
        shock_count=status.shock_count,
        recovery_progress=1.0,
    )


def interpolate_color(
    color_a: Tuple[float, float, float],
    color_b: Tuple[float, float, float],
    t: float,
) -> Tuple[float, float, float]:
    """
    Linear interpolation between two colors.
    
    Args:
        color_a: Starting color (RGB, 0-1)
        color_b: Ending color (RGB, 0-1)
        t: Interpolation factor (0.0 = color_a, 1.0 = color_b)
    
    Returns:
        Interpolated RGB color
    """
    t = max(0.0, min(1.0, t))  # Clamp
    
    r = color_a[0] + (color_b[0] - color_a[0]) * t
    g = color_a[1] + (color_b[1] - color_a[1]) * t
    b = color_a[2] + (color_b[2] - color_a[2]) * t
    
    return (r, g, b)


def is_shocked(status: ColorEffectStatus) -> bool:
    """Check if currently in shocked state."""
    return status.state == ColorEffectState.SHOCKED


def is_normal(status: ColorEffectStatus) -> bool:
    """Check if currently in normal state."""
    return status.state == ColorEffectState.NORMAL
