"""
Tests for Color Effect System

Unit tests for shock color change and state management.
Implements TEND-103: Add unit tests for color effects.
"""

from qixotic.tendroids.contact.color_effect_helpers import (
    ColorConfig,
    ColorEffectState,
    ColorEffectStatus,
    trigger_shock,
    check_shock_exit,
    reset_to_normal,
    interpolate_color,
    is_shocked,
    is_normal,
)
from qixotic.tendroids.contact.color_effect_controller import ColorEffectController


# =============================================================================
# COLOR CONFIG TESTS
# =============================================================================

class TestColorConfig:
    """Tests for ColorConfig defaults."""

    def test_default_normal_color(self):
        """Default normal color is cyan."""
        config = ColorConfig()
        assert config.normal_color == (0.2, 0.8, 0.9)

    def test_default_shock_color(self):
        """Default shock color is red/orange."""
        config = ColorConfig()
        assert config.shock_color == (1.0, 0.3, 0.1)

    def test_default_approach_minimum(self):
        """Default approach minimum is 15."""
        config = ColorConfig()
        assert config.approach_minimum == 15.0

    def test_custom_config(self):
        """Custom config values work."""
        config = ColorConfig(
            normal_color=(0.0, 1.0, 0.0),
            shock_color=(1.0, 0.0, 0.0),
            approach_minimum=20.0,
        )
        assert config.normal_color == (0.0, 1.0, 0.0)
        assert config.shock_color == (1.0, 0.0, 0.0)
        assert config.approach_minimum == 20.0


# =============================================================================
# TRIGGER SHOCK TESTS
# =============================================================================

class TestTriggerShock:
    """Tests for trigger_shock function."""

    def test_changes_state_to_shocked(self):
        """Trigger changes state to SHOCKED."""
        status = ColorEffectStatus()
        result = trigger_shock(status)
        assert result.state == ColorEffectState.SHOCKED

    def test_applies_shock_color(self):
        """Trigger applies shock color."""
        config = ColorConfig(shock_color=(1.0, 0.0, 0.0))
        status = ColorEffectStatus()
        result = trigger_shock(status, config)
        assert result.current_color == (1.0, 0.0, 0.0)

    def test_increments_shock_count(self):
        """Trigger increments shock counter."""
        status = ColorEffectStatus(shock_count=5)
        result = trigger_shock(status)
        assert result.shock_count == 6

    def test_resets_recovery_progress(self):
        """Trigger resets recovery progress."""
        status = ColorEffectStatus(recovery_progress=0.5)
        result = trigger_shock(status)
        assert result.recovery_progress == 0.0

    def test_can_trigger_while_already_shocked(self):
        """Can trigger again while already shocked."""
        status = ColorEffectStatus(
            state=ColorEffectState.SHOCKED,
            shock_count=3,
        )
        result = trigger_shock(status)
        assert result.state == ColorEffectState.SHOCKED
        assert result.shock_count == 4


# =============================================================================
# CHECK SHOCK EXIT TESTS
# =============================================================================

class TestCheckShockExit:
    """Tests for check_shock_exit function."""

    def test_stays_shocked_when_within_range(self):
        """Stays shocked when distance < approach_minimum."""
        config = ColorConfig(approach_minimum=15.0)
        status = ColorEffectStatus(state=ColorEffectState.SHOCKED)
        
        result = check_shock_exit(status, distance_to_tendroid=10.0, config=config)
        
        assert result.state == ColorEffectState.SHOCKED

    def test_exits_shocked_when_beyond_range(self):
        """Exits shocked when distance >= approach_minimum."""
        config = ColorConfig(approach_minimum=15.0)
        status = ColorEffectStatus(state=ColorEffectState.SHOCKED)
        
        result = check_shock_exit(status, distance_to_tendroid=15.0, config=config)
        
        assert result.state == ColorEffectState.NORMAL

    def test_restores_normal_color_on_exit(self):
        """Restores normal color when exiting shocked state."""
        config = ColorConfig(
            normal_color=(0.0, 1.0, 0.0),
            approach_minimum=15.0,
        )
        status = ColorEffectStatus(
            state=ColorEffectState.SHOCKED,
            current_color=(1.0, 0.0, 0.0),
        )
        
        result = check_shock_exit(status, distance_to_tendroid=20.0, config=config)
        
        assert result.current_color == (0.0, 1.0, 0.0)

    def test_preserves_shock_count_on_exit(self):
        """Preserves shock count when exiting."""
        status = ColorEffectStatus(
            state=ColorEffectState.SHOCKED,
            shock_count=10,
        )
        
        result = check_shock_exit(status, distance_to_tendroid=100.0)
        
        assert result.shock_count == 10

    def test_no_change_when_already_normal(self):
        """No change when already in normal state."""
        status = ColorEffectStatus(state=ColorEffectState.NORMAL)
        
        result = check_shock_exit(status, distance_to_tendroid=5.0)
        
        assert result.state == ColorEffectState.NORMAL

    def test_exact_boundary_exits_shocked(self):
        """Exactly at approach_minimum exits shocked."""
        config = ColorConfig(approach_minimum=15.0)
        status = ColorEffectStatus(state=ColorEffectState.SHOCKED)
        
        result = check_shock_exit(status, distance_to_tendroid=15.0, config=config)
        
        assert result.state == ColorEffectState.NORMAL


# =============================================================================
# RESET TO NORMAL TESTS
# =============================================================================

class TestResetToNormal:
    """Tests for reset_to_normal function."""

    def test_changes_state_to_normal(self):
        """Reset changes state to NORMAL."""
        status = ColorEffectStatus(state=ColorEffectState.SHOCKED)
        result = reset_to_normal(status)
        assert result.state == ColorEffectState.NORMAL

    def test_applies_normal_color(self):
        """Reset applies normal color."""
        config = ColorConfig(normal_color=(0.5, 0.5, 0.5))
        status = ColorEffectStatus(current_color=(1.0, 0.0, 0.0))
        result = reset_to_normal(status, config)
        assert result.current_color == (0.5, 0.5, 0.5)

    def test_preserves_shock_count(self):
        """Reset preserves shock count."""
        status = ColorEffectStatus(shock_count=7)
        result = reset_to_normal(status)
        assert result.shock_count == 7


# =============================================================================
# INTERPOLATE COLOR TESTS
# =============================================================================

class TestInterpolateColor:
    """Tests for interpolate_color function."""

    def test_t_zero_returns_color_a(self):
        """t=0 returns first color."""
        result = interpolate_color((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 0.0)
        assert result == (1.0, 0.0, 0.0)

    def test_t_one_returns_color_b(self):
        """t=1 returns second color."""
        result = interpolate_color((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 1.0)
        assert result == (0.0, 1.0, 0.0)

    def test_t_half_returns_midpoint(self):
        """t=0.5 returns midpoint."""
        result = interpolate_color((0.0, 0.0, 0.0), (1.0, 1.0, 1.0), 0.5)
        assert abs(result[0] - 0.5) < 1e-6
        assert abs(result[1] - 0.5) < 1e-6
        assert abs(result[2] - 0.5) < 1e-6

    def test_clamps_t_below_zero(self):
        """t below 0 is clamped."""
        result = interpolate_color((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), -0.5)
        assert result == (1.0, 0.0, 0.0)

    def test_clamps_t_above_one(self):
        """t above 1 is clamped."""
        result = interpolate_color((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), 1.5)
        assert result == (0.0, 1.0, 0.0)


# =============================================================================
# STATE CHECK TESTS
# =============================================================================

class TestStateChecks:
    """Tests for is_shocked and is_normal functions."""

    def test_is_shocked_true_when_shocked(self):
        """is_shocked returns True when SHOCKED."""
        status = ColorEffectStatus(state=ColorEffectState.SHOCKED)
        assert is_shocked(status) is True

    def test_is_shocked_false_when_normal(self):
        """is_shocked returns False when NORMAL."""
        status = ColorEffectStatus(state=ColorEffectState.NORMAL)
        assert is_shocked(status) is False

    def test_is_normal_true_when_normal(self):
        """is_normal returns True when NORMAL."""
        status = ColorEffectStatus(state=ColorEffectState.NORMAL)
        assert is_normal(status) is True

    def test_is_normal_false_when_shocked(self):
        """is_normal returns False when SHOCKED."""
        status = ColorEffectStatus(state=ColorEffectState.SHOCKED)
        assert is_normal(status) is False


# =============================================================================
# COLOR EFFECT CONTROLLER TESTS
# =============================================================================

class TestColorEffectControllerInit:
    """Tests for ColorEffectController initialization."""

    def test_initial_state_normal(self):
        """Controller starts in NORMAL state."""
        controller = ColorEffectController()
        assert controller.status.state == ColorEffectState.NORMAL

    def test_initial_shock_count_zero(self):
        """Controller starts with zero shocks."""
        controller = ColorEffectController()
        assert controller.shock_count == 0

    def test_is_shocked_initially_false(self):
        """is_shocked is False initially."""
        controller = ColorEffectController()
        assert controller.is_shocked is False

    def test_custom_config(self):
        """Custom config is used."""
        config = ColorConfig(approach_minimum=25.0)
        controller = ColorEffectController(config=config)
        assert controller._config.approach_minimum == 25.0


class TestColorEffectControllerOnContact:
    """Tests for on_contact method."""

    def test_changes_to_shocked(self):
        """on_contact changes state to shocked."""
        controller = ColorEffectController()
        controller.on_contact()
        assert controller.is_shocked is True

    def test_increments_shock_count(self):
        """on_contact increments shock count."""
        controller = ColorEffectController()
        controller.on_contact()
        controller.on_contact()
        controller.on_contact()
        assert controller.shock_count == 3


class TestColorEffectControllerUpdate:
    """Tests for update method."""

    def test_stays_shocked_when_close(self):
        """Stays shocked when still close to tendroid."""
        controller = ColorEffectController()
        controller.on_contact()
        controller.update(distance_to_tendroid=5.0)
        assert controller.is_shocked is True

    def test_exits_shocked_when_far(self):
        """Exits shocked when far from tendroid."""
        controller = ColorEffectController()
        controller.on_contact()
        controller.update(distance_to_tendroid=20.0)
        assert controller.is_shocked is False

    def test_no_change_when_normal(self):
        """No change when already normal."""
        controller = ColorEffectController()
        controller.update(distance_to_tendroid=5.0)
        assert controller.status.state == ColorEffectState.NORMAL


class TestColorEffectControllerReset:
    """Tests for reset method."""

    def test_reset_returns_to_normal(self):
        """Reset returns to normal state."""
        controller = ColorEffectController()
        controller.on_contact()
        controller.reset()
        assert controller.is_shocked is False
        assert controller.status.state == ColorEffectState.NORMAL
