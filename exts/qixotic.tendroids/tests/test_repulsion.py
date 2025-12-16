"""
Tests for Repulsion System

Unit tests for surface normal calculation and repulsion force computation.
Implements TEND-99: Add unit tests for repulsion system.
"""

import math

from qixotic.tendroids.contact.repulsion_helpers import (
    RepulsionConfig,
    RepulsionResult,
    calculate_cylinder_surface_normal,
    calculate_surface_normal_from_contact,
    compute_repulsion_force,
    compute_corrected_position,
    calculate_repulsion,
)


# =============================================================================
# SURFACE NORMAL TESTS
# =============================================================================

class TestCalculateCylinderSurfaceNormal:
    """Tests for calculate_cylinder_surface_normal function."""

    def test_contact_positive_x(self):
        """Contact on +X side returns +X normal."""
        normal = calculate_cylinder_surface_normal(
            contact_point=(10.0, 5.0, 0.0),
            cylinder_center=(0.0, 5.0, 0.0),
        )
        assert normal[0] == 1.0
        assert normal[1] == 0.0
        assert normal[2] == 0.0

    def test_contact_negative_x(self):
        """Contact on -X side returns -X normal."""
        normal = calculate_cylinder_surface_normal(
            contact_point=(-10.0, 5.0, 0.0),
            cylinder_center=(0.0, 5.0, 0.0),
        )
        assert normal[0] == -1.0
        assert normal[1] == 0.0
        assert normal[2] == 0.0

    def test_contact_positive_z(self):
        """Contact on +Z side returns +Z normal."""
        normal = calculate_cylinder_surface_normal(
            contact_point=(0.0, 5.0, 10.0),
            cylinder_center=(0.0, 5.0, 0.0),
        )
        assert normal[0] == 0.0
        assert normal[1] == 0.0
        assert normal[2] == 1.0

    def test_contact_diagonal(self):
        """Contact at 45 degrees returns normalized diagonal."""
        normal = calculate_cylinder_surface_normal(
            contact_point=(10.0, 5.0, 10.0),
            cylinder_center=(0.0, 5.0, 0.0),
        )
        expected = 1.0 / math.sqrt(2.0)
        assert abs(normal[0] - expected) < 1e-6
        assert normal[1] == 0.0
        assert abs(normal[2] - expected) < 1e-6

    def test_y_coordinate_ignored(self):
        """Y difference doesn't affect horizontal normal."""
        normal1 = calculate_cylinder_surface_normal(
            contact_point=(10.0, 0.0, 0.0),
            cylinder_center=(0.0, 100.0, 0.0),
        )
        normal2 = calculate_cylinder_surface_normal(
            contact_point=(10.0, 100.0, 0.0),
            cylinder_center=(0.0, 0.0, 0.0),
        )
        assert normal1 == normal2 == (1.0, 0.0, 0.0)

    def test_contact_at_center_returns_default(self):
        """Contact at cylinder axis returns default normal."""
        normal = calculate_cylinder_surface_normal(
            contact_point=(5.0, 10.0, 5.0),
            cylinder_center=(5.0, 0.0, 5.0),
        )
        assert normal == (1.0, 0.0, 0.0)


class TestCalculateSurfaceNormalFromContact:
    """Tests for calculate_surface_normal_from_contact function."""

    def test_creature_outside_tendroid(self):
        """Creature outside returns correct normal and negative penetration."""
        normal, penetration = calculate_surface_normal_from_contact(
            creature_position=(20.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        assert normal == (1.0, 0.0, 0.0)
        assert penetration == 6.0 - 20.0  # -14.0 (outside)

    def test_creature_inside_tendroid(self):
        """Creature inside returns positive penetration."""
        normal, penetration = calculate_surface_normal_from_contact(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        assert normal == (1.0, 0.0, 0.0)
        assert penetration == 6.0 - 3.0  # 3.0 (inside)

    def test_creature_at_surface(self):
        """Creature exactly at surface has zero penetration."""
        normal, penetration = calculate_surface_normal_from_contact(
            creature_position=(6.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        assert abs(penetration) < 1e-6


# =============================================================================
# REPULSION FORCE TESTS
# =============================================================================

class TestComputeRepulsionForce:
    """Tests for compute_repulsion_force function."""

    def test_base_force_applied(self):
        """Base force is applied along normal."""
        config = RepulsionConfig(base_force=100.0)
        force = compute_repulsion_force(
            surface_normal=(1.0, 0.0, 0.0),
            config=config,
        )
        assert force[0] == 100.0
        assert force[1] == 0.0
        assert force[2] == 0.0

    def test_penetration_increases_force(self):
        """Deeper penetration increases force."""
        config = RepulsionConfig(base_force=100.0, penetration_multiplier=2.0)
        force = compute_repulsion_force(
            surface_normal=(1.0, 0.0, 0.0),
            penetration_depth=10.0,
            config=config,
        )
        # 100 + 10 * 2 = 120
        assert force[0] == 120.0

    def test_velocity_increases_force(self):
        """Approach velocity increases force."""
        config = RepulsionConfig(base_force=100.0, velocity_multiplier=0.5)
        force = compute_repulsion_force(
            surface_normal=(1.0, 0.0, 0.0),
            approach_velocity=20.0,
            config=config,
        )
        # 100 + 20 * 0.5 = 110
        assert force[0] == 110.0

    def test_force_clamped_to_max(self):
        """Force is clamped to max_force."""
        config = RepulsionConfig(base_force=100.0, max_force=150.0,
                                  penetration_multiplier=100.0)
        force = compute_repulsion_force(
            surface_normal=(1.0, 0.0, 0.0),
            penetration_depth=10.0,  # Would be 100 + 1000 = 1100
            config=config,
        )
        assert force[0] == 150.0

    def test_force_clamped_to_min(self):
        """Force never goes below min_force."""
        config = RepulsionConfig(base_force=5.0, min_force=10.0)
        force = compute_repulsion_force(
            surface_normal=(1.0, 0.0, 0.0),
            config=config,
        )
        assert force[0] == 10.0

    def test_diagonal_normal(self):
        """Force applied correctly for diagonal normal."""
        config = RepulsionConfig(base_force=100.0)
        n = 1.0 / math.sqrt(2.0)
        force = compute_repulsion_force(
            surface_normal=(n, 0.0, n),
            config=config,
        )
        assert abs(force[0] - 100.0 * n) < 1e-6
        assert force[1] == 0.0
        assert abs(force[2] - 100.0 * n) < 1e-6

    def test_default_config_used(self):
        """Default config is used when none provided."""
        force = compute_repulsion_force(
            surface_normal=(1.0, 0.0, 0.0),
        )
        # Should use default base_force of 100
        assert force[0] == 100.0


# =============================================================================
# CORRECTED POSITION TESTS
# =============================================================================

class TestComputeCorrectedPosition:
    """Tests for compute_corrected_position function."""

    def test_creature_inside_pushed_outside(self):
        """Creature inside tendroid is pushed to surface."""
        corrected = compute_corrected_position(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
            safety_margin=0.01,
        )
        # Should be at radius + margin in +X direction
        assert abs(corrected[0] - 6.01) < 1e-6
        assert corrected[1] == 5.0  # Y unchanged
        assert abs(corrected[2]) < 1e-6

    def test_creature_outside_unchanged_direction(self):
        """Creature outside maintains direction from center."""
        corrected = compute_corrected_position(
            creature_position=(20.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        # Still on +X side
        assert corrected[0] > 0

    def test_y_coordinate_preserved(self):
        """Y coordinate is preserved during correction."""
        corrected = compute_corrected_position(
            creature_position=(3.0, 100.0, 0.0),
            tendroid_position=(0.0, 0.0, 0.0),
            tendroid_radius=6.0,
        )
        assert corrected[1] == 100.0

    def test_diagonal_correction(self):
        """Diagonal penetration corrected along radial."""
        corrected = compute_corrected_position(
            creature_position=(2.0, 5.0, 2.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
            safety_margin=0.0,
        )
        # Distance from center should be exactly radius
        dx = corrected[0] - 0.0
        dz = corrected[2] - 0.0
        dist = math.sqrt(dx * dx + dz * dz)
        assert abs(dist - 6.0) < 1e-6

    def test_at_center_pushed_positive_x(self):
        """Creature at center pushed in +X direction."""
        corrected = compute_corrected_position(
            creature_position=(0.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
            safety_margin=0.01,
        )
        assert corrected[0] == 6.01
        assert corrected[2] == 0.0


# =============================================================================
# FULL REPULSION CALCULATION TESTS
# =============================================================================

class TestCalculateRepulsion:
    """Tests for calculate_repulsion combined function."""

    def test_returns_repulsion_result(self):
        """Returns complete RepulsionResult."""
        result = calculate_repulsion(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        assert isinstance(result, RepulsionResult)
        assert result.force_vector is not None
        assert result.surface_normal is not None
        assert result.corrected_position is not None

    def test_force_magnitude_calculated(self):
        """Force magnitude is correctly calculated."""
        result = calculate_repulsion(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        fx, fy, fz = result.force_vector
        expected_mag = math.sqrt(fx*fx + fy*fy + fz*fz)
        assert abs(result.force_magnitude - expected_mag) < 1e-6

    def test_penetration_depth_positive_when_inside(self):
        """Penetration depth is positive when inside."""
        result = calculate_repulsion(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        assert result.penetration_depth == 3.0  # 6 - 3

    def test_penetration_depth_zero_when_outside(self):
        """Penetration depth is zero when outside."""
        result = calculate_repulsion(
            creature_position=(20.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
        )
        assert result.penetration_depth == 0.0

    def test_custom_config_applied(self):
        """Custom config is applied to calculation."""
        config = RepulsionConfig(base_force=200.0, max_force=1000.0)
        result = calculate_repulsion(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            tendroid_radius=6.0,
            config=config,
        )
        # Force should reflect 200 base + penetration bonus
        assert result.force_magnitude > 200.0

    def test_approach_velocity_included(self):
        """Approach velocity affects force."""
        result_no_vel = calculate_repulsion(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            approach_velocity=0.0,
        )
        result_with_vel = calculate_repulsion(
            creature_position=(3.0, 5.0, 0.0),
            tendroid_position=(0.0, 5.0, 0.0),
            approach_velocity=50.0,
        )
        assert result_with_vel.force_magnitude > result_no_vel.force_magnitude
