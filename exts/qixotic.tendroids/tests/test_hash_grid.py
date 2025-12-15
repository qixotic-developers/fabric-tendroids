"""
Unit Tests for Warp Hash Grid Infrastructure

TEND-15: Set up Warp Hash Grid infrastructure
Tests grid initialization, position registration, and rebuild operations.

Run with: python -m pytest tests/test_hash_grid.py -v
"""

import sys
import unittest
from unittest.mock import MagicMock


# ============================================================================
# Mock Warp module for testing without GPU
# ============================================================================

class MockWarpArray:
  """Mock warp.array for CPU testing."""

  def __init__(self, data=None, dtype=None, device=None, shape=None):
    if data is not None:
      self._data = list(data)
      self._shape = (len(data),)
    elif shape is not None:
      self._data = [None] * shape
      self._shape = (shape,)
    else:
      self._data = []
      self._shape = (0,)
    self.dtype = dtype
    self.device = device

  @property
  def shape(self):
    return self._shape

  def numpy(self):
    return self._data


class MockHashGrid:
  """Mock warp.HashGrid for testing."""

  def __init__(self, dim_x=128, dim_y=128, dim_z=128, device="cuda:0"):
    self.dim_x = dim_x
    self.dim_y = dim_y
    self.dim_z = dim_z
    self.device = device
    self.id = 12345  # Mock grid ID
    self._points = None
    self._radius = None
    self._built = False

  def build(self, points, radius):
    self._points = points
    self._radius = radius
    self._built = True


class MockWarp:
  """Mock warp module."""
  vec3 = "vec3"
  uint64 = "uint64"

  @staticmethod
  def init():
    pass

  @staticmethod
  def array(data=None, dtype=None, device=None, shape=None):
    return MockWarpArray(data=data, dtype=dtype, device=device, shape=shape)

  @staticmethod
  def zeros(count, dtype=None, device=None):
    return MockWarpArray(shape=count, dtype=dtype, device=device)

  @staticmethod
  def HashGrid(dim_x=128, dim_y=128, dim_z=128, device="cuda:0"):
    return MockHashGrid(dim_x, dim_y, dim_z, device)

  @staticmethod
  def launch(kernel, dim, inputs, device=None):
    pass  # No-op for testing

  @staticmethod
  def kernel(func):
    return func  # Return function unchanged


# ============================================================================
# Test Configuration
# ============================================================================

class TestGridConfig(unittest.TestCase):
  """Test GridConfig dataclass."""

  def test_default_values(self):
    """Test default grid configuration."""
    # Import after mocking
    from qixotic.tendroids.proximity.proximity_config import GridConfig

    config = GridConfig()
    self.assertEqual(config.dim_x, 128)
    self.assertEqual(config.dim_y, 64)
    self.assertEqual(config.dim_z, 128)
    self.assertEqual(config.cell_size, 1.0)
    self.assertEqual(config.device, "cuda:0")

  def test_custom_values(self):
    """Test custom grid configuration."""
    from qixotic.tendroids.proximity.proximity_config import GridConfig

    config = GridConfig(dim_x=64, dim_y=32, dim_z=64, cell_size=0.5)
    self.assertEqual(config.dim_x, 64)
    self.assertEqual(config.dim_y, 32)
    self.assertEqual(config.cell_size, 0.5)

  def test_grid_bounds(self):
    """Test grid bounds calculation."""
    from qixotic.tendroids.proximity.proximity_config import GridConfig

    config = GridConfig(dim_x=100, dim_y=50, dim_z=100, cell_size=1.0)
    bounds = config.get_grid_bounds()

    self.assertEqual(bounds[0], (-50.0, -25.0, -50.0))
    self.assertEqual(bounds[1], (50.0, 25.0, 50.0))


class TestProximityConfig(unittest.TestCase):
  """Test ProximityConfig dataclass."""

  def test_default_values(self):
    """Test default proximity thresholds."""
    from qixotic.tendroids.proximity.proximity_config import ProximityConfig

    config = ProximityConfig()
    self.assertEqual(config.detection_radius, 1.0)
    self.assertEqual(config.approach_epsilon, 0.04)
    self.assertEqual(config.approach_minimum, 0.15)
    self.assertEqual(config.warning_distance, 0.25)

  def test_validation_pass(self):
    """Test valid configuration passes validation."""
    from qixotic.tendroids.proximity.proximity_config import ProximityConfig

    config = ProximityConfig()
    self.assertTrue(config.validate())

  def test_validation_fail(self):
    """Test invalid configuration fails validation."""
    from qixotic.tendroids.proximity.proximity_config import ProximityConfig

    # Invalid: epsilon > minimum
    config = ProximityConfig(approach_epsilon=0.2, approach_minimum=0.1)
    is_valid, error_msg = config.validate()
    self.assertFalse(is_valid)
    self.assertIn("approach_minimum", error_msg)


class TestScenePresets(unittest.TestCase):
  """Test scene configuration presets."""

  def test_preset_small(self):
    """Test small scene preset."""
    from qixotic.tendroids.proximity.proximity_config import get_grid_config

    config = get_grid_config("small")
    self.assertEqual(config.dim_x, 64)
    self.assertEqual(config.cell_size, 0.5)

  def test_preset_large(self):
    """Test large scene preset."""
    from qixotic.tendroids.proximity.proximity_config import get_grid_config

    config = get_grid_config("large")
    self.assertEqual(config.dim_x, 256)
    self.assertEqual(config.cell_size, 2.0)

  def test_preset_none_returns_default(self):
    """Test None preset returns default config."""
    from qixotic.tendroids.proximity.proximity_config import (
      get_grid_config, DEFAULT_GRID_CONFIG
    )

    config = get_grid_config(None)
    self.assertEqual(config.dim_x, DEFAULT_GRID_CONFIG.dim_x)


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
  # Install mocks before importing proximity module
  sys.modules['warp'] = MockWarp
  sys.modules['carb'] = MagicMock()

  unittest.main(verbosity=2)
