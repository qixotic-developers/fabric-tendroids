"""
Tests that the animation controller runs the interaction step in every animation path.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from qixotic.tendroids.bubbles.bubble_manager import V2BubbleManager
from qixotic.tendroids.scene.animation_controller import V2AnimationController


class FakeCreature:
    def __init__(self, x):
        self.x = x
        self.repulsions = []
        self.input_lock = None

    def get_contact_proxy(self):
        return [((self.x, 50.0, 0.0), 6.0)]

    def get_position(self):
        return (self.x, 50.0, 0.0)

    def apply_repulsion_force(self, force):
        self.repulsions.append(force)

    def set_input_lock(self, status):
        self.input_lock = status

    def update(self, *args, **kwargs):
        return [], []


def make_controller(path, creature_x):
    controller = V2AnimationController()
    tendroid = SimpleNamespace(
        name="t0", position=(0.0, 0.0, 0.0), radius=6.0, length=100.0,
        apply_wave_only_with_state=lambda wave_state: None,
    )
    controller.set_tendroids([tendroid])
    controller.creature_controller = FakeCreature(creature_x)
    if path == "gpu":
        controller.gpu_bubble_adapter = MagicMock()
        controller._update_gpu_path = lambda *args, **kwargs: None
    elif path == "cpu":
        # Specced on the real manager so a call to a method it lacks fails the test.
        controller.bubble_manager = MagicMock(spec=V2BubbleManager)
        controller.bubble_manager.get_bubble_positions.return_value = {}
        controller.bubble_manager.get_bubble_radii.return_value = {}
    return controller


@pytest.mark.parametrize("path", ["gpu", "cpu", "wave_only"])
class TestInteractionInEveryPath:
    def test_touching_the_tendroid_shocks_the_creature_once(self, path):
        controller = make_controller(path, creature_x=10.0)
        for _ in range(3):
            controller._on_update(None)
        creature = controller.creature_controller
        assert len(creature.repulsions) == 1
        assert creature.input_lock.is_locked

    def test_creature_clear_of_the_tendroid_is_left_alone(self, path):
        controller = make_controller(path, creature_x=60.0)
        controller._on_update(None)
        creature = controller.creature_controller
        assert creature.repulsions == []
        assert not creature.input_lock.is_locked


def test_replacing_tendroids_forgets_overlap_history():
    controller = make_controller("wave_only", creature_x=10.0)
    controller._on_update(None)
    controller.set_tendroids(controller.tendroids)  # a rebuilt scene reuses the names
    controller._on_update(None)
    assert len(controller.creature_controller.repulsions) == 2


def test_shock_colour_is_shown_on_the_creature_material():
    controller = make_controller("wave_only", creature_x=10.0)
    controller.color_effect_controller = MagicMock()
    controller._on_update(None)
    shown = controller.color_effect_controller.apply_status.call_args.args[0]
    assert shown is controller.interaction_system.orchestrator.state.color_status
