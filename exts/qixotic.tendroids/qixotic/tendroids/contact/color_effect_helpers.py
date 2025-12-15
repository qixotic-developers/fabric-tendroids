"""
Color Effect Helpers - Pure logic for shock color state management

Provides color state tracking, interpolation, and transition logic
without USD dependencies for testability.

Implements TEND-26: Implement shock color change effect.
Implements TEND-27: Implement color fade during recovery.
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Tuple


class ColorEffectState(Enum):
    """State of the color effect system."""
    NORMAL = auto()      # Default color, no contact
    SHOCKED = auto()     # Contact occurred, showing shock color
    RECOVERING = auto()  # Fading back to normal


@dataclass
class ColorConfig:
    """Configuration for color effects."""
    # Default creature color (cyan)
    normal_color: Tuple[float, float, float] = (0.2, 0.8, 0.9)
    
    # Shock color on contact (bright red/orange)
    shock_color: Tuple[float, float, float] = (1.0, 0.3, 0.1)
    
    # Distance threshold to start recovery
    approach_minimum: float = 15.0
    
    # Recovery fade duration in seconds
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
    """
    if config is None:
        config = ColorConfig()
    
    return ColorEffectStatus(
        state=ColorEffectState.SHOCKED,
        current_color=config.shock_color,
        shock_count=status.shock_count + 1,
        recovery_progress=0.0,
    )


def start_recovery(
    status: ColorEffectStatus,
    config: ColorConfig = None,
) -> ColorEffectStatus:
    """
    Transition from SHOCKED to RECOVERING state.
    
    Called when creature moves beyond approach_minimum.
    """
    if config is None:
        config = ColorConfig()
    
    return ColorEffectStatus(
        state=ColorEffectState.RECOVERING,
        current_color=status.current_color,  # Keep shock color initially
        shock_count=status.shock_count,
        recovery_progress=0.0,
    )


def update_recovery(
    status: ColorEffectStatus,
    fade_progress: float,
    config: ColorConfig = None,
) -> ColorEffectStatus:
    """
    Update recovery state with new fade progress.
    
    Args:
        status: Current status
        fade_progress: Progress 0.0 (shock) to 1.0 (normal)
        config: Color configuration
    
    Returns:
        Updated status with interpolated color
    """
    if config is None:
        config = ColorConfig()
    
    # Only process if recovering
    if status.state != ColorEffectState.RECOVERING:
        return status
    
    fade_progress = max(0.0, min(1.0, fade_progress))
    
    # Interpolate color
    new_color = interpolate_color(
        config.shock_color,
        config.normal_color,
        fade_progress,
    )
    
    # Check if recovery complete
    if fade_progress >= 1.0:
        return ColorEffectStatus(
            state=ColorEffectState.NORMAL,
            current_color=config.normal_color,
            shock_count=status.shock_count,
            recovery_progress=1.0,
        )
    
    return ColorEffectStatus(
        state=ColorEffectState.RECOVERING,
        current_color=new_color,
        shock_count=status.shock_count,
        recovery_progress=fade_progress,
    )


def check_shock_exit(
    status: ColorEffectStatus,
    distance_to_tendroid: float,
    config: ColorConfig = None,
) -> ColorEffectStatus:
    """
    Check if creature should exit shocked state based on distance.
    
    Transitions to RECOVERING (not NORMAL) for fade effect.
    """
    if config is None:
        config = ColorConfig()
    
    # Only process if currently shocked
    if status.state != ColorEffectState.SHOCKED:
        return status
    
    # Check if beyond approach_minimum - start recovery
    if distance_to_tendroid >= config.approach_minimum:
        return start_recovery(status, config)
    
    # Still within range, stay shocked
    return status


def reset_to_normal(
    status: ColorEffectStatus,
    config: ColorConfig = None,
) -> ColorEffectStatus:
    """Reset color to normal state immediately."""
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
    """Linear interpolation between two colors."""
    t = max(0.0, min(1.0, t))
    
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


def is_recovering(status: ColorEffectStatus) -> bool:
    """Check if currently in recovering state."""
    return status.state == ColorEffectState.RECOVERING
