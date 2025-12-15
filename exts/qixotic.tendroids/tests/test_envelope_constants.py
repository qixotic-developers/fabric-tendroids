"""
Unit Tests for Envelope Constants

Validates that envelope parameters match TEND-11 design specifications.
These tests can run without Omniverse.
"""

import sys
from pathlib import Path

# Add source to path
ext_root = Path(__file__).parent.parent
if str(ext_root) not in sys.path:
  sys.path.insert(0, str(ext_root))


class TestEnvelopeGeometry:
  """Test envelope geometry constants match design specifications."""

  def test_envelope_radius_matches_creature(self):
    """Envelope radius should match visual creature radius (6.0)."""
    from qixotic.tendroids.controllers.envelope_constants import ENVELOPE_RADIUS
    assert ENVELOPE_RADIUS == 6.0

  def test_envelope_half_height_correct(self):
    """Half height should be 6.0 (full cylinder height = 12.0)."""
    from qixotic.tendroids.controllers.envelope_constants import ENVELOPE_HALF_HEIGHT
    assert ENVELOPE_HALF_HEIGHT == 6.0

  def test_envelope_total_length_calculated(self):
    """Total length should be 2*half_height + 2*radius = 24.0."""
    from qixotic.tendroids.controllers.envelope_constants import (
      ENVELOPE_RADIUS, ENVELOPE_HALF_HEIGHT, ENVELOPE_TOTAL_LENGTH
    )
    expected = 2 * ENVELOPE_HALF_HEIGHT + 2 * ENVELOPE_RADIUS
    assert ENVELOPE_TOTAL_LENGTH == expected
    assert ENVELOPE_TOTAL_LENGTH == 24.0

  def test_envelope_axis_is_z(self):
    """Capsule axis should be Z (creature forward direction)."""
    from qixotic.tendroids.controllers.envelope_constants import ENVELOPE_AXIS
    assert ENVELOPE_AXIS == "Z"


class TestPhysXParameters:
  """Test PhysX collision parameters."""

  def test_contact_offset_positive(self):
    """Contact offset must be positive for early detection."""
    from qixotic.tendroids.controllers.envelope_constants import CONTACT_OFFSET
    assert CONTACT_OFFSET > 0
    assert CONTACT_OFFSET == 0.04  # 4cm as designed

  def test_rest_offset_positive(self):
    """Rest offset must be positive."""
    from qixotic.tendroids.controllers.envelope_constants import REST_OFFSET
    assert REST_OFFSET > 0
    assert REST_OFFSET == 0.01  # 1cm as designed

  def test_contact_offset_greater_than_rest(self):
    """Contact offset should be >= rest offset (PhysX requirement)."""
    from qixotic.tendroids.controllers.envelope_constants import (
      CONTACT_OFFSET, REST_OFFSET
    )
    assert CONTACT_OFFSET >= REST_OFFSET


class TestCollisionGroups:
  """Test collision group definitions."""

  def test_collision_groups_distinct(self):
    """Creature and tendroid collision groups should be different."""
    from qixotic.tendroids.controllers.envelope_constants import (
      CREATURE_COLLISION_GROUP, TENDROID_COLLISION_GROUP
    )
    assert CREATURE_COLLISION_GROUP != TENDROID_COLLISION_GROUP

  def test_collision_groups_positive(self):
    """Collision groups should be positive integers."""
    from qixotic.tendroids.controllers.envelope_constants import (
      CREATURE_COLLISION_GROUP, TENDROID_COLLISION_GROUP
    )
    assert CREATURE_COLLISION_GROUP > 0
    assert TENDROID_COLLISION_GROUP > 0


class TestDebugSettings:
  """Test debug visualization settings."""

  def test_debug_collider_off_by_default(self):
    """Debug collider visualization should be off by default."""
    from qixotic.tendroids.controllers.envelope_constants import DEBUG_SHOW_COLLIDER
    assert DEBUG_SHOW_COLLIDER is False

  def test_debug_color_valid_rgb(self):
    """Debug color should be valid RGB tuple."""
    from qixotic.tendroids.controllers.envelope_constants import DEBUG_COLLIDER_COLOR
    assert len(DEBUG_COLLIDER_COLOR) == 3
    assert all(0.0 <= c <= 1.0 for c in DEBUG_COLLIDER_COLOR)

  def test_debug_opacity_valid_range(self):
    """Debug opacity should be in [0, 1] range."""
    from qixotic.tendroids.controllers.envelope_constants import DEBUG_COLLIDER_OPACITY
    assert 0.0 <= DEBUG_COLLIDER_OPACITY <= 1.0
