"""
Unit tests for the Deflection Module

TEND-3: Tendroid Deflection System tests
Tests TEND-19, TEND-20, TEND-21, TEND-22, TEND-23
"""

import pytest
import math
from qixotic.tendroids.deflection import (
    # Config
    ApproachType, DeflectionLimits, DetectionZones, DeflectionConfig,
    
    # Approach calculators
    TendroidGeometry, ApproachResult,
    calculate_vertical_proximity, calculate_head_on_approach,
    calculate_pass_by_approach, detect_approach_type,
    
    # Deflection helpers
    calculate_height_ratio, lerp_deflection, calculate_proportional_deflection,
    calculate_cylinder_normal, calculate_deflection_direction,
    calculate_bend_axis, calculate_deflection,
    
    # Controller
    DeflectionController, TendroidDeflectionState,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def default_tendroid():
    """Standard tendroid geometry for tests."""
    return TendroidGeometry(
        center_x=0.0,
        center_z=0.0,
        base_y=0.0,
        height=1.0,
        radius=0.05
    )


@pytest.fixture
def default_zones():
    """Standard detection zones for tests."""
    return DetectionZones()


@pytest.fixture
def default_limits():
    """Standard deflection limits for tests."""
    return DeflectionLimits()


# =============================================================================
# TEND-19: Vertical Proximity Tests
# =============================================================================

class TestVerticalProximity:
    """Tests for vertical (pass-over) approach detection."""
    
    def test_creature_above_tendroid_tip_no_detection(self, default_tendroid, default_zones):
        """Creature above tendroid should not trigger."""
        pos = (0.1, 1.5, 0.0)  # Y=1.5 above tip at Y=1.0
        result = calculate_vertical_proximity(pos, default_tendroid, default_zones)
        
        assert result.approach_type == ApproachType.NONE
        assert not result.is_within_range
    
    def test_creature_below_tendroid_base_no_detection(self, default_tendroid, default_zones):
        """Creature below tendroid should not trigger."""
        pos = (0.1, -0.5, 0.0)  # Y=-0.5 below base at Y=0
        result = calculate_vertical_proximity(pos, default_tendroid, default_zones)
        
        assert result.approach_type == ApproachType.NONE
        assert not result.is_within_range
    
    def test_creature_at_midpoint_within_range(self, default_tendroid, default_zones):
        """Creature at tendroid midpoint should be detected."""
        pos = (0.1, 0.5, 0.0)  # Y=0.5 = midpoint, close horizontally
        result = calculate_vertical_proximity(pos, default_tendroid, default_zones)
        
        assert result.approach_type == ApproachType.VERTICAL
        assert result.is_within_range
        assert 0.45 < result.height_ratio < 0.55  # ~0.5
    
    def test_height_ratio_at_base(self, default_tendroid, default_zones):
        """Height ratio should be 0 at base."""
        pos = (0.1, 0.0, 0.0)
        result = calculate_vertical_proximity(pos, default_tendroid, default_zones)
        
        assert result.height_ratio == pytest.approx(0.0, abs=0.01)
    
    def test_height_ratio_at_tip(self, default_tendroid, default_zones):
        """Height ratio should be 1 at tip."""
        pos = (0.1, 1.0, 0.0)
        result = calculate_vertical_proximity(pos, default_tendroid, default_zones)
        
        assert result.height_ratio == pytest.approx(1.0, abs=0.01)
    
    def test_horizontal_distance_uses_xz_only(self, default_tendroid, default_zones):
        """Distance should be calculated from XZ plane only."""
        pos = (0.1, 0.5, 0.0)
        result = calculate_vertical_proximity(pos, default_tendroid, default_zones)
        
        # Distance = 0.1 - 0.05 (radius) = 0.05
        assert result.distance == pytest.approx(0.05, abs=0.01)


# =============================================================================
# TEND-20: Head-On Approach Tests
# =============================================================================

class TestHeadOnApproach:
    """Tests for head-on approach detection."""
    
    def test_moving_toward_tendroid_detected(self, default_tendroid, default_zones):
        """Creature moving directly toward tendroid should be head-on."""
        pos = (0.3, 0.5, 0.0)  # 30cm away
        vel = (-1.0, 0.0, 0.0)  # Moving toward center
        
        result = calculate_head_on_approach(pos, vel, default_tendroid, default_zones)
        
        assert result.approach_type == ApproachType.HEAD_ON
        assert result.is_within_range
    
    def test_moving_away_not_detected(self, default_tendroid, default_zones):
        """Creature moving away should not be head-on."""
        pos = (0.3, 0.5, 0.0)
        vel = (1.0, 0.0, 0.0)  # Moving away
        
        result = calculate_head_on_approach(pos, vel, default_tendroid, default_zones)
        
        assert result.approach_type == ApproachType.NONE
        assert not result.is_within_range
    
    def test_stationary_creature_not_head_on(self, default_tendroid, default_zones):
        """Stationary creature should not be detected as head-on."""
        pos = (0.3, 0.5, 0.0)
        vel = (0.0, 0.0, 0.0)
        
        result = calculate_head_on_approach(pos, vel, default_tendroid, default_zones)
        
        assert result.approach_type == ApproachType.NONE


# =============================================================================
# TEND-21: Pass-By Approach Tests
# =============================================================================

class TestPassByApproach:
    """Tests for pass-by approach detection."""
    
    def test_tangential_movement_detected(self, default_tendroid, default_zones):
        """Creature moving tangentially should be pass-by."""
        pos = (0.1, 0.5, 0.0)  # Close to tendroid
        vel = (0.0, 0.0, 1.0)  # Moving along Z axis (tangent)
        
        result = calculate_pass_by_approach(pos, vel, default_tendroid, default_zones)
        
        assert result.approach_type == ApproachType.PASS_BY
        assert result.is_within_range
    
    def test_creature_outside_detection_circle(self, default_tendroid, default_zones):
        """Creature outside detection circle not detected."""
        pos = (1.0, 0.5, 0.0)  # Far from tendroid
        vel = (0.0, 0.0, 1.0)
        
        result = calculate_pass_by_approach(pos, vel, default_tendroid, default_zones)
        
        assert not result.is_within_range


# =============================================================================
# TEND-22: Height-Based Proportionality Tests
# =============================================================================

class TestHeightProportionality:
    """Tests for height-based deflection calculation."""
    
    def test_height_ratio_calculation(self):
        """Test height ratio formula."""
        assert calculate_height_ratio(0.0, 0.0, 1.0) == 0.0
        assert calculate_height_ratio(1.0, 0.0, 1.0) == 1.0
        assert calculate_height_ratio(0.5, 0.0, 1.0) == 0.5
    
    def test_lerp_deflection_at_base(self, default_limits):
        """Deflection at base should be minimum."""
        angle = lerp_deflection(
            default_limits.minimum_deflection,
            default_limits.maximum_deflection,
            0.0
        )
        assert angle == pytest.approx(default_limits.minimum_deflection)
    
    def test_lerp_deflection_at_tip(self, default_limits):
        """Deflection at tip should be maximum."""
        angle = lerp_deflection(
            default_limits.minimum_deflection,
            default_limits.maximum_deflection,
            1.0
        )
        assert angle == pytest.approx(default_limits.maximum_deflection)
    
    def test_lerp_deflection_at_midpoint(self, default_limits):
        """Deflection at midpoint should be average."""
        angle = lerp_deflection(
            default_limits.minimum_deflection,
            default_limits.maximum_deflection,
            0.5
        )
        expected = (default_limits.minimum_deflection + default_limits.maximum_deflection) / 2
        assert angle == pytest.approx(expected)


# =============================================================================
# TEND-23: Surface Normal Tests  
# =============================================================================

class TestSurfaceNormals:
    """Tests for surface normal calculations."""
    
    def test_normal_points_outward(self, default_tendroid):
        """Normal should point from center toward point."""
        point = (1.0, 0.5, 0.0)  # On +X side
        normal = calculate_cylinder_normal(point, default_tendroid)
        
        assert normal[0] > 0  # X component positive
        assert normal[1] == pytest.approx(0.0)  # No Y component
        assert normal[2] == pytest.approx(0.0)  # No Z component
    
    def test_normal_is_unit_vector(self, default_tendroid):
        """Normal should be normalized."""
        point = (0.5, 0.5, 0.5)
        normal = calculate_cylinder_normal(point, default_tendroid)
        
        magnitude = math.sqrt(sum(n*n for n in normal))
        assert magnitude == pytest.approx(1.0, abs=0.001)
    
    def test_deflection_direction_opposite_normal(self):
        """Deflection direction should be opposite to normal."""
        normal = (1.0, 0.0, 0.0)
        direction = calculate_deflection_direction(normal)
        
        assert direction == (-1.0, 0.0, 0.0)


# =============================================================================
# Controller Integration Tests
# =============================================================================

class TestDeflectionController:
    """Integration tests for DeflectionController."""
    
    def test_register_tendroid(self, default_tendroid):
        """Test tendroid registration."""
        controller = DeflectionController()
        controller.register_tendroid(0, default_tendroid)
        
        assert 0 in controller._tendroids
        assert 0 in controller._states
    
    def test_update_deflects_nearby_creature(self, default_tendroid):
        """Test that nearby creature causes deflection."""
        controller = DeflectionController()
        controller.register_tendroid(0, default_tendroid)
        
        pos = (0.1, 0.5, 0.0)  # Close to tendroid
        vel = (-0.5, 0.0, 0.0)  # Moving toward
        
        states = controller.update(pos, vel, 0.016)
        
        assert states[0].target_angle > 0
    
    def test_disabled_controller_no_deflection(self, default_tendroid):
        """Test disabled controller produces no deflection."""
        controller = DeflectionController()
        controller.register_tendroid(0, default_tendroid)
        controller.enabled = False
        
        pos = (0.1, 0.5, 0.0)
        vel = (-0.5, 0.0, 0.0)
        
        states = controller.update(pos, vel, 0.016)
        
        assert states[0].target_angle == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
