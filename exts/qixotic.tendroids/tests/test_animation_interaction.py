"""
Tests that the animation controller runs the interaction step in every animation path.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from qixotic.tendroids.scene import animation_controller as animation_module
from qixotic.tendroids.scene.animation_controller import V2AnimationController


class FakeCreature:
    def __init__(self, x):
        self.x = x

    def get_contact_proxy(self):
        return [((self.x, 50.0, 0.0), 6.0)]

    def get_position(self):
        return (self.x, 50.0, 0.0)

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
        controller.bubble_manager = MagicMock()
        controller.bubble_manager.get_bubble_positions.return_value = {}
        controller.bubble_manager.get_bubble_radii.return_value = {}
    return controller


@pytest.fixture
def carb_mock(monkeypatch):
    mock = MagicMock()
    monkeypatch.setattr(animation_module, "carb", mock)
    return mock


def contact_logs(carb_mock):
    return [c.args[0] for c in carb_mock.log_verbose.call_args_list if "Contact with" in c.args[0]]


@pytest.mark.parametrize("path", ["gpu", "cpu", "wave_only"])
class TestInteractionInEveryPath:
    def test_touching_the_tendroid_logs_one_contact_at_debug_level(self, carb_mock, path):
        controller = make_controller(path, creature_x=10.0)
        for _ in range(3):
            controller._on_update(None)
        logs = contact_logs(carb_mock)
        assert len(logs) == 1
        assert "t0" in logs[0]
        carb_mock.log_error.assert_not_called()

    def test_creature_clear_of_the_tendroid_logs_nothing(self, carb_mock, path):
        controller = make_controller(path, creature_x=60.0)
        controller._on_update(None)
        assert contact_logs(carb_mock) == []
        carb_mock.log_error.assert_not_called()
