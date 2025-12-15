"""
Tests for Proximity Kernel (TEND-16)

Verifies GPU-accelerated proximity detection with single tendroid.
Tests horizontal distance calculation and force vector output.

Run with: python -m pytest tests/test_proximity_kernel.py -v
"""

import math

import pytest


class TestProximityKernelUnit:
  """Unit tests for proximity kernel without GPU."""

  def test_horizontal_distance_calculation(self):
    """TEND-72: Verify horizontal distance ignores Y coordinate."""
    # Creature at (5, 10, 0), Tendroid at (0, 0, 0) with radius 1
    # Horizontal distance = sqrt(5^2 + 0^2) = 5
    # Surface distance = 5 - 1 = 4

    creature_pos = (5.0, 10.0, 0.0)
    tendroid_pos = (0.0, 0.0, 0.0)
    tendroid_radius = 1.0

    dx = creature_pos[0] - tendroid_pos[0]
    dz = creature_pos[2] - tendroid_pos[2]
    horizontal_dist = math.sqrt(dx * dx + dz * dz)
    surface_dist = horizontal_dist - tendroid_radius

    assert horizontal_dist == 5.0
    assert surface_dist == 4.0

  def test_horizontal_distance_diagonal(self):
    """TEND-72: Verify diagonal XZ distance."""
    # Creature at (3, 5, 4), Tendroid at (0, 0, 0) with radius 0.5
    # Horizontal distance = sqrt(3^2 + 4^2) = 5

    creature_pos = (3.0, 5.0, 4.0)
    tendroid_pos = (0.0, 0.0, 0.0)

    dx = creature_pos[0] - tendroid_pos[0]
    dz = creature_pos[2] - tendroid_pos[2]
    horizontal_dist = math.sqrt(dx * dx + dz * dz)

    assert horizontal_dist == 5.0

  def test_zone_classification_contact(self):
    """Verify contact zone (< epsilon)."""
    from qixotic.tendroids.proximity import ApproachParameters

    params = ApproachParameters(
      approach_epsilon=0.04,
      approach_minimum=0.15,
      warning_distance=0.25,
      detection_radius=1.0,
    )

    assert params.get_zone(0.02) == "contact"
    assert params.get_zone(0.04) == "contact"  # At boundary

  def test_zone_classification_recovering(self):
    """Verify recovering zone (epsilon < d < minimum)."""
    from qixotic.tendroids.proximity import ApproachParameters

    params = ApproachParameters(
      approach_epsilon=0.04,
      approach_minimum=0.15,
      warning_distance=0.25,
      detection_radius=1.0,
    )

    assert params.get_zone(0.05) == "recovering"
    assert params.get_zone(0.10) == "recovering"

  def test_zone_classification_approaching(self):
    """Verify approaching zone (minimum < d < warning)."""
    from qixotic.tendroids.proximity import ApproachParameters

    params = ApproachParameters(
      approach_epsilon=0.04,
      approach_minimum=0.15,
      warning_distance=0.25,
      detection_radius=1.0,
    )

    assert params.get_zone(0.20) == "approaching"

  def test_zone_classification_detected(self):
    """Verify detected zone (warning < d < detection)."""
    from qixotic.tendroids.proximity import ApproachParameters

    params = ApproachParameters(
      approach_epsilon=0.04,
      approach_minimum=0.15,
      warning_distance=0.25,
      detection_radius=1.0,
    )

    assert params.get_zone(0.50) == "detected"
    assert params.get_zone(0.99) == "detected"

  def test_zone_classification_idle(self):
    """Verify idle zone (> detection_radius)."""
    from qixotic.tendroids.proximity import ApproachParameters

    params = ApproachParameters(
      approach_epsilon=0.04,
      approach_minimum=0.15,
      warning_distance=0.25,
      detection_radius=1.0,
    )

    # Note: At exactly detection_radius (1.0), still "detected"
    # Idle requires > detection_radius
    assert params.get_zone(1.0) == "detected"  # Boundary is inclusive
    assert params.get_zone(1.01) == "idle"
    assert params.get_zone(5.0) == "idle"

  def test_force_direction_calculation(self):
    """TEND-73: Verify force direction is away from tendroid."""
    # Creature at (2, 0, 0), Tendroid at (0, 0, 0)
    # Expected direction: (1, 0, 0)

    creature_pos = (2.0, 0.0, 0.0)
    tendroid_pos = (0.0, 0.0, 0.0)

    dx = creature_pos[0] - tendroid_pos[0]
    dz = creature_pos[2] - tendroid_pos[2]
    dist = math.sqrt(dx * dx + dz * dz)

    dir_x = dx / dist
    dir_z = dz / dist

    assert abs(dir_x - 1.0) < 0.0001
    assert abs(dir_z - 0.0) < 0.0001

  def test_force_falloff_at_boundary(self):
    """TEND-73: Verify force is zero at detection boundary."""
    # At detection radius, falloff = (1 - 1)^2 = 0
    detection_radius = 1.0
    distance = detection_radius

    t = distance / detection_radius
    falloff = (1.0 - t) ** 2

    assert falloff == 0.0

  def test_force_falloff_at_surface(self):
    """TEND-73: Verify force is maximum at surface."""
    # At surface (distance = 0), falloff = (1 - 0)^2 = 1
    detection_radius = 1.0
    distance = 0.0

    t = distance / detection_radius
    falloff = (1.0 - t) ** 2

    assert falloff == 1.0

  def test_force_falloff_midpoint(self):
    """TEND-73: Verify smooth falloff at midpoint."""
    # At half distance, falloff = (1 - 0.5)^2 = 0.25
    detection_radius = 1.0
    distance = 0.5

    t = distance / detection_radius
    falloff = (1.0 - t) ** 2

    assert falloff == 0.25


class TestProximityResultDataclass:
  """Test ProximityResult dataclass."""

  def test_proximity_result_contact(self):
    """Verify is_contact property."""
    from qixotic.tendroids.proximity import ProximityResult

    result = ProximityResult(
      creature_idx=0,
      tendroid_idx=0,
      surface_distance=0.02,
      zone="contact",
      force=(5.0, 0.0, 0.0)
    )

    assert result.is_contact is True
    assert result.is_detected is True

  def test_proximity_result_idle(self):
    """Verify idle state properties."""
    from qixotic.tendroids.proximity import ProximityResult

    result = ProximityResult(
      creature_idx=0,
      tendroid_idx=0,
      surface_distance=2.0,
      zone="idle",
      force=(0.0, 0.0, 0.0)
    )

    assert result.is_contact is False
    assert result.is_detected is False


# GPU Integration tests require Warp and CUDA
# Skip if warp not properly installed or no GPU available
def _has_warp_gpu():
  """Check if Warp with GPU support is available."""
  try:
    import warp as wp
    # Check if vec3 is callable (real warp, not a mock)
    if not callable(getattr(wp, 'vec3', None)):
      return False
    # Try to initialize warp
    wp.init()
    return True
  except Exception:
    return False


@pytest.mark.skipif(
  not _has_warp_gpu(),
  reason="GPU tests require Warp with CUDA support"
)
class TestProximityKernelGPU:
  """Integration tests requiring GPU."""

  @pytest.fixture
  def detector(self):
    """Create configured detector."""
    from qixotic.tendroids.proximity import SingleTendroidProximity

    detector = SingleTendroidProximity()
    detector.configure(
      tendroid_position=(0.0, 0.0, 0.0),
      tendroid_radius=0.5
    )
    yield detector
    detector.destroy()

  def test_check_proximity_contact(self, detector):
    """Test contact detection."""
    result = detector.check_proximity((0.52, 0.0, 0.0))
    # Distance to surface = 0.52 - 0.5 = 0.02 (< epsilon 0.04)
    assert result.zone == "contact"
    assert result.is_contact is True

  def test_check_proximity_idle(self, detector):
    """Test idle state far from tendroid."""
    result = detector.check_proximity((5.0, 0.0, 0.0))
    # Distance to surface = 5.0 - 0.5 = 4.5 (> detection 1.0)
    assert result.zone == "idle"
    assert result.is_detected is False

  def test_check_proximity_batch(self, detector):
    """Test batch proximity checking."""
    positions = [
      (0.52, 0.0, 0.0),  # Contact
      (5.0, 0.0, 0.0),  # Idle
      (1.0, 0.0, 0.0),  # Detected (0.5 from surface)
    ]

    results = detector.check_proximity_batch(positions)

    assert len(results) == 3
    assert results[0].zone == "contact"
    assert results[1].zone == "idle"
    assert results[2].zone == "detected"


if __name__ == "__main__":
  pytest.main([__file__, "-v"])
