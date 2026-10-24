"""
Tendroid Surface - Distance from a point to the tendroid as drawn

Pure geometry, no USD or Warp imports. Reproduces the centerline of the mesh
produced by the deformation kernel (bend about the latched axis, then wave
offset, both scaled by a smoothstep of height over length). Bubble bulging is
ignored by design (parent spec #21). It is exactly radial only for a straight
tendroid; on a bent one the kernel scales the bent position about the base axis,
so an active bubble shifts the true centerline sideways by up to
max_amplitude * lateral bend offset. The parity test runs with the bubble off.
"""

import math
from dataclasses import dataclass
from typing import Tuple

Vec3 = Tuple[float, float, float]

DEFAULT_SAMPLES = 16
_REFINE_ITERATIONS = 30


@dataclass(frozen=True)
class TendroidShape:
    """A tendroid's current pose, in the same terms the deformation kernel takes."""
    base: Vec3
    radius: float
    length: float
    deflection_angle: float = 0.0
    deflection_axis: Tuple[float, float] = (1.0, 0.0)  # (x, z), as passed to the kernel
    wave_offset: Tuple[float, float] = (0.0, 0.0)  # (dx, dz) at full height


@dataclass(frozen=True)
class SurfaceHit:
    """Result of a surface query; distance is negative when the point is inside."""
    distance: float
    contact_point: Vec3
    normal: Vec3


def _smoothstep(shape: TendroidShape, height: float) -> float:
    ratio = height / shape.length if shape.length > 0 else 0.0
    ratio = max(0.0, min(1.0, ratio))
    return ratio * ratio * (3.0 - 2.0 * ratio)


def centerline_point(shape: TendroidShape, height: float) -> Vec3:
    """World position of the centerline at an undeformed height above the base."""
    height = max(0.0, min(shape.length, height))
    blend = _smoothstep(shape, height)

    ax, az = shape.deflection_axis
    axis_len = math.hypot(ax, az)
    # Same fallback as the kernel launcher for a degenerate axis.
    ax, az = (ax / axis_len, az / axis_len) if axis_len > 0.0001 else (1.0, 0.0)

    angle = shape.deflection_angle * blend
    lateral = -height * math.sin(angle)

    bx, by, bz = shape.base
    return (
        bx + (-az) * lateral + shape.wave_offset[0] * blend,
        by + height * math.cos(angle),
        bz + ax * lateral + shape.wave_offset[1] * blend,
    )


def _distance_sq(a: Vec3, b: Vec3) -> float:
    return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2


def closest_point(shape: TendroidShape, position: Vec3, samples: int = DEFAULT_SAMPLES) -> Vec3:
    """Closest point on the centerline: coarse sampling, then refine the best segment."""
    step = shape.length / samples
    heights = [step * i for i in range(samples + 1)]
    best = min(range(samples + 1), key=lambda i: _distance_sq(centerline_point(shape, heights[i]), position))

    low = heights[max(best - 1, 0)]
    high = heights[min(best + 1, samples)]
    for _ in range(_REFINE_ITERATIONS):
        third = (high - low) / 3.0
        m1, m2 = low + third, high - third
        if _distance_sq(centerline_point(shape, m1), position) < _distance_sq(centerline_point(shape, m2), position):
            high = m2
        else:
            low = m1
    return centerline_point(shape, (low + high) / 2.0)


def surface_hit(shape: TendroidShape, position: Vec3, samples: int = DEFAULT_SAMPLES) -> SurfaceHit:
    """Distance, contact point and outward normal of the drawn tendroid surface."""
    closest = closest_point(shape, position, samples)
    offset = (position[0] - closest[0], position[1] - closest[1], position[2] - closest[2])
    centerline_distance = math.sqrt(offset[0] ** 2 + offset[1] ** 2 + offset[2] ** 2)

    if centerline_distance < 1e-8:
        normal = (1.0, 0.0, 0.0)  # On the centerline every direction is outward; match repulsion_helpers.
    else:
        normal = (offset[0] / centerline_distance, offset[1] / centerline_distance, offset[2] / centerline_distance)

    contact_point = (
        closest[0] + normal[0] * shape.radius,
        closest[1] + normal[1] * shape.radius,
        closest[2] + normal[2] * shape.radius,
    )
    return SurfaceHit(centerline_distance - shape.radius, contact_point, normal)
