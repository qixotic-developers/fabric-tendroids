"""
Debug Visualization Module

Provides visual debugging tools for creature-tendroid interactions.
Uses omni.debugdraw for lightweight, toggleable visualization.

Usage:
    from qixotic.tendroids.debug import EnvelopeVisualizer

    # Create visualizer
    visualizer = EnvelopeVisualizer()

    # In update loop
    visualizer.update(creature.get_position())

    # Toggle on/off
    visualizer.toggle()
"""

from .envelope_debug_config import (
    EnvelopeDebugConfig,
    ZoneColors,
    DebugDrawSettings,
    DEFAULT_DEBUG_CONFIG,
    get_zone_color,
)

from .envelope_debug_draw import (
    is_debugdraw_available,
    draw_circle_xz,
    draw_sphere_wireframe,
)

from .envelope_visualizer import EnvelopeVisualizer

__all__ = [
    # Main visualizer
    "EnvelopeVisualizer",
    # Configuration
    "EnvelopeDebugConfig",
    "ZoneColors",
    "DebugDrawSettings",
    "DEFAULT_DEBUG_CONFIG",
    # Utilities
    "is_debugdraw_available",
    "get_zone_color",
    "draw_circle_xz",
    "draw_sphere_wireframe",
]
