"""
Interaction System - Per-frame contact detection against the drawn tendroid surface

Tests each contact proxy sphere against every tendroid's visible (bent and
waved) surface. A contact fires only on the transition from not overlapping to
overlapping, once per tendroid, at the deepest-penetrating sphere. Pure
geometry plus the recovery orchestrator: no USD, Warp or Kit imports.
"""

import math
from dataclasses import dataclass, replace
from typing import Dict, List, Sequence, Set, Tuple

from ..animation.wave_offset import wave_offset
from ..recovery.recovery_orchestrator import RecoveryOrchestrator
from .repulsion_helpers import compute_repulsion_force
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
    """
    Detects contacts and drives the creature's shock and recovery response.

    The creature is passed in as an object with get_contact_proxy, get_position,
    apply_repulsion_force and set_input_lock, so the step needs no scene.
    """

    def __init__(self, orchestrator: RecoveryOrchestrator = None):
        self.orchestrator = orchestrator or RecoveryOrchestrator()
        self._overlapping: Set[str] = set()

    def forget_overlaps(self) -> None:
        """Drop overlap history, e.g. when the tendroids are replaced."""
        self._overlapping = set()

    def detect(self, spheres: Sequence[Sphere], shapes: Dict[str, TendroidShape]) -> List[Contact]:
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

    def resolve(self, creature, shapes: Dict[str, TendroidShape], dt: float) -> List[Contact]:
        """Run one frame: detect contacts, start a shock for each, advance recovery, derive input lock."""
        contacts = self.detect(creature.get_contact_proxy(), shapes)
        for contact in contacts:
            force = compute_repulsion_force(contact.normal, contact.penetration)
            self.orchestrator.handle_contact(contact.point, contact.normal, creature.get_position(), force)
            creature.apply_repulsion_force(force)

        # The orchestrator's displacement is not applied: repulsion moves the creature through
        # its velocity only, so the creature controller stays the sole writer of its position.
        self.orchestrator.update(creature.get_position(), dt)

        # A copy, so the creature can adjust its own lock without corrupting orchestrator state.
        creature.set_input_lock(replace(self.orchestrator.state.input_lock))
        return contacts
