"""
Bubble controls section for V2 control panel

Manages bubble motion, timing, and visual parameters with live updates.
"""

import omni.ui as ui

from .slider_row import create_float_slider_row


class BubbleControls:
  """Bubble parameter controls with live binding to bubble manager."""

  def __init__(self, bubble_manager=None):
    """
    Initialize bubble controls.

    Args:
        bubble_manager: V2BubbleManager to bind (can be set later)
    """
    self.bubble_manager = bubble_manager

  def set_bubble_manager(self, bubble_manager):
    """Bind to a bubble manager for live updates."""
    self.bubble_manager = bubble_manager

  def _get_config(self):
    """Get config from bubble manager or return None."""
    if self.bubble_manager:
      return self.bubble_manager.config
    return None

  def build(self, parent: ui.VStack = None):
    """Build bubble controls UI."""
    with ui.CollapsableFrame("Bubble Settings", height=0, collapsed=False):
      with ui.VStack(spacing=2):
        cfg = self._get_config()

        # Rise speed (inside tendroid)
        create_float_slider_row(
          "Rise Speed:", cfg.rise_speed if cfg else 60.0, 20.0, 120.0,
          "Bubble rise speed inside tendroid (units/sec)",
          self._on_rise_speed_changed,
          precision=0
        )

        # Released rise speed
        create_float_slider_row(
          "Float Speed:", cfg.released_rise_speed if cfg else 40.0, 10.0, 80.0,
          "Bubble rise speed after release (units/sec)",
          self._on_released_speed_changed,
          precision=0
        )

        # Diameter multiplier
        create_float_slider_row(
          "Size Mult:", cfg.diameter_multiplier if cfg else 1.1, 0.5, 2.0,
          "Bubble size relative to deformation (1.0 = exact fit)",
          self._on_diameter_mult_changed,
          precision=2
        )

        # Pop height range
        create_float_slider_row(
          "Min Pop Ht:", cfg.min_pop_height if cfg else 150.0, 50.0, 300.0,
          "Minimum height above tendroid before pop",
          self._on_min_pop_changed,
          precision=0
        )

        create_float_slider_row(
          "Max Pop Ht:", cfg.max_pop_height if cfg else 250.0, 100.0, 400.0,
          "Maximum height above tendroid before pop",
          self._on_max_pop_changed,
          precision=0
        )

        # Respawn delay
        create_float_slider_row(
          "Respawn Dly:", cfg.respawn_delay if cfg else 1.0, 0.0, 5.0,
          "Seconds before new bubble spawns after pop",
          self._on_respawn_delay_changed,
          precision=1
        )

  def _on_rise_speed_changed(self, value: float):
    """Handle rise speed change."""
    cfg = self._get_config()
    if cfg:
      cfg.rise_speed = value

  def _on_released_speed_changed(self, value: float):
    """Handle released rise speed change."""
    cfg = self._get_config()
    if cfg:
      cfg.released_rise_speed = value

  def _on_diameter_mult_changed(self, value: float):
    """Handle diameter multiplier change."""
    cfg = self._get_config()
    if cfg:
      cfg.diameter_multiplier = value

  def _on_min_pop_changed(self, value: float):
    """Handle min pop height change."""
    cfg = self._get_config()
    if cfg:
      cfg.min_pop_height = value

  def _on_max_pop_changed(self, value: float):
    """Handle max pop height change."""
    cfg = self._get_config()
    if cfg:
      cfg.max_pop_height = value

  def _on_respawn_delay_changed(self, value: float):
    """Handle respawn delay change."""
    cfg = self._get_config()
    if cfg:
      cfg.respawn_delay = value
