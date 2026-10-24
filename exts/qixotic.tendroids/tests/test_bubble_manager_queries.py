"""
Tests for the CPU bubble manager's creature-facing queries.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from qixotic.tendroids.bubbles.bubble_manager import V2BubbleManager


def make_state(phase, world_pos=(1.0, 2.0, 3.0), radius=4.0):
    return SimpleNamespace(phase=phase, world_pos=list(world_pos), current_radius=radius, _pop=MagicMock())


@pytest.fixture
def manager():
    # Built without a stage: the queries only read bubble state.
    manager = V2BubbleManager.__new__(V2BubbleManager)
    manager._bubbles = {
        "idle": make_state("idle"),
        "rising": make_state("rising"),
        "exiting": make_state("exiting"),
        "released": make_state("released"),
        "popped": make_state("popped"),
    }
    return manager


def test_positions_and_radii_cover_only_bubbles_the_creature_can_hit(manager):
    assert set(manager.get_bubble_positions()) == {"rising", "exiting", "released"}
    assert set(manager.get_bubble_radii()) == {"rising", "exiting", "released"}


def test_position_is_a_tuple_and_radius_is_the_current_radius(manager):
    assert manager.get_bubble_positions()["rising"] == (1.0, 2.0, 3.0)
    assert manager.get_bubble_radii()["rising"] == 4.0


def test_pop_bubble_pops_a_hittable_bubble(manager):
    manager.pop_bubble("rising")
    manager._bubbles["rising"]._pop.assert_called_once()


@pytest.mark.parametrize("name", ["idle", "popped", "missing"])
def test_pop_bubble_ignores_bubbles_that_cannot_be_hit(manager, name):
    manager.pop_bubble(name)
    assert not any(s._pop.called for s in manager._bubbles.values())
