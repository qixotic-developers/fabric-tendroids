"""
Envelope Visualizer Controller

Main controller class for visualizing creature envelope and proximity zones.
Integrates with creature controller and proximity configuration.
"""

from typing import Optional, Tuple

import carb

from .envelope_debug_config import (
    EnvelopeDebugConfig,
    DEFAULT_DEBUG_CONFIG,
    get_zone_color,
)
from .envelope_debug_draw import (
    is_debugdraw_available,
    get_draw_interface,
    draw_circle_xz,
    draw_sphere_wireframe,
)
from ..proximity.proximity_config import (
    ApproachParameters,
    DEFAULT_APPROACH_PARAMS,
)
from ..controllers.envelope_constants import ENVELOPE_RADIUS


class EnvelopeVisualizer:
    """
    Visualizes creature envelope and proximity detection zones.

    Draws concentric zones around the creature position:
    - Envelope: Physical collision boundary (cyan)
    - Contact: Danger zone (red)
    - Recovery: Safe clearance (orange)
    - Warning: Attention zone (yellow)
    - Detection: Outer awareness (green)
    """

    def __init__(
        self,
        approach_params: Optional[ApproachParameters] = None,
        config: Optional[EnvelopeDebugConfig] = None,
        envelope_radius: float = ENVELOPE_RADIUS,
    ):
        """
        Initialize the envelope visualizer.

        Args:
            approach_params: Proximity zone distances
            config: Debug visualization config
            envelope_radius: Physical envelope radius
        """
        self._approach = approach_params or DEFAULT_APPROACH_PARAMS
        self._config = config or DEFAULT_DEBUG_CONFIG
        self._envelope_radius = envelope_radius
        self._draw_interface = None
        self._enabled = True

        carb.log_info("[EnvelopeVisualizer] Initialized")

    @property
    def enabled(self) -> bool:
        """Check if visualization is enabled."""
        return self._enabled and self._config.settings.enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Enable or disable visualization."""
        self._enabled = value

    def toggle(self) -> bool:
        """Toggle visualization on/off. Returns new state."""
        self._enabled = not self._enabled
        state = "ON" if self._enabled else "OFF"
        carb.log_info(f"[EnvelopeVisualizer] Debug draw {state}")
        return self._enabled

    def update(self, creature_position: Tuple[float, float, float]) -> None:
        """
        Draw envelope visualization at creature position.

        Call this every frame from the main update loop.

        Args:
            creature_position: Current creature (x, y, z) position
        """
        if not self.enabled:
            return

        if not is_debugdraw_available():
            return

        # Lazy init draw interface
        if self._draw_interface is None:
            self._draw_interface = get_draw_interface()
            if self._draw_interface is None:
                return

        self._draw_zones(creature_position)

    def _draw_zones(self, pos: Tuple[float, float, float]) -> None:
        """Draw all enabled zone circles."""
        settings = self._config.settings
        segments = settings.segment_count

        # Apply height offset for visibility
        draw_pos = (pos[0], pos[1] + settings.height_offset, pos[2])

        # Draw from outside in for proper layering

        # Detection zone (green, outermost)
        if settings.show_detection_zone:
            radius = self._envelope_radius + self._approach.detection_radius
            color = get_zone_color("detection", self._config)
            draw_circle_xz(
                self._draw_interface, draw_pos, radius, color, segments
            )

        # Warning zone (yellow)
        if settings.show_warning_zone:
            radius = self._envelope_radius + self._approach.warning_distance
            color = get_zone_color("warning", self._config)
            draw_circle_xz(
                self._draw_interface, draw_pos, radius, color, segments
            )

        # Recovery zone (orange)
        if settings.show_recovery_zone:
            radius = self._envelope_radius + self._approach.approach_minimum
            color = get_zone_color("recovery", self._config)
            draw_circle_xz(
                self._draw_interface, draw_pos, radius, color, segments
            )

        # Contact zone (red)
        if settings.show_contact_zone:
            radius = self._envelope_radius + self._approach.approach_epsilon
            color = get_zone_color("contact", self._config)
            draw_circle_xz(
                self._draw_interface, draw_pos, radius, color, segments
            )

        # Envelope boundary (cyan, innermost)
        if settings.show_envelope:
            color = get_zone_color("envelope", self._config)
            draw_sphere_wireframe(
                self._draw_interface, draw_pos, self._envelope_radius,
                color, segments
            )

    def set_approach_params(self, params: ApproachParameters) -> None:
        """Update proximity zone parameters."""
        self._approach = params

    def set_envelope_radius(self, radius: float) -> None:
        """Update physical envelope radius."""
        self._envelope_radius = radius
