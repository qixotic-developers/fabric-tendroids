"""
Debug Draw Helper Functions

Low-level drawing functions using omni.debugdraw for envelope visualization.
Draws wireframe circles/spheres at specified positions with zone colors.
"""

import math
from typing import Tuple

import carb


Color4 = Tuple[float, float, float, float]
Vec3 = Tuple[float, float, float]


def is_debugdraw_available() -> bool:
    """Check if debug draw interface is available."""
    try:
        import omni.debugdraw  # noqa: F401
        return True
    except ImportError:
        return False


def get_draw_interface():
    """Get the debug draw interface, or None if unavailable."""
    try:
        from omni.debugdraw import get_debug_draw_interface
        return get_debug_draw_interface()
    except ImportError:
        return None
    except Exception as e:
        carb.log_warn(f"[EnvelopeDebug] Failed to get debug draw: {e}")
        return None


def draw_circle_xz(
    draw_interface,
    center: Vec3,
    radius: float,
    color: Color4,
    segments: int = 24,
    thickness: float = 2.0
) -> None:
    """
    Draw a horizontal circle in the XZ plane.

    Args:
        draw_interface: omni.debugdraw interface
        center: Center point (x, y, z)
        radius: Circle radius
        color: RGBA color tuple
        segments: Number of line segments
        thickness: Line thickness (unused, kept for API compatibility)
    """
    if draw_interface is None or radius <= 0:
        return

    cx, cy, cz = center
    r, g, b, a = color
    color_int = _color_to_uint(r, g, b, a)

    angle_step = (2.0 * math.pi) / segments
    points = []

    for i in range(segments + 1):
        angle = i * angle_step
        x = cx + radius * math.cos(angle)
        z = cz + radius * math.sin(angle)
        points.append((x, cy, z))

    # Draw line segments
    for i in range(len(points) - 1):
        draw_interface.draw_line(
            carb.Float3(*points[i]),
            color_int,
            carb.Float3(*points[i + 1]),
            color_int
        )


def draw_circle_xy(
    draw_interface,
    center: Vec3,
    radius: float,
    color: Color4,
    segments: int = 24
) -> None:
    """Draw a vertical circle in the XY plane."""
    if draw_interface is None or radius <= 0:
        return

    cx, cy, cz = center
    color_int = _color_to_uint(*color)
    angle_step = (2.0 * math.pi) / segments
    points = []

    for i in range(segments + 1):
        angle = i * angle_step
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y, cz))

    for i in range(len(points) - 1):
        draw_interface.draw_line(
            carb.Float3(*points[i]),
            color_int,
            carb.Float3(*points[i + 1]),
            color_int
        )


def draw_sphere_wireframe(
    draw_interface,
    center: Vec3,
    radius: float,
    color: Color4,
    segments: int = 24
) -> None:
    """
    Draw a wireframe sphere using three orthogonal circles.

    Args:
        draw_interface: omni.debugdraw interface
        center: Center point
        radius: Sphere radius
        color: RGBA color
        segments: Segments per circle
    """
    # XZ plane (horizontal)
    draw_circle_xz(draw_interface, center, radius, color, segments)
    # XY plane (front)
    draw_circle_xy(draw_interface, center, radius, color, segments)
    # YZ plane (side)
    draw_circle_yz(draw_interface, center, radius, color, segments)


def draw_circle_yz(
    draw_interface,
    center: Vec3,
    radius: float,
    color: Color4,
    segments: int = 24
) -> None:
    """Draw a vertical circle in the YZ plane."""
    if draw_interface is None or radius <= 0:
        return

    cx, cy, cz = center
    color_int = _color_to_uint(*color)
    angle_step = (2.0 * math.pi) / segments
    points = []

    for i in range(segments + 1):
        angle = i * angle_step
        y = cy + radius * math.cos(angle)
        z = cz + radius * math.sin(angle)
        points.append((cx, y, z))

    for i in range(len(points) - 1):
        draw_interface.draw_line(
            carb.Float3(*points[i]),
            color_int,
            carb.Float3(*points[i + 1]),
            color_int
        )


def _color_to_uint(r: float, g: float, b: float, a: float) -> int:
    """Convert RGBA floats (0-1) to packed uint32 ABGR."""
    ri = int(max(0.0, min(255.0, r * 255.0)))
    gi = int(max(0.0, min(255.0, g * 255.0)))
    bi = int(max(0.0, min(255.0, b * 255.0)))
    ai = int(max(0.0, min(255.0, a * 255.0)))
    return (ai << 24) | (bi << 16) | (gi << 8) | ri
