"""
Tests for Envelope Debug Visualization Module

Tests configuration, color utilities, and visualizer setup
without requiring Omniverse runtime.
"""

import pytest


class TestZoneColors:
    """Test zone color configuration."""

    def test_default_colors_exist(self):
        """All zone colors should be defined."""
        from qixotic.tendroids.debug import ZoneColors

        colors = ZoneColors()
        assert colors.contact is not None
        assert colors.recovery is not None
        assert colors.warning is not None
        assert colors.detection is not None
        assert colors.envelope is not None

    def test_colors_are_rgba_tuples(self):
        """Colors should be 4-element RGBA tuples."""
        from qixotic.tendroids.debug import ZoneColors

        colors = ZoneColors()
        for color in [colors.contact, colors.recovery, colors.warning,
                      colors.detection, colors.envelope]:
            assert len(color) == 4
            assert all(0.0 <= c <= 1.0 for c in color)

    def test_custom_colors(self):
        """Can create custom color schemes."""
        from qixotic.tendroids.debug import ZoneColors

        custom = ZoneColors(
            contact=(1.0, 0.0, 0.0, 1.0),
            recovery=(0.5, 0.5, 0.0, 1.0),
        )
        assert custom.contact == (1.0, 0.0, 0.0, 1.0)
        assert custom.recovery == (0.5, 0.5, 0.0, 1.0)


class TestDebugDrawSettings:
    """Test debug draw settings."""

    def test_default_enabled(self):
        """Debug draw should be enabled by default."""
        from qixotic.tendroids.debug import DebugDrawSettings

        settings = DebugDrawSettings()
        assert settings.enabled is True

    def test_all_zones_visible_by_default(self):
        """All zones should be visible by default."""
        from qixotic.tendroids.debug import DebugDrawSettings

        settings = DebugDrawSettings()
        assert settings.show_contact_zone is True
        assert settings.show_recovery_zone is True
        assert settings.show_warning_zone is True
        assert settings.show_detection_zone is True
        assert settings.show_envelope is True

    def test_can_disable_zones(self):
        """Can selectively disable zones."""
        from qixotic.tendroids.debug import DebugDrawSettings

        settings = DebugDrawSettings(
            show_detection_zone=False,
            show_warning_zone=False,
        )
        assert settings.show_detection_zone is False
        assert settings.show_warning_zone is False
        assert settings.show_contact_zone is True


class TestEnvelopeDebugConfig:
    """Test complete debug configuration."""

    def test_default_config_creation(self):
        """Can create default config."""
        from qixotic.tendroids.debug import EnvelopeDebugConfig

        config = EnvelopeDebugConfig()
        assert config.colors is not None
        assert config.settings is not None

    def test_default_config_instance(self):
        """Default config instance exists."""
        from qixotic.tendroids.debug import DEFAULT_DEBUG_CONFIG

        assert DEFAULT_DEBUG_CONFIG is not None
        assert DEFAULT_DEBUG_CONFIG.settings.enabled is True


class TestGetZoneColor:
    """Test zone color lookup function."""

    def test_known_zones(self):
        """Returns correct colors for known zones."""
        from qixotic.tendroids.debug import get_zone_color, DEFAULT_DEBUG_CONFIG

        contact = get_zone_color("contact")
        assert contact == DEFAULT_DEBUG_CONFIG.colors.contact

        detection = get_zone_color("detection")
        assert detection == DEFAULT_DEBUG_CONFIG.colors.detection

    def test_unknown_zone_returns_white(self):
        """Unknown zone returns white."""
        from qixotic.tendroids.debug import get_zone_color

        color = get_zone_color("unknown_zone")
        assert color == (1.0, 1.0, 1.0, 1.0)

    def test_custom_config(self):
        """Can use custom config."""
        from qixotic.tendroids.debug import (
            get_zone_color, EnvelopeDebugConfig, ZoneColors
        )

        custom_colors = ZoneColors(contact=(0.0, 0.0, 1.0, 1.0))
        custom_config = EnvelopeDebugConfig(colors=custom_colors)

        color = get_zone_color("contact", custom_config)
        assert color == (0.0, 0.0, 1.0, 1.0)


class TestEnvelopeVisualizer:
    """Test envelope visualizer controller."""

    def test_creation_with_defaults(self):
        """Can create visualizer with defaults."""
        from qixotic.tendroids.debug import EnvelopeVisualizer

        viz = EnvelopeVisualizer()
        assert viz is not None
        assert viz.enabled is True

    def test_toggle(self):
        """Can toggle visualization on/off."""
        from qixotic.tendroids.debug import EnvelopeVisualizer

        viz = EnvelopeVisualizer()
        assert viz.enabled is True

        result = viz.toggle()
        assert result is False
        assert viz.enabled is False

        result = viz.toggle()
        assert result is True
        assert viz.enabled is True

    def test_enabled_setter(self):
        """Can set enabled directly."""
        from qixotic.tendroids.debug import EnvelopeVisualizer

        viz = EnvelopeVisualizer()
        viz.enabled = False
        assert viz.enabled is False

    def test_custom_envelope_radius(self):
        """Can specify custom envelope radius."""
        from qixotic.tendroids.debug import EnvelopeVisualizer

        viz = EnvelopeVisualizer(envelope_radius=10.0)
        assert viz._envelope_radius == 10.0

    def test_custom_approach_params(self):
        """Can specify custom approach parameters."""
        from qixotic.tendroids.debug import EnvelopeVisualizer
        from qixotic.tendroids.proximity.proximity_config import ApproachParameters

        params = ApproachParameters(approach_epsilon=0.1)
        viz = EnvelopeVisualizer(approach_params=params)
        assert viz._approach.approach_epsilon == 0.1

    def test_update_without_debugdraw(self):
        """Update handles missing debugdraw gracefully."""
        from qixotic.tendroids.debug import EnvelopeVisualizer

        viz = EnvelopeVisualizer()
        # Should not raise even without omni.debugdraw
        viz.update((0.0, 50.0, 0.0))

    def test_set_approach_params(self):
        """Can update approach parameters."""
        from qixotic.tendroids.debug import EnvelopeVisualizer
        from qixotic.tendroids.proximity.proximity_config import ApproachParameters

        viz = EnvelopeVisualizer()
        new_params = ApproachParameters(detection_radius=2.0)
        viz.set_approach_params(new_params)
        assert viz._approach.detection_radius == 2.0

    def test_set_envelope_radius(self):
        """Can update envelope radius."""
        from qixotic.tendroids.debug import EnvelopeVisualizer

        viz = EnvelopeVisualizer()
        viz.set_envelope_radius(12.0)
        assert viz._envelope_radius == 12.0


class TestDebugDrawHelpers:
    """Test low-level drawing helper functions."""

    def test_is_debugdraw_available(self):
        """Check debugdraw availability function exists."""
        from qixotic.tendroids.debug import is_debugdraw_available

        # Will return False in test environment (no Omniverse)
        result = is_debugdraw_available()
        assert isinstance(result, bool)

    def test_color_conversion(self):
        """Test internal color conversion."""
        from qixotic.tendroids.debug.envelope_debug_draw import _color_to_uint

        # Pure red with full alpha
        color = _color_to_uint(1.0, 0.0, 0.0, 1.0)
        assert color == 0xFF0000FF  # ABGR format

        # Pure green
        color = _color_to_uint(0.0, 1.0, 0.0, 1.0)
        assert color == 0xFF00FF00

        # Pure blue
        color = _color_to_uint(0.0, 0.0, 1.0, 1.0)
        assert color == 0xFFFF0000

        # 50% alpha white
        color = _color_to_uint(1.0, 1.0, 1.0, 0.5)
        assert (color >> 24) & 0xFF == 127  # Alpha byte


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
