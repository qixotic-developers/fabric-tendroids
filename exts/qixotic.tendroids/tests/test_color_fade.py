"""
Tests for Color Fade System

Unit tests for recovery fade calculations.
Implements TEND-107: Add visual comparison test scenario.
"""

from qixotic.tendroids.contact.color_fade_helpers import (
    FadeConfig,
    FadeMode,
    calculate_distance_fade,
    calculate_speed_fade,
    calculate_time_fade,
    calculate_fade_progress,
    apply_easing,
    blend_fade_modes,
)


# =============================================================================
# FADE CONFIG TESTS
# =============================================================================

class TestFadeConfig:
    """Tests for FadeConfig defaults."""

    def test_default_mode_is_distance(self):
        """Default mode is DISTANCE."""
        config = FadeConfig()
        assert config.mode == FadeMode.DISTANCE

    def test_default_distance_settings(self):
        """Default distance settings are reasonable."""
        config = FadeConfig()
        assert config.fade_start_distance == 6.0
        assert config.fade_end_distance == 15.0

    def test_default_speed_settings(self):
        """Default speed settings are reasonable."""
        config = FadeConfig()
        assert config.max_speed == 50.0
        assert config.min_speed == 5.0

    def test_custom_config(self):
        """Custom config values work."""
        config = FadeConfig(
            mode=FadeMode.SPEED,
            fade_start_distance=10.0,
            max_speed=100.0,
        )
        assert config.mode == FadeMode.SPEED
        assert config.fade_start_distance == 10.0
        assert config.max_speed == 100.0


# =============================================================================
# DISTANCE FADE TESTS
# =============================================================================

class TestCalculateDistanceFade:
    """Tests for distance-proportional fade."""

    def test_at_start_distance_returns_zero(self):
        """At start distance, progress is 0."""
        config = FadeConfig(fade_start_distance=6.0, fade_end_distance=15.0)
        result = calculate_distance_fade(6.0, config)
        assert result == 0.0

    def test_below_start_distance_returns_zero(self):
        """Below start distance, progress is 0."""
        config = FadeConfig(fade_start_distance=6.0)
        result = calculate_distance_fade(3.0, config)
        assert result == 0.0

    def test_at_end_distance_returns_one(self):
        """At end distance, progress is 1."""
        config = FadeConfig(fade_end_distance=15.0)
        result = calculate_distance_fade(15.0, config)
        assert result == 1.0

    def test_beyond_end_distance_returns_one(self):
        """Beyond end distance, progress is 1."""
        config = FadeConfig(fade_end_distance=15.0)
        result = calculate_distance_fade(20.0, config)
        assert result == 1.0

    def test_midpoint_returns_half(self):
        """At midpoint, progress is 0.5."""
        config = FadeConfig(fade_start_distance=0.0, fade_end_distance=10.0)
        result = calculate_distance_fade(5.0, config)
        assert abs(result - 0.5) < 1e-6

    def test_linear_interpolation(self):
        """Fade is linear between start and end."""
        config = FadeConfig(fade_start_distance=0.0, fade_end_distance=100.0)
        assert abs(calculate_distance_fade(25.0, config) - 0.25) < 1e-6
        assert abs(calculate_distance_fade(75.0, config) - 0.75) < 1e-6


# =============================================================================
# SPEED FADE TESTS
# =============================================================================

class TestCalculateSpeedFade:
    """Tests for speed-proportional fade."""

    def test_at_max_speed_returns_zero(self):
        """At max speed, progress is 0 (full shock)."""
        config = FadeConfig(max_speed=50.0, min_speed=5.0)
        result = calculate_speed_fade(50.0, config)
        assert result == 0.0

    def test_above_max_speed_returns_zero(self):
        """Above max speed, progress is 0."""
        config = FadeConfig(max_speed=50.0)
        result = calculate_speed_fade(100.0, config)
        assert result == 0.0

    def test_at_min_speed_returns_one(self):
        """At min speed, progress is 1 (normal)."""
        config = FadeConfig(min_speed=5.0)
        result = calculate_speed_fade(5.0, config)
        assert result == 1.0

    def test_below_min_speed_returns_one(self):
        """Below min speed, progress is 1."""
        config = FadeConfig(min_speed=5.0)
        result = calculate_speed_fade(2.0, config)
        assert result == 1.0

    def test_inverse_relationship(self):
        """Higher speed = lower progress (more shock)."""
        config = FadeConfig(max_speed=50.0, min_speed=0.0)
        high_speed = calculate_speed_fade(40.0, config)
        low_speed = calculate_speed_fade(10.0, config)
        assert high_speed < low_speed


# =============================================================================
# TIME FADE TESTS
# =============================================================================

class TestCalculateTimeFade:
    """Tests for time-based fade."""

    def test_at_zero_time_returns_zero(self):
        """At start, progress is 0."""
        config = FadeConfig(fade_duration=0.5)
        result = calculate_time_fade(0.0, config)
        assert result == 0.0

    def test_negative_time_returns_zero(self):
        """Negative time returns 0."""
        result = calculate_time_fade(-1.0)
        assert result == 0.0

    def test_at_duration_returns_one(self):
        """At duration, progress is 1."""
        config = FadeConfig(fade_duration=0.5)
        result = calculate_time_fade(0.5, config)
        assert result == 1.0

    def test_beyond_duration_returns_one(self):
        """Beyond duration, progress is 1."""
        config = FadeConfig(fade_duration=0.5)
        result = calculate_time_fade(1.0, config)
        assert result == 1.0

    def test_half_duration_returns_half(self):
        """At half duration, progress is 0.5."""
        config = FadeConfig(fade_duration=1.0)
        result = calculate_time_fade(0.5, config)
        assert abs(result - 0.5) < 1e-6


# =============================================================================
# CALCULATE FADE PROGRESS TESTS
# =============================================================================

class TestCalculateFadeProgress:
    """Tests for unified fade progress calculation."""

    def test_distance_mode_uses_distance(self):
        """DISTANCE mode uses distance parameter."""
        config = FadeConfig(
            mode=FadeMode.DISTANCE,
            fade_start_distance=0.0,
            fade_end_distance=10.0,
        )
        result = calculate_fade_progress(config, distance=5.0)
        assert abs(result - 0.5) < 1e-6

    def test_speed_mode_uses_speed(self):
        """SPEED mode uses speed parameter."""
        config = FadeConfig(
            mode=FadeMode.SPEED,
            max_speed=100.0,
            min_speed=0.0,
        )
        result = calculate_fade_progress(config, speed=50.0)
        assert abs(result - 0.5) < 1e-6

    def test_time_mode_uses_elapsed_time(self):
        """TIME mode uses elapsed_time parameter."""
        config = FadeConfig(
            mode=FadeMode.TIME,
            fade_duration=2.0,
        )
        result = calculate_fade_progress(config, elapsed_time=1.0)
        assert abs(result - 0.5) < 1e-6


# =============================================================================
# EASING TESTS
# =============================================================================

class TestApplyEasing:
    """Tests for easing functions."""

    def test_linear_unchanged(self):
        """Linear easing returns input unchanged."""
        assert apply_easing(0.5, "linear") == 0.5

    def test_ease_in_slower_start(self):
        """Ease in is slower at start."""
        linear = 0.5
        eased = apply_easing(0.5, "ease_in")
        assert eased < linear  # Quadratic: 0.5^2 = 0.25

    def test_ease_out_faster_start(self):
        """Ease out is faster at start."""
        linear = 0.5
        eased = apply_easing(0.5, "ease_out")
        assert eased > linear

    def test_ease_in_out_at_midpoint(self):
        """Ease in-out at midpoint."""
        result = apply_easing(0.5, "ease_in_out")
        assert abs(result - 0.5) < 1e-6

    def test_clamps_input(self):
        """Clamps input to 0-1 range."""
        assert apply_easing(-0.5, "linear") == 0.0
        assert apply_easing(1.5, "linear") == 1.0


# =============================================================================
# BLEND FADE MODES TESTS
# =============================================================================

class TestBlendFadeModes:
    """Tests for blending fade modes."""

    def test_full_distance_weight(self):
        """100% distance weight uses only distance."""
        result = blend_fade_modes(
            distance_progress=1.0,
            speed_progress=0.0,
            distance_weight=1.0,
        )
        assert result == 1.0

    def test_full_speed_weight(self):
        """0% distance weight uses only speed."""
        result = blend_fade_modes(
            distance_progress=1.0,
            speed_progress=0.0,
            distance_weight=0.0,
        )
        assert result == 0.0

    def test_equal_weight_averages(self):
        """50/50 weight averages values."""
        result = blend_fade_modes(
            distance_progress=1.0,
            speed_progress=0.0,
            distance_weight=0.5,
        )
        assert abs(result - 0.5) < 1e-6

    def test_clamps_weight(self):
        """Weight is clamped to 0-1."""
        result1 = blend_fade_modes(1.0, 0.0, distance_weight=-0.5)
        result2 = blend_fade_modes(1.0, 0.0, distance_weight=1.5)
        assert result1 == 0.0  # Weight clamped to 0
        assert result2 == 1.0  # Weight clamped to 1


# =============================================================================
# VISUAL COMPARISON SCENARIO TESTS (TEND-107)
# =============================================================================

class TestVisualComparisonScenarios:
    """
    Test scenarios for visual comparison between fade modes.
    
    These tests verify the different visual behaviors that can be
    compared when running the actual simulation.
    """

    def test_distance_mode_gradual_from_contact(self):
        """Distance mode: gradual fade as creature moves away."""
        config = FadeConfig(
            mode=FadeMode.DISTANCE,
            fade_start_distance=6.0,
            fade_end_distance=15.0,
        )
        # Simulate creature moving away
        distances = [6.0, 8.0, 10.0, 12.0, 15.0]
        progress = [calculate_fade_progress(config, distance=d) for d in distances]
        
        # Should be monotonically increasing
        for i in range(1, len(progress)):
            assert progress[i] >= progress[i-1]

    def test_speed_mode_fast_then_slow(self):
        """Speed mode: stays shock while fast, fades as slowing."""
        config = FadeConfig(
            mode=FadeMode.SPEED,
            max_speed=50.0,
            min_speed=5.0,
        )
        # Simulate creature slowing down
        speeds = [50.0, 40.0, 30.0, 20.0, 10.0, 5.0]
        progress = [calculate_fade_progress(config, speed=s) for s in speeds]
        
        # Should be monotonically increasing as speed decreases
        for i in range(1, len(progress)):
            assert progress[i] >= progress[i-1]

    def test_distance_vs_speed_different_profiles(self):
        """Distance and speed modes have different fade profiles."""
        dist_config = FadeConfig(mode=FadeMode.DISTANCE)
        speed_config = FadeConfig(mode=FadeMode.SPEED)
        
        # At same "normalized" progress point, behaviors differ
        dist_progress = calculate_fade_progress(dist_config, distance=10.5)
        speed_progress = calculate_fade_progress(speed_config, speed=27.5)
        
        # Both should be around 0.5 but calculated differently
        assert 0.4 < dist_progress < 0.6
        assert 0.4 < speed_progress < 0.6

    def test_hybrid_mode_smooth_transition(self):
        """Blended mode provides smooth transition."""
        # Use 70% distance, 30% speed
        distance_vals = [6.0, 9.0, 12.0, 15.0]
        speed_vals = [40.0, 30.0, 20.0, 10.0]
        
        dist_config = FadeConfig(mode=FadeMode.DISTANCE)
        speed_config = FadeConfig(mode=FadeMode.SPEED)
        
        results = []
        for d, s in zip(distance_vals, speed_vals):
            d_prog = calculate_fade_progress(dist_config, distance=d)
            s_prog = calculate_fade_progress(speed_config, speed=s)
            blended = blend_fade_modes(d_prog, s_prog, distance_weight=0.7)
            results.append(blended)
        
        # Should be monotonically increasing
        for i in range(1, len(results)):
            assert results[i] >= results[i-1]
