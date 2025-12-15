"""
Unit Tests for Envelope Collision Detection

Tests for TEND-14: Unit tests for envelope collision detection.
Tests geometric collision algorithms for the creature capsule envelope.
"""

import pytest
import math
import sys
from pathlib import Path

# Add source to path
ext_root = Path(__file__).parent.parent
if str(ext_root) not in sys.path:
    sys.path.insert(0, str(ext_root))

from qixotic.tendroids.controllers.envelope_collision import (
    Vec3, Capsule, CollisionResult,
    closest_point_on_segment,
    point_capsule_collision,
    sphere_capsule_collision,
    calculate_approach_velocity,
    is_glancing_contact,
    is_head_on_contact,
)
from qixotic.tendroids.controllers.envelope_constants import (
    ENVELOPE_RADIUS,
    ENVELOPE_HALF_HEIGHT,
    CONTACT_OFFSET,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def creature_capsule():
    """Standard creature capsule at origin, aligned with Z-axis."""
    return Capsule(
        center=Vec3(0, 50, 0),  # 50 units up
        axis=Vec3(0, 0, 1),     # Z-axis (forward)
        half_height=ENVELOPE_HALF_HEIGHT,  # 6.0
        radius=ENVELOPE_RADIUS,  # 6.0
    )


@pytest.fixture
def simple_capsule():
    """Simple test capsule at origin."""
    return Capsule(
        center=Vec3(0, 0, 0),
        axis=Vec3(0, 0, 1),
        half_height=5.0,
        radius=2.0,
    )


# =============================================================================
# Vec3 Tests
# =============================================================================

class TestVec3:
    """Test Vec3 helper class."""
    
    def test_length(self):
        v = Vec3(3, 4, 0)
        assert v.length() == pytest.approx(5.0)
    
    def test_normalized(self):
        v = Vec3(10, 0, 0)
        n = v.normalized()
        assert n.x == pytest.approx(1.0)
        assert n.length() == pytest.approx(1.0)
    
    def test_dot_product(self):
        a = Vec3(1, 0, 0)
        b = Vec3(0, 1, 0)
        assert a.dot(b) == pytest.approx(0.0)  # Perpendicular
        
        c = Vec3(1, 0, 0)
        assert a.dot(c) == pytest.approx(1.0)  # Parallel


# =============================================================================
# TEND-61: Glancing Contact Tests
# =============================================================================

class TestGlancingContactDetection:
    """Test glancing contact detection - TEND-61."""
    
    def test_tangent_velocity_is_glancing(self, simple_capsule):
        """Velocity parallel to surface is glancing."""
        # Point just touching cylinder surface
        point = Vec3(2.0, 0, 0)  # At radius distance
        collision = point_capsule_collision(point, simple_capsule)
        
        # Velocity tangent to surface (along Z)
        velocity = Vec3(0, 0, 10)
        
        assert is_glancing_contact(collision, velocity)
    
    def test_perpendicular_velocity_not_glancing(self, simple_capsule):
        """Velocity perpendicular to surface is not glancing."""
        point = Vec3(2.0, 0, 0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # Velocity toward center (perpendicular to surface)
        velocity = Vec3(-10, 0, 0)
        
        assert not is_glancing_contact(collision, velocity)
    
    def test_45_degree_approach_classification(self, simple_capsule):
        """45-degree approach should be borderline glancing."""
        point = Vec3(2.0, 0, 0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # 45-degree velocity
        velocity = Vec3(-1, 0, 1).normalized() * 10
        
        # cos(45°) ≈ 0.707, threshold is 0.5
        assert not is_glancing_contact(collision, velocity, glancing_threshold=0.5)
        assert is_glancing_contact(collision, velocity, glancing_threshold=0.8)
    
    def test_glancing_contact_on_cap(self, simple_capsule):
        """Glancing contact on hemispherical cap."""
        # Point on cap edge
        point = Vec3(2.0, 0, 5.0)  # At cap
        collision = point_capsule_collision(point, simple_capsule)
        
        assert collision.contact_type == "cap_b"
        
        # Velocity tangent to cap surface
        velocity = Vec3(0, 10, 0)  # Perpendicular to XZ plane
        
        # Should be glancing since velocity is tangent
        assert is_glancing_contact(collision, velocity)


# =============================================================================
# TEND-62: Head-On Contact Tests
# =============================================================================

class TestHeadOnContactDetection:
    """Test head-on contact detection - TEND-62."""
    
    def test_direct_approach_is_head_on(self, simple_capsule):
        """Direct approach perpendicular to surface is head-on."""
        point = Vec3(2.0, 0, 0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # Velocity directly toward center
        velocity = Vec3(-10, 0, 0)
        
        assert is_head_on_contact(collision, velocity)
    
    def test_tangent_approach_not_head_on(self, simple_capsule):
        """Tangent approach is not head-on."""
        point = Vec3(2.0, 0, 0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # Velocity along surface
        velocity = Vec3(0, 0, 10)
        
        assert not is_head_on_contact(collision, velocity)
    
    def test_head_on_cap_contact(self, simple_capsule):
        """Head-on contact with hemispherical cap."""
        # Point directly in front of cap
        point = Vec3(0, 0, 7.0)  # Beyond cap (5 + 2 = 7)
        collision = point_capsule_collision(point, simple_capsule)
        
        assert collision.contact_type == "cap_b"
        
        # Velocity toward cap center
        velocity = Vec3(0, 0, -10)
        
        assert is_head_on_contact(collision, velocity)
    
    def test_head_on_threshold_sensitivity(self, simple_capsule):
        """Test head-on threshold parameter."""
        point = Vec3(2.0, 0, 0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # 60-degree approach (cos(60°) ≈ 0.5)
        angle = math.radians(60)
        velocity = Vec3(-math.cos(angle), 0, math.sin(angle)) * 10
        
        # Should not be head-on with default 0.7 threshold
        assert not is_head_on_contact(collision, velocity, head_on_threshold=0.7)
        # Should be head-on with lower threshold
        assert is_head_on_contact(collision, velocity, head_on_threshold=0.4)


# =============================================================================
# TEND-63: No False Positives Tests
# =============================================================================

class TestNoFalsePositives:
    """Test that collisions outside envelope return false - TEND-63."""
    
    def test_point_far_from_capsule(self, creature_capsule):
        """Point far from capsule should not collide."""
        far_point = Vec3(100, 50, 0)  # 100 units away
        collision = point_capsule_collision(far_point, creature_capsule)
        
        assert not collision.hit
        assert collision.distance > 0
    
    def test_point_just_outside_radius(self, simple_capsule):
        """Point just outside radius should not collide."""
        # Radius is 2.0, place point at 2.1
        point = Vec3(2.1, 0, 0)
        collision = point_capsule_collision(point, simple_capsule)
        
        assert not collision.hit
        assert collision.distance == pytest.approx(0.1, abs=0.01)
    
    def test_point_outside_cap(self, simple_capsule):
        """Point outside hemispherical cap should not collide."""
        # Cap extends to z = 5 + 2 = 7
        point = Vec3(0, 0, 8.0)
        collision = point_capsule_collision(point, simple_capsule)
        
        assert not collision.hit
        assert collision.distance == pytest.approx(1.0, abs=0.01)
    
    def test_sphere_outside_capsule(self, simple_capsule):
        """Sphere not touching capsule should not collide."""
        # Capsule radius 2.0, sphere radius 1.0, center at 4.0
        sphere_center = Vec3(4.0, 0, 0)
        sphere_radius = 1.0
        
        collision = sphere_capsule_collision(
            sphere_center, sphere_radius, simple_capsule
        )
        
        assert not collision.hit
        assert collision.distance == pytest.approx(1.0, abs=0.01)
    
    def test_no_collision_along_axis_extension(self, simple_capsule):
        """Points along axis extension (beyond caps) should not collide."""
        # Point far along positive Z beyond cap
        point = Vec3(0, 0, 20)
        collision = point_capsule_collision(point, simple_capsule)
        
        assert not collision.hit
        # Distance should be from cap center (z=5) to point (z=20) minus radius
        expected_distance = 15 - 2  # 13
        assert collision.distance == pytest.approx(expected_distance, abs=0.1)
    
    def test_multiple_positions_outside_envelope(self, creature_capsule):
        """Test grid of positions outside envelope."""
        outside_positions = [
            Vec3(20, 50, 0),    # Far right
            Vec3(-20, 50, 0),   # Far left
            Vec3(0, 50, 30),    # Far front
            Vec3(0, 50, -30),   # Far back
            Vec3(0, 70, 0),     # Far above
            Vec3(0, 30, 0),     # Far below
        ]
        
        for pos in outside_positions:
            collision = point_capsule_collision(pos, creature_capsule)
            assert not collision.hit, f"False positive at {pos}"


# =============================================================================
# Contact Offset Tests
# =============================================================================

class TestContactOffset:
    """Test contact offset expands collision detection zone."""
    
    def test_contact_offset_expands_detection(self, simple_capsule):
        """Contact offset should detect contacts earlier."""
        # Point at radius + 0.03 (inside contact offset zone)
        point = Vec3(2.03, 0, 0)
        
        # Without offset - no collision
        collision_no_offset = point_capsule_collision(point, simple_capsule, 0.0)
        assert not collision_no_offset.hit
        
        # With 0.04 offset - collision (point is within expanded zone)
        collision_with_offset = point_capsule_collision(point, simple_capsule, 0.04)
        assert collision_with_offset.hit
    
    def test_design_contact_offset_value(self, creature_capsule):
        """Test with designed CONTACT_OFFSET value."""
        # Point just outside physical radius, inside contact zone
        just_outside = ENVELOPE_RADIUS + CONTACT_OFFSET / 2
        point = Vec3(just_outside, 50, 0)
        
        collision = point_capsule_collision(
            point, creature_capsule, CONTACT_OFFSET
        )
        
        assert collision.hit


# =============================================================================
# Contact Type Classification Tests
# =============================================================================

class TestContactTypeClassification:
    """Test correct classification of contact location."""
    
    def test_cylinder_contact(self, simple_capsule):
        """Contact on cylinder body (not caps)."""
        point = Vec3(2.0, 0, 0)  # Middle of cylinder
        collision = point_capsule_collision(point, simple_capsule)
        
        assert collision.contact_type == "cylinder"
    
    def test_cap_a_contact(self, simple_capsule):
        """Contact on bottom cap (negative axis direction)."""
        point = Vec3(0, 0, -7.0)  # Beyond bottom cap
        collision = point_capsule_collision(point, simple_capsule)
        
        assert collision.contact_type == "cap_a"
    
    def test_cap_b_contact(self, simple_capsule):
        """Contact on top cap (positive axis direction)."""
        point = Vec3(0, 0, 7.0)  # Beyond top cap
        collision = point_capsule_collision(point, simple_capsule)
        
        assert collision.contact_type == "cap_b"
    
    def test_contact_at_cylinder_cap_boundary(self, simple_capsule):
        """Contact at boundary between cylinder and cap."""
        # Right at the cap start (z = half_height = 5)
        point = Vec3(2.0, 0, 5.0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # Should be classified as cap since t >= 1.0
        assert collision.contact_type == "cap_b"


# =============================================================================
# Contact Normal Accuracy Tests
# =============================================================================

class TestContactNormalAccuracy:
    """Test accuracy of computed contact normals."""
    
    def test_normal_points_outward_cylinder(self, simple_capsule):
        """Normal should point outward from cylinder surface."""
        point = Vec3(2.0, 0, 0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # Normal should point in +X direction
        assert collision.contact_normal.x == pytest.approx(1.0, abs=0.01)
        assert collision.contact_normal.y == pytest.approx(0.0, abs=0.01)
        assert collision.contact_normal.z == pytest.approx(0.0, abs=0.01)
    
    def test_normal_points_outward_cap(self, simple_capsule):
        """Normal should point outward from cap surface."""
        point = Vec3(0, 0, 7.0)
        collision = point_capsule_collision(point, simple_capsule)
        
        # Normal should point in +Z direction
        assert collision.contact_normal.z == pytest.approx(1.0, abs=0.01)
    
    def test_normal_is_unit_length(self, simple_capsule):
        """Contact normal should be unit length."""
        test_points = [
            Vec3(2.0, 0, 0),
            Vec3(0, 0, 7.0),
            Vec3(1.5, 1.5, 3.0),
        ]
        
        for point in test_points:
            collision = point_capsule_collision(point, simple_capsule)
            assert collision.contact_normal.length() == pytest.approx(1.0, abs=0.01)
    
    def test_normal_direction_at_45_degrees(self, simple_capsule):
        """Normal direction for point at 45 degrees from axis."""
        point = Vec3(1.414, 1.414, 0)  # 45 degrees in XY plane
        collision = point_capsule_collision(point, simple_capsule)
        
        expected_x = 1.0 / math.sqrt(2)
        expected_y = 1.0 / math.sqrt(2)
        
        assert collision.contact_normal.x == pytest.approx(expected_x, abs=0.01)
        assert collision.contact_normal.y == pytest.approx(expected_y, abs=0.01)


# =============================================================================
# Approach Velocity Tests
# =============================================================================

class TestApproachVelocity:
    """Test approach velocity calculation."""
    
    def test_approaching_velocity_positive(self, simple_capsule):
        """Velocity toward capsule should be positive."""
        pos = Vec3(10, 0, 0)
        vel = Vec3(-5, 0, 0)  # Moving toward capsule
        
        approach = calculate_approach_velocity(pos, vel, simple_capsule)
        
        assert approach > 0
    
    def test_receding_velocity_negative(self, simple_capsule):
        """Velocity away from capsule should be negative."""
        pos = Vec3(10, 0, 0)
        vel = Vec3(5, 0, 0)  # Moving away from capsule
        
        approach = calculate_approach_velocity(pos, vel, simple_capsule)
        
        assert approach < 0
    
    def test_tangent_velocity_zero(self, simple_capsule):
        """Velocity tangent to capsule should be near zero."""
        pos = Vec3(10, 0, 0)
        vel = Vec3(0, 0, 5)  # Moving parallel to axis
        
        approach = calculate_approach_velocity(pos, vel, simple_capsule)
        
        assert approach == pytest.approx(0.0, abs=0.01)


# =============================================================================
# Wave Motion Induced Contact Tests
# =============================================================================

class TestWaveMotionContact:
    """Test contacts that occur due to wave-like motion patterns."""
    
    def test_sinusoidal_approach(self, creature_capsule):
        """Simulate sinusoidal motion approaching capsule."""
        # Object oscillating in X while moving toward capsule
        time_steps = 10
        amplitude = 2.0
        
        collisions_detected = []
        
        for t in range(time_steps):
            # Sinusoidal X position, constant approach in Y
            x = amplitude * math.sin(t * 0.5)
            z = 20 - t * 2  # Approaching from z=20 toward capsule at z=0
            
            point = Vec3(x, 50, z)
            collision = point_capsule_collision(point, creature_capsule)
            collisions_detected.append(collision.hit)
        
        # Should detect collision as object gets close
        assert any(collisions_detected), "Should detect collision during approach"
        assert not all(collisions_detected), "Shouldn't collide at all times"
    
    def test_oscillating_contact(self, simple_capsule):
        """Test object that oscillates in and out of contact."""
        # Object oscillating around surface
        center_distance = 2.0  # At surface
        amplitude = 0.5
        
        contacts = []
        for t in range(20):
            r = center_distance + amplitude * math.sin(t * 0.5)
            point = Vec3(r, 0, 0)
            collision = point_capsule_collision(point, simple_capsule)
            contacts.append(collision.hit)
        
        # Should have mix of contact and no-contact
        assert any(contacts) and not all(contacts)
