"""
Interaction System - Per-frame contact detection against the drawn tendroid surface

Tests each contact proxy sphere against every tendroid's visible (bent and
waved) surface. A contact fires only on the transition from not overlapping to
overlapping, once per tendroid, at the deepest-penetrating sphere. Pure
geometry: no USD, Warp or Kit imports.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Sequence, Set, Tuple

from ..animation.wave_offset import wave_offset
from .tendroid_surface import TendroidShape, surface_hit

Vec3 = Tuple[float, float, float]
Sphere = Tuple[Vec3, float]  # (center, radius)

# Matches the threshold the deformation paths use before they bend a mesh.
_MIN_DEFLECTION_ANGLE = 0.001


@dataclass(frozen=True)
class Contact:
    """A contact between the creature's contact proxy and a tendroid's drawn surface."""
    tendroid_name: str
    point: Vec3
    normal: Vec3
    penetration: float


def shape_for(tendroid, deflection_state, wave_state: dict) -> TendroidShape:
    """The pose the deformation paths draw this frame, for a tendroid wrapper."""
    angle, axis = 0.0, (1.0, 0.0)
    if (deflection_state and deflection_state.is_deflecting
            and abs(deflection_state.current_angle) > _MIN_DEFLECTION_ANGLE):
        # The deformation paths negate the angle to bend away from the creature.
        angle = -deflection_state.current_angle
        axis = (deflection_state.deflection_axis[0], deflection_state.deflection_axis[2])

    return TendroidShape(
        base=tuple(tendroid.position),
        radius=tendroid.radius,
        length=tendroid.length,
        deflection_angle=angle,
        deflection_axis=axis,
        wave_offset=wave_offset(tendroid.position, wave_state),
    )


def _deepest_contact(name: str, shape: TendroidShape, spheres: Sequence[Sphere]):
    deepest = None
    for center, radius in spheres:
        # The centerline never leaves this ball, so farther spheres cannot overlap.
        reach = shape.length + math.hypot(*shape.wave_offset) + shape.radius + radius
        if math.dist(center, shape.base) > reach:
            continue
        hit = surface_hit(shape, center)
        penetration = radius - hit.distance
        if penetration > 0.0 and (deepest is None or penetration > deepest.penetration):
            deepest = Contact(name, hit.contact_point, hit.normal, penetration)
    return deepest


class InteractionSystem:
    """Resolves contacts between the creature's contact proxy and the tendroids."""

    def __init__(self):
        self._overlapping: Set[str] = set()

    def resolve(self, spheres: Sequence[Sphere], shapes: Dict[str, TendroidShape]) -> List[Contact]:
        """Return the contacts that began this frame."""
        began = []
        overlapping_now = set()
        for name, shape in shapes.items():
            contact = _deepest_contact(name, shape, spheres)
            if contact is None:
                continue
            overlapping_now.add(name)
            if name not in self._overlapping:
                began.append(contact)
        self._overlapping = overlapping_now
        return began
