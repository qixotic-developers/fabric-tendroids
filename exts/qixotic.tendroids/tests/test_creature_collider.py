"""
Unit Tests for Creature Collider Helper

Tests collider creation, configuration, and destruction.
Uses mocks to run without Omniverse.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add source to path
ext_root = Path(__file__).parent.parent
if str(ext_root) not in sys.path:
  sys.path.insert(0, str(ext_root))

from tests.test_mocks import (
  MockStage, MockPrim, MockCapsule,
  MockCollisionAPI, MockPhysxCollisionAPI
)


class TestColliderCreation:
  """Test create_creature_collider function."""

  @pytest.fixture
  def patched_modules(self):
    """Patch USD modules for testing."""
    with patch.dict('sys.modules', {
      'carb': MagicMock(),
      'pxr': MagicMock(),
      'pxr.Gf': MagicMock(),
      'pxr.UsdGeom': MagicMock(),
      'pxr.UsdPhysics': MagicMock(),
      'pxr.Sdf': MagicMock(),
      'pxr.UsdShade': MagicMock(),
    }):
      yield

  def test_returns_false_for_invalid_prim(self, mock_stage, patched_modules):
    """Should return False if creature prim doesn't exist."""
    # Mock the module imports inside the function
    with patch('qixotic.tendroids.controllers.creature_collider_helper.carb') as mock_carb:
      from qixotic.tendroids.controllers.creature_collider_helper import create_creature_collider

      # Stage has no prims - should fail
      result = create_creature_collider(mock_stage, "/World/NonExistent")
      assert result is False
      mock_carb.log_error.assert_called()

  def test_creates_collider_at_correct_path(self, mock_stage_with_creature, patched_modules):
    """Should create collider as child of creature prim."""
    with patch('qixotic.tendroids.controllers.creature_collider_helper.carb') as mock_carb, \
      patch('qixotic.tendroids.controllers.creature_collider_helper.UsdGeom') as mock_geom, \
      patch('qixotic.tendroids.controllers.creature_collider_helper.UsdPhysics') as mock_physics:
      # Setup mocks
      mock_capsule = MagicMock()
      mock_capsule.GetPrim.return_value = MockPrim("/World/Creature/Collider", "Capsule")
      mock_geom.Capsule.Define.return_value = mock_capsule
      mock_geom.Imageable.return_value = MagicMock()

      from qixotic.tendroids.controllers.creature_collider_helper import create_creature_collider

      result = create_creature_collider(mock_stage_with_creature, "/World/Creature")

      # Verify capsule was defined at correct path
      mock_geom.Capsule.Define.assert_called_once()
      call_args = mock_geom.Capsule.Define.call_args
      assert "/World/Creature/Collider" in str(call_args)


class TestColliderDestruction:
  """Test destroy_creature_collider function."""

  def test_removes_existing_collider(self, mock_stage):
    """Should remove collider prim if it exists."""
    # Add collider to stage
    mock_stage.add_prim("/World/Creature/Collider", "Capsule")

    with patch('qixotic.tendroids.controllers.creature_collider_helper.carb'):
      from qixotic.tendroids.controllers.creature_collider_helper import destroy_creature_collider

      destroy_creature_collider(mock_stage, "/World/Creature")

      # Verify prim was removed
      assert "/World/Creature/Collider" in mock_stage.removed_prims

  def test_handles_missing_collider_gracefully(self, mock_stage):
    """Should not error if collider doesn't exist."""
    with patch('qixotic.tendroids.controllers.creature_collider_helper.carb'):
      from qixotic.tendroids.controllers.creature_collider_helper import destroy_creature_collider

      # Should not raise
      destroy_creature_collider(mock_stage, "/World/Creature")


class TestColliderDimensions:
  """Test that collider uses correct dimensions from constants."""

  def test_uses_envelope_constants(self, patched_modules):
    """Collider should use dimensions from envelope_constants."""
    from qixotic.tendroids.controllers.envelope_constants import (
      ENVELOPE_RADIUS, ENVELOPE_HALF_HEIGHT, ENVELOPE_AXIS
    )

    # These should match TEND-11 design
    assert ENVELOPE_RADIUS == 6.0
    assert ENVELOPE_HALF_HEIGHT == 6.0
    assert ENVELOPE_AXIS == "Z"

  @pytest.fixture
  def patched_modules(self):
    with patch.dict('sys.modules', {
      'carb': MagicMock(),
      'pxr': MagicMock(),
      'pxr.Gf': MagicMock(),
      'pxr.UsdGeom': MagicMock(),
      'pxr.UsdPhysics': MagicMock(),
      'pxr.Sdf': MagicMock(),
      'pxr.UsdShade': MagicMock(),
    }):
      yield


class TestPhysXConfiguration:
  """Test PhysX-specific collision configuration."""

  def test_contact_offset_applied(self, envelope_params):
    """Contact offset should match design specification."""
    from qixotic.tendroids.controllers.envelope_constants import CONTACT_OFFSET
    assert CONTACT_OFFSET == envelope_params['contact_offset']

  def test_rest_offset_applied(self, envelope_params):
    """Rest offset should match design specification."""
    from qixotic.tendroids.controllers.envelope_constants import REST_OFFSET
    assert REST_OFFSET == envelope_params['rest_offset']
