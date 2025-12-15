"""
Unit Tests for ProximityHashGrid Operations

TEND-64: Initialize Warp HashGrid with scene dimensions
TEND-65: Create Warp arrays for position data
TEND-66: Implement grid rebuild on position updates
TEND-67: Integrate HashGrid with simulation loop

Run with: python -m pytest tests/test_hash_grid_operations.py -v
"""

import sys
import unittest
from unittest.mock import MagicMock


# ============================================================================
# Mock Setup (must be before imports)
# ============================================================================

class MockWarpArray:
  """Mock warp.array."""

  def __init__(self, data=None, dtype=None, device=None, shape=None):
    if data is not None:
      self._data = list(data)
      self._shape = (len(data),)
    else:
      self._data = []
      self._shape = (shape,) if shape else (0,)
    self.dtype = dtype
    self.device = device

  @property
  def shape(self):
    return self._shape


class MockHashGrid:
  """Mock warp.HashGrid."""

  def __init__(self, dim_x, dim_y, dim_z, device):
    self.dim_x = dim_x
    self.dim_y = dim_y
    self.dim_z = dim_z
    self.device = device
    self.id = 99999
    self._built = False

  def build(self, points, radius):
    self._built = True
    self._points = points
    self._radius = radius


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
    pass

  @staticmethod
  def kernel(func):
    return func


# Install mocks
sys.modules['warp'] = MockWarp
sys.modules['carb'] = MagicMock()


# ============================================================================
# Tests
# ============================================================================

class TestHashGridInitialization(unittest.TestCase):
  """TEND-64: Test HashGrid initialization."""

  def test_initialize_default_config(self):
    """Test grid initializes with default config."""
    from qixotic.tendroids.proximity import ProximityHashGrid

    grid = ProximityHashGrid()
    result = grid.initialize()

    self.assertTrue(result)
    self.assertTrue(grid.is_initialized)

  def test_initialize_custom_config(self):
    """Test grid initializes with custom config."""
    from qixotic.tendroids.proximity import ProximityHashGrid, GridConfig

    config = GridConfig(dim_x=64, dim_y=32, dim_z=64)
    grid = ProximityHashGrid(config)
    result = grid.initialize()

    self.assertTrue(result)
    self.assertEqual(grid.config.dim_x, 64)

  def test_not_initialized_before_init(self):
    """Test grid reports not initialized before init()."""
    from qixotic.tendroids.proximity import ProximityHashGrid

    grid = ProximityHashGrid()
    self.assertFalse(grid.is_initialized)


class TestPositionRegistration(unittest.TestCase):
  """TEND-65: Test Warp array creation for positions."""

  def setUp(self):
    from qixotic.tendroids.proximity import ProximityHashGrid
    self.grid = ProximityHashGrid()
    self.grid.initialize()

  def test_register_creatures(self):
    """Test creature position registration."""
    positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)]
    result = self.grid.register_creatures(positions)

    self.assertTrue(result)
    self.assertEqual(self.grid.get_creature_count(), 3)

  def test_register_tendroids(self):
    """Test tendroid position registration."""
    positions = [(5.0, 0.0, 5.0), (10.0, 0.0, 10.0)]
    result = self.grid.register_tendroids(positions)

    self.assertTrue(result)
    self.assertEqual(self.grid.get_tendroid_count(), 2)

  def test_register_empty_returns_false(self):
    """Test empty position list returns False."""
    result = self.grid.register_creatures([])
    self.assertFalse(result)

  def test_register_both_types(self):
    """Test registering both creatures and tendroids."""
    creatures = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)]
    tendroids = [(5.0, 0.0, 5.0)]

    self.grid.register_creatures(creatures)
    self.grid.register_tendroids(tendroids)

    self.assertEqual(self.grid.get_creature_count(), 2)
    self.assertEqual(self.grid.get_tendroid_count(), 1)


class TestPositionUpdates(unittest.TestCase):
  """TEND-66: Test position update functionality."""

  def setUp(self):
    from qixotic.tendroids.proximity import ProximityHashGrid
    self.grid = ProximityHashGrid()
    self.grid.initialize()
    self.grid.register_creatures([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)])

  def test_update_creatures_same_count(self):
    """Test updating creatures with same count."""
    new_positions = [(0.5, 0.0, 0.0), (1.5, 0.0, 0.0)]
    result = self.grid.update_creatures(new_positions)

    self.assertTrue(result)
    self.assertEqual(self.grid.get_creature_count(), 2)

  def test_update_creatures_different_count_re_registers(self):
    """Test updating with different count re-registers."""
    new_positions = [(0.0, 0.0, 0.0)]  # Only 1 now
    result = self.grid.update_creatures(new_positions)

    self.assertTrue(result)
    self.assertEqual(self.grid.get_creature_count(), 1)

  def test_update_unregistered_creatures_registers(self):
    """Test updating unregistered creatures auto-registers."""
    from qixotic.tendroids.proximity import ProximityHashGrid

    new_grid = ProximityHashGrid()
    new_grid.initialize()

    positions = [(0.0, 0.0, 0.0)]
    result = new_grid.update_creatures(positions)

    self.assertTrue(result)
    self.assertEqual(new_grid.get_creature_count(), 1)


class TestGridRebuild(unittest.TestCase):
  """TEND-66, TEND-67: Test grid rebuild and simulation integration."""

  def setUp(self):
    from qixotic.tendroids.proximity import ProximityHashGrid
    self.grid = ProximityHashGrid()
    self.grid.initialize()

  def test_rebuild_with_positions(self):
    """Test rebuild succeeds with registered positions."""
    self.grid.register_creatures([(0.0, 0.0, 0.0)])
    self.grid.register_tendroids([(5.0, 0.0, 0.0)])

    result = self.grid.rebuild(search_radius=1.0)
    self.assertTrue(result)

  def test_rebuild_without_init_fails(self):
    """Test rebuild fails if not initialized."""
    from qixotic.tendroids.proximity import ProximityHashGrid

    grid = ProximityHashGrid()
    # Skip initialize()
    result = grid.rebuild()

    self.assertFalse(result)

  def test_rebuild_without_positions_warns(self):
    """Test rebuild with no positions returns False."""
    result = self.grid.rebuild()
    self.assertFalse(result)

  def test_get_grid_id(self):
    """Test grid ID retrieval."""
    grid_id = self.grid.get_grid_id()
    self.assertIsNotNone(grid_id)


class TestIndexClassification(unittest.TestCase):
  """Test creature/tendroid index classification."""

  def setUp(self):
    from qixotic.tendroids.proximity import ProximityHashGrid
    self.grid = ProximityHashGrid()
    self.grid.initialize()
    # Register: 3 creatures (indices 0,1,2), 2 tendroids (indices 3,4)
    self.grid.register_creatures([(0, 0, 0), (1, 0, 0), (2, 0, 0)])
    self.grid.register_tendroids([(5, 0, 0), (6, 0, 0)])

  def test_is_creature_index(self):
    """Test creature index detection."""
    self.assertTrue(self.grid.is_creature_index(0))
    self.assertTrue(self.grid.is_creature_index(1))
    self.assertTrue(self.grid.is_creature_index(2))
    self.assertFalse(self.grid.is_creature_index(3))
    self.assertFalse(self.grid.is_creature_index(4))

  def test_is_tendroid_index(self):
    """Test tendroid index detection."""
    self.assertFalse(self.grid.is_tendroid_index(0))
    self.assertFalse(self.grid.is_tendroid_index(2))
    self.assertTrue(self.grid.is_tendroid_index(3))
    self.assertTrue(self.grid.is_tendroid_index(4))


class TestGridDestroy(unittest.TestCase):
  """Test grid cleanup."""

  def test_destroy_releases_resources(self):
    """Test destroy clears all state."""
    from qixotic.tendroids.proximity import ProximityHashGrid

    grid = ProximityHashGrid()
    grid.initialize()
    grid.register_creatures([(0, 0, 0)])

    grid.destroy()

    self.assertFalse(grid.is_initialized)
    self.assertEqual(grid.get_creature_count(), 0)
    self.assertEqual(grid.get_tendroid_count(), 0)


# ============================================================================
# Run
# ============================================================================

if __name__ == "__main__":
  unittest.main(verbosity=2)
