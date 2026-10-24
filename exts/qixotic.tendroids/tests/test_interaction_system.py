"""
Tests for the interaction system's per-frame contact resolve step.

Driven by plain data: no USD, Kit or Warp.
"""

from types import SimpleNamespace

import pytest

from qixotic.tendroids.contact.color_effect_helpers import ColorConfig, ColorEffectState
from qixotic.tendroids.contact.interaction_system import InteractionSystem, shape_for
from qixotic.tendroids.contact.tendroid_surface import TendroidShape

RADIUS = 6.0
LENGTH = 100.0
CREATURE_RADIUS = 6.0


def straight(x=0.0, z=0.0):
    return TendroidShape(base=(x, 0.0, z), radius=RADIUS, length=LENGTH)


def bent_away(angle=-0.6):
    return TendroidShape(
        base=(0.0, 0.0, 0.0), radius=RADIUS, length=LENGTH,
        deflection_angle=angle, deflection_axis=(1.0, 0.0),
    )


def creature_at(x, y=50.0, z=0.0, radius=CREATURE_RADIUS):
    return [((x, y, z), radius)]


class TestContactFires:
    def test_touching_the_surface_fires_one_contact(self):
        system = InteractionSystem()
        contacts = system.detect(creature_at(10.0), {"t0": straight()})
        assert [c.tendroid_name for c in contacts] == ["t0"]
        assert contacts[0].normal == pytest.approx((1.0, 0.0, 0.0), abs=1e-4)
        assert contacts[0].point == pytest.approx((RADIUS, 50.0, 0.0), abs=1e-3)

    def test_clear_of_the_surface_fires_nothing(self):
        assert InteractionSystem().detect(creature_at(30.0), {"t0": straight()}) == []

    def test_bent_away_tendroid_causes_no_contact_where_the_rest_shape_was(self):
        # (0, 95, 0) is on the rest axis near the tip; the tendroid has moved off it.
        system = InteractionSystem()
        assert system.detect(creature_at(0.0, y=95.0), {"t0": bent_away()}) == []

    def test_bent_surface_is_touched_where_it_is_drawn(self):
        shape = bent_away()
        from qixotic.tendroids.contact.tendroid_surface import centerline_point
        tip = centerline_point(shape, LENGTH)
        contacts = InteractionSystem().detect([(tip, CREATURE_RADIUS)], {"t0": shape})
        assert len(contacts) == 1


class TestEdgeTriggering:
    def test_sustained_overlap_is_one_contact(self):
        system = InteractionSystem()
        shapes = {"t0": straight()}
        fired = [len(system.detect(creature_at(10.0), shapes)) for _ in range(5)]
        assert fired == [1, 0, 0, 0, 0]

    def test_leaving_and_reentering_is_a_second_contact(self):
        system = InteractionSystem()
        shapes = {"t0": straight()}
        fired = [
            len(system.detect(creature_at(x), shapes))
            for x in (10.0, 10.0, 40.0, 10.0)
        ]
        assert fired == [1, 0, 0, 1]

    def test_each_tendroid_is_tracked_separately(self):
        system = InteractionSystem()
        shapes = {"a": straight(0.0), "b": straight(30.0)}
        assert len(system.detect(creature_at(10.0), shapes)) == 1
        # Moving out of a's reach and into b's fires only b.
        contacts = system.detect(creature_at(22.0), shapes)
        assert [c.tendroid_name for c in contacts] == ["b"]


class TestMultipleSpheres:
    def test_several_spheres_yield_one_contact_at_the_deepest_penetration(self):
        proxy = [((11.0, 50.0, 0.0), 6.0), ((8.0, 70.0, 0.0), 6.0)]
        contacts = InteractionSystem().detect(proxy, {"t0": straight()})
        assert len(contacts) == 1
        assert contacts[0].point[1] == pytest.approx(70.0, abs=1e-3)

    def test_one_sphere_touching_is_enough(self):
        proxy = [((40.0, 50.0, 0.0), 6.0), ((10.0, 20.0, 0.0), 6.0)]
        assert len(InteractionSystem().detect(proxy, {"t0": straight()})) == 1


class TestShapeFor:
    TENDROID = SimpleNamespace(name="t0", position=(100.0, 0.0, 50.0), radius=RADIUS, length=LENGTH)
    WAVE = {'enabled': True, 'displacement': 0.5, 'amplitude': 10.0, 'dir_x': 1.0, 'dir_z': 0.0}

    def deflection(self, angle, is_deflecting=True):
        return SimpleNamespace(current_angle=angle, is_deflecting=is_deflecting, deflection_axis=(0.0, 0.0, 1.0))

    def test_deflection_is_negated_and_uses_xz_axis_like_the_deformation_paths(self):
        shape = shape_for(self.TENDROID, self.deflection(0.4), self.WAVE)
        assert shape.deflection_angle == pytest.approx(-0.4)
        assert shape.deflection_axis == (0.0, 1.0)

    @pytest.mark.parametrize("state", [None, "tiny", "idle"])
    def test_no_effective_deflection_gives_a_straight_shape(self, state):
        states = {
            None: None,
            "tiny": self.deflection(0.0005),
            "idle": self.deflection(0.4, is_deflecting=False),
        }
        assert shape_for(self.TENDROID, states[state], self.WAVE).deflection_angle == 0.0

    def test_wave_offset_comes_from_the_shared_helper(self):
        from qixotic.tendroids.animation.wave_offset import wave_offset
        shape = shape_for(self.TENDROID, None, self.WAVE)
        assert shape.wave_offset == wave_offset(self.TENDROID.position, self.WAVE)
        assert shape.base == self.TENDROID.position


# =============================================================================
# RESPONSE (real recovery orchestrator, fake creature)
# =============================================================================

DT = 1.0 / 60.0


class FakeCreature:
    """Plain-data stand-in for the creature controller."""

    def __init__(self, position):
        self.position = tuple(position)
        self.velocity = (0.0, 0.0, 0.0)
        self.input_lock = None
        self.repulsions = []

    def get_contact_proxy(self):
        return [(self.position, CREATURE_RADIUS)]

    def get_position(self):
        return self.position

    def apply_repulsion_force(self, force):
        self.repulsions.append(force)
        self.velocity = tuple(v + f for v, f in zip(self.velocity, force))

    def set_input_lock(self, status):
        self.input_lock = status

    def move(self, dt):
        """Integrate velocity the way the creature controller does."""
        self.position = tuple(p + v * dt for p, v in zip(self.position, self.velocity))
        self.velocity = tuple(v * 0.98 for v in self.velocity)


def run_frame(system, creature, shapes):
    contacts = system.resolve(creature, shapes, DT)
    creature.move(DT)
    return contacts


class TestShockResponse:
    def test_contact_pushes_the_creature_along_the_surface_normal_by_velocity_only(self):
        system = InteractionSystem()
        creature = FakeCreature((10.0, 50.0, 0.0))
        system.resolve(creature, {"t0": straight()}, DT)
        assert len(creature.repulsions) == 1
        fx, fy, fz = creature.repulsions[0]
        assert fx > 0.0 and fy == pytest.approx(0.0, abs=1e-3) and fz == pytest.approx(0.0, abs=1e-3)
        assert creature.position == (10.0, 50.0, 0.0)  # resolve never writes position

    def test_contact_shocks_the_colour_and_locks_input(self):
        system = InteractionSystem()
        creature = FakeCreature((10.0, 50.0, 0.0))
        system.resolve(creature, {"t0": straight()}, DT)
        # At scene scale the approach threshold is crossed within the same frame, so the
        # state may already be RECOVERING; the colour is still the shock colour.
        assert system.orchestrator.state.color_status.state != ColorEffectState.NORMAL
        assert system.orchestrator.current_color == ColorConfig().shock_color
        assert creature.input_lock.is_locked

    def test_no_contact_leaves_the_creature_unlocked_and_unpushed(self):
        system = InteractionSystem()
        creature = FakeCreature((60.0, 50.0, 0.0))
        system.resolve(creature, {"t0": straight()}, DT)
        assert creature.repulsions == []
        assert not creature.input_lock.is_locked

    def test_sustained_overlap_does_not_restart_the_shock(self):
        system = InteractionSystem()
        creature = FakeCreature((10.0, 50.0, 0.0))
        for _ in range(3):
            system.resolve(creature, {"t0": straight()}, DT)  # not moved, so still overlapping
        assert system.orchestrator.total_contacts == 1
        assert len(creature.repulsions) == 1

    def test_touching_a_second_tendroid_during_recovery_restarts_the_shock(self):
        system = InteractionSystem()
        shapes = {"a": straight(0.0), "b": straight(30.0)}
        creature = FakeCreature((10.0, 50.0, 0.0))
        system.resolve(creature, shapes, DT)
        creature.position = (22.0, 50.0, 0.0)  # clear of a, touching b
        system.resolve(creature, shapes, DT)
        assert system.orchestrator.total_contacts == 2
        assert creature.input_lock.is_locked


class TestRecovery:
    def test_control_returns_once_the_creature_has_moved_clear(self):
        system = InteractionSystem()
        shapes = {"t0": straight()}
        creature = FakeCreature((10.0, 50.0, 0.0))
        for _ in range(600):
            run_frame(system, creature, shapes)
            if system.orchestrator.total_recoveries:
                break
        assert system.orchestrator.total_recoveries == 1
        assert not creature.input_lock.is_locked
        assert system.orchestrator.state.color_status.state == ColorEffectState.NORMAL

    def test_input_lock_status_given_to_the_creature_is_a_copy(self):
        system = InteractionSystem()
        creature = FakeCreature((10.0, 50.0, 0.0))
        system.resolve(creature, {"t0": straight()}, DT)
        creature.input_lock.is_locked = False
        assert system.orchestrator.is_input_locked
