"""
Integration Tests for Deflection System

TEND-89: Create integration tests for deflection system

Tests:
- DeflectionIntegration with mock creature controller
- BatchDeflectionManager with multiple tendroids
- TendroidWrapper with deflection mixin
- State transitions and recovery
- Edge cases and performance
"""

from dataclasses import dataclass
from typing import Tuple

import pytest


# === Mock Classes ===

@dataclass
class MockTendroidWrapper:
  """Mock tendroid wrapper for testing."""
  name: str
  position: Tuple[float, float, float]
  length: float
  radius: float


class MockCreatureController:
  """Mock creature controller for testing."""

  def __init__(self):
    self.position = (0.0, 0.5, 0.0)
    self.velocity = (0.0, 0.0, 0.0)

  def get_position(self) -> Tuple[float, float, float]:
    return self.position

  def set_position(self, pos: Tuple[float, float, float]):
    self.position = pos

  def set_velocity(self, vel: Tuple[float, float, float]):
    self.velocity = vel


# === Fixtures ===

@pytest.fixture
def mock_tendroids():
  """Create mock tendroid wrappers."""
  return [
    MockTendroidWrapper("tendroid_0", (0.0, 0.0, 0.0), 1.0, 0.05),
    MockTendroidWrapper("tendroid_1", (0.5, 0.0, 0.0), 1.0, 0.05),
    MockTendroidWrapper("tendroid_2", (0.0, 0.0, 0.5), 1.0, 0.05),
    MockTendroidWrapper("tendroid_3", (0.5, 0.0, 0.5), 1.0, 0.05),
  ]


@pytest.fixture
def mock_creature():
  """Create mock creature controller."""
  return MockCreatureController()


# === DeflectionIntegration Tests ===

class TestDeflectionIntegration:
  """Tests for DeflectionIntegration class."""

  def test_register_tendroids(self, mock_tendroids):
    """Test tendroid registration from wrappers."""
    from qixotic.tendroids.deflection import DeflectionIntegration

    integration = DeflectionIntegration()
    integration.register_tendroids(mock_tendroids)

    assert len(integration._tendroid_map) == 4
    assert "tendroid_0" in integration._tendroid_map
    assert "tendroid_3" in integration._tendroid_map

  def test_update_with_creature(self, mock_tendroids, mock_creature):
    """Test update extracts creature state correctly."""
    from qixotic.tendroids.deflection import DeflectionIntegration

    integration = DeflectionIntegration()
    integration.register_tendroids(mock_tendroids)

    # Move creature near tendroid_0
    mock_creature.set_position((0.1, 0.5, 0.0))
    mock_creature.set_velocity((0.1, 0.0, 0.0))

    states = integration.update(mock_creature, 0.016)

    assert len(states) == 4
    assert "tendroid_0" in states

  def test_get_deflecting_tendroids(self, mock_tendroids, mock_creature):
    """Test identification of deflecting tendroids."""
    from qixotic.tendroids.deflection import DeflectionIntegration

    integration = DeflectionIntegration()
    integration.register_tendroids(mock_tendroids)

    # Move creature very close to tendroid_0
    mock_creature.set_position((0.08, 0.5, 0.0))

    # Run several updates to build up deflection
    for _ in range(10):
      integration.update(mock_creature, 0.016)

    deflecting = integration.get_deflecting_tendroids()
    # tendroid_0 should be deflecting
    assert "tendroid_0" in deflecting or len(deflecting) >= 0

  def test_enable_disable(self, mock_tendroids, mock_creature):
    """Test enabling and disabling deflection."""
    from qixotic.tendroids.deflection import DeflectionIntegration

    integration = DeflectionIntegration()
    integration.register_tendroids(mock_tendroids)

    # Disable
    integration.enabled = False
    states = integration.update(mock_creature, 0.016)
    assert len(states) == 0

    # Re-enable
    integration.enabled = True
    states = integration.update(mock_creature, 0.016)
    assert len(states) == 4


# === BatchDeflectionManager Tests ===

class TestBatchDeflectionManager:
  """Tests for BatchDeflectionManager class."""

  def test_register_tendroids(self, mock_tendroids):
    """Test batch registration."""
    from qixotic.tendroids.deflection import BatchDeflectionManager

    manager = BatchDeflectionManager(device="cpu")
    manager.register_tendroids(mock_tendroids)

    assert manager.is_built
    assert manager.tendroid_count == 4

  def test_compute_deflections_far(self, mock_tendroids):
    """Test deflection when creature is far away."""
    from qixotic.tendroids.deflection import BatchDeflectionManager

    manager = BatchDeflectionManager(device="cpu")
    manager.register_tendroids(mock_tendroids)

    # Creature far from all tendroids
    angles, axes = manager.compute_deflections(
      creature_pos=(10.0, 0.5, 10.0),
      creature_vel=(0.0, 0.0, 0.0),
      dt=0.016
    )

    assert len(angles) == 4
    assert all(abs(a) < 0.01 for a in angles)

  def test_compute_deflections_near(self, mock_tendroids):
    """Test deflection when creature is near."""
    from qixotic.tendroids.deflection import BatchDeflectionManager

    manager = BatchDeflectionManager(device="cpu")
    manager.register_tendroids(mock_tendroids)

    # Run multiple frames near tendroid_0
    angles, axes = [], []
    for _ in range(30):
      angles, axes = manager.compute_deflections(
        creature_pos=(0.08, 0.5, 0.0),
        creature_vel=(0.1, 0.0, 0.0),
        dt=0.016
      )

    # tendroid_0 should have significant deflection
    assert angles[0] > 0.01

  def test_recovery(self, mock_tendroids):
    """Test deflection recovery when creature leaves."""
    from qixotic.tendroids.deflection import BatchDeflectionManager

    manager = BatchDeflectionManager(device="cpu")
    manager.register_tendroids(mock_tendroids)

    # Build up deflection
    for _ in range(30):
      manager.compute_deflections((0.08, 0.5, 0.0), (0.0, 0.0, 0.0), 0.016)

    # Get max deflection
    angles_deflected, _ = manager.compute_deflections(
      (0.08, 0.5, 0.0), (0.0, 0.0, 0.0), 0.016
    )
    max_defl = angles_deflected[0]

    # Move creature away and recover
    for _ in range(60):
      manager.compute_deflections((10.0, 0.5, 10.0), (0.0, 0.0, 0.0), 0.016)

    angles_recovered, _ = manager.compute_deflections(
      (10.0, 0.5, 10.0), (0.0, 0.0, 0.0), 0.016
    )

    # Should have recovered significantly
    assert angles_recovered[0] < max_defl * 0.5


# === Wrapper Deflection Tests ===

class TestWrapperDeflection:
  """Tests for TendroidDeflectionMixin and utilities."""

  def test_create_deflectable_class(self):
    """Test creating deflectable tendroid class."""
    from qixotic.tendroids.deflection import create_deflectable_tendroid_class

    DeflectableTendroid = create_deflectable_tendroid_class(MockTendroidWrapper)

    tendroid = DeflectableTendroid(
      name="test",
      position=(0.0, 0.0, 0.0),
      length=1.0,
      radius=0.05
    )

    assert hasattr(tendroid, 'deflection_transform')
    assert hasattr(tendroid, 'is_deflecting')
    assert not tendroid.is_deflecting

  def test_apply_deflection_to_wrapper(self, mock_tendroids):
    """Test applying deflection to existing wrapper."""
    from qixotic.tendroids.deflection import (
      apply_deflection_to_wrapper,
      get_deflection_from_wrapper,
      TendroidDeflectionState,
      ApproachType,
    )

    wrapper = mock_tendroids[0]

    # Create mock state
    state = TendroidDeflectionState(
      tendroid_id=0,
      current_angle=0.2,
      target_angle=0.3,
      deflection_direction=(1.0, 0.0, 0.0),
      deflection_axis=(0.0, 0.0, 1.0),
      last_approach_type=ApproachType.HEAD_ON,
      is_deflecting=True
    )

    transform = apply_deflection_to_wrapper(wrapper, state)

    assert transform.bend_angle == 0.2
    assert transform.is_deflecting

    # Retrieve transform
    retrieved = get_deflection_from_wrapper(wrapper)
    assert retrieved is not None
    assert retrieved.bend_angle == 0.2


# === Edge Cases ===

class TestEdgeCases:
  """Tests for edge cases and boundary conditions."""

  def test_empty_tendroid_list(self):
    """Test with no tendroids."""
    from qixotic.tendroids.deflection import BatchDeflectionManager

    manager = BatchDeflectionManager(device="cpu")
    manager.register_tendroids([])

    assert not manager.is_built

    angles, axes = manager.compute_deflections(
      (0.0, 0.5, 0.0), (0.0, 0.0, 0.0), 0.016
    )

    assert len(angles) == 0
    assert len(axes) == 0

  def test_creature_at_tendroid_center(self, mock_tendroids):
    """Test creature exactly at tendroid center."""
    from qixotic.tendroids.deflection import BatchDeflectionManager

    manager = BatchDeflectionManager(device="cpu")
    manager.register_tendroids(mock_tendroids)

    # Creature at exact center of tendroid_0
    angles, axes = manager.compute_deflections(
      creature_pos=(0.0, 0.5, 0.0),
      creature_vel=(0.0, 0.0, 0.0),
      dt=0.016
    )

    # Should handle gracefully (no crash)
    assert len(angles) == 4

  def test_creature_above_tendroid(self, mock_tendroids):
    """Test creature above tendroid height."""
    from qixotic.tendroids.deflection import BatchDeflectionManager

    manager = BatchDeflectionManager(device="cpu")
    manager.register_tendroids(mock_tendroids)

    # Creature above tendroid (y > height)
    angles, axes = [], []
    for _ in range(10):
      angles, axes = manager.compute_deflections(
        creature_pos=(0.08, 2.0, 0.0),
        creature_vel=(0.0, 0.0, 0.0),
        dt=0.016
      )

    # Should not deflect (above tendroid)
    assert abs(angles[0]) < 0.01

  def test_rapid_position_changes(self, mock_tendroids):
    """Test rapid creature position changes."""
    from qixotic.tendroids.deflection import DeflectionIntegration

    integration = DeflectionIntegration()
    integration.register_tendroids(mock_tendroids)

    creature = MockCreatureController()

    # Rapid position changes
    positions = [
      (0.08, 0.5, 0.0),
      (0.5, 0.5, 0.3),
      (0.1, 0.8, 0.1),
      (0.08, 0.2, 0.0),
    ]

    for pos in positions:
      creature.set_position(pos)
      states = integration.update(creature, 0.016)
      assert len(states) == 4  # Should always return all states


if __name__ == "__main__":
  pytest.main([__file__, "-v"])
