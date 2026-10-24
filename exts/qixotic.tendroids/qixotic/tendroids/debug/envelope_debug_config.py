"""
Envelope Debug Visualization Configuration

Color schemes and settings for visualizing creature envelope zones
using omni.debugdraw.

Zones (inside-out):
- Contact zone: Where collision triggers (approach_epsilon)
- Recovery zone: Safe clearance area (approach_minimum)
- Warning zone: Creature starts slowing (warning_distance)
- Detection zone: Outer boundary (detection_radius)
"""

from dataclasses import dataclass, field
from typing import Tuple

# Type alias for RGBA color
Color4 = Tuple[float, float, float, float]


@dataclass
class ZoneColors:
    """Color scheme for envelope zones."""

    # Contact zone - red (danger)
    contact: Color4 = (1.0, 0.2, 0.2, 0.6)

    # Recovery zone - orange (caution)
    recovery: Color4 = (1.0, 0.6, 0.2, 0.5)

    # Warning zone - yellow (attention)
    warning: Color4 = (1.0, 1.0, 0.2, 0.4)

    # Detection zone - green (safe/aware)
    detection: Color4 = (0.2, 1.0, 0.2, 0.3)

    # Envelope boundary - cyan wireframe
    envelope: Color4 = (0.2, 0.8, 1.0, 0.8)


@dataclass
class DebugDrawSettings:
    """Settings for debug visualization."""

    # Master toggle
    enabled: bool = True

    # Individual zone toggles
    show_contact_zone: bool = True
    show_recovery_zone: bool = True
    show_warning_zone: bool = True
    show_detection_zone: bool = True
    show_envelope: bool = True

    # Draw style
    wireframe: bool = True
    segment_count: int = 24  # Circle segments for sphere approximation
    line_thickness: float = 2.0

    # Z-offset to prevent z-fighting with ground
    height_offset: float = 0.01


@dataclass
class EnvelopeDebugConfig:
    """Complete configuration for envelope debug visualization."""

    colors: ZoneColors = field(default_factory=ZoneColors)
    settings: DebugDrawSettings = field(default_factory=DebugDrawSettings)


# Default configuration instance
DEFAULT_DEBUG_CONFIG = EnvelopeDebugConfig()


def get_zone_color(zone_name: str, config: EnvelopeDebugConfig = None) -> Color4:
    """
    Get color for a named zone.

    Args:
        zone_name: One of "contact", "recovery", "warning", "detection", "envelope"
        config: Optional config, uses default if None

    Returns:
        RGBA color tuple
    """
    if config is None:
        config = DEFAULT_DEBUG_CONFIG

    color_map = {
        "contact": config.colors.contact,
        "recovery": config.colors.recovery,
        "warning": config.colors.warning,
        "detection": config.colors.detection,
        "envelope": config.colors.envelope,
    }
    return color_map.get(zone_name, (1.0, 1.0, 1.0, 1.0))
