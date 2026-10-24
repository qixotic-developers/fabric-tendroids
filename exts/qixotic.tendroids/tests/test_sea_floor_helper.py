"""Tests for sea floor height-map helpers."""

import builtins
import sys
from unittest.mock import MagicMock, patch

# Mock Warp before importing the extension package.
sys.modules["warp"] = MagicMock()

from qixotic.tendroids.environment import sea_floor_helper


class TestNoiseModule:
  """Tests for loading the procedural noise provider."""

  def test_uses_fallback_when_noise_module_is_not_readable(self):
    """A protected Kit package must not prevent sea floor generation."""
    original_import = builtins.__import__
    previous_noise_module = sea_floor_helper._noise_module

    def permission_denied_import(name, globals=None, locals=None, fromlist=(), level=0):
      if name == "noise":
        raise PermissionError(
          "[Errno 13] Permission denied: "
          "'C:\\Kit\\pip3-envs\\default-3.12\\noise\\__init__.py'"
        )
      return original_import(name, globals, locals, fromlist, level)

    try:
      sea_floor_helper._noise_module = None
      with patch("builtins.__import__", side_effect=permission_denied_import):
        noise_module = sea_floor_helper._get_noise_module()

      first_value = noise_module.pnoise2(1.25, -0.75, base=42)
      second_value = noise_module.pnoise2(1.25, -0.75, base=42)

      assert isinstance(first_value, float)
      assert first_value == second_value
    finally:
      sea_floor_helper._noise_module = previous_noise_module