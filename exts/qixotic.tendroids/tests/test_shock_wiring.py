"""
Tests for the pieces that wire the recovery orchestrator into the scene:
the orchestrator completing a recovery, the creature taking its input lock, and
the colour controller showing the orchestrator's colour.
"""

from unittest.mock import MagicMock

from qixotic.tendroids.contact.color_effect_controller import ColorEffectController
from qixotic.tendroids.contact.color_effect_helpers import ColorEffectStatus
from qixotic.tendroids.contact.input_lock_helpers import InputLockReason, InputLockStatus
from qixotic.tendroids.controllers.creature_controller import CreatureController
from qixotic.tendroids.recovery.recovery_orchestrator import RecoveryOrchestrator


def test_recovery_completes_after_the_threshold_is_crossed():
    orchestrator = RecoveryOrchestrator()
    orchestrator.handle_contact(
        contact_point=(6.0, 0.0, 0.0), surface_normal=(1.0, 0.0, 0.0),
        creature_pos=(10.0, 0.0, 0.0), repulsion_force=(100.0, 0.0, 0.0),
    )
    for _ in range(300):
        orchestrator.update((50.0, 0.0, 0.0), 1.0 / 60.0)
    assert orchestrator.total_recoveries == 1
    assert not orchestrator.is_input_locked


def make_creature(lock_status):
    creature = CreatureController.__new__(CreatureController)
    creature._input_lock_status = lock_status
    return creature


class TestCreatureInputLock:
    def test_takes_the_lock_from_the_orchestrator(self):
        creature = make_creature(InputLockStatus())
        creature.set_input_lock(InputLockStatus(is_locked=True, reason=InputLockReason.CONTACT))
        assert creature.is_input_locked

    def test_releases_the_lock_when_the_orchestrator_does(self):
        creature = make_creature(InputLockStatus(is_locked=True, reason=InputLockReason.RECOVERING))
        creature.set_input_lock(InputLockStatus())
        assert not creature.is_input_locked

    def test_a_running_test_lock_is_not_overwritten(self):
        creature = make_creature(InputLockStatus(is_locked=True, reason=InputLockReason.TEST))
        creature.set_input_lock(InputLockStatus())
        assert creature.is_input_locked
        assert creature.input_lock_reason == InputLockReason.TEST


class TestColorEffectControllerApplyStatus:
    def test_shows_a_new_colour_on_the_material(self):
        controller = ColorEffectController()
        controller._apply_color_to_material = MagicMock()
        controller.apply_status(ColorEffectStatus(current_color=(1.0, 0.3, 0.1)))
        controller._apply_color_to_material.assert_called_once()
        assert controller.status.current_color == (1.0, 0.3, 0.1)

    def test_does_not_rewrite_the_material_when_the_colour_is_unchanged(self):
        controller = ColorEffectController()
        controller._apply_color_to_material = MagicMock()
        controller.apply_status(ColorEffectStatus())
        controller._apply_color_to_material.assert_not_called()
