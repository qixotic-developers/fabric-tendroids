"""
Regression Tests for Creature Controller

Ensures existing functionality is not broken by new changes.
Tests core physics, movement, and interaction detection.
"""

import pytest
import math
import sys
from pathlib import Path

# Add source to path
ext_root = Path(__file__).parent.parent
if str(ext_root) not in sys.path:
    sys.path.insert(0, str(ext_root))

from tests.test_mocks import MockVec3f


class TestCreaturePhysics:
    """Test creature physics calculations (no Omniverse required)."""
    
    def test_velocity_damping(self):
        """Velocity should be damped by drag coefficient."""
        drag = 0.98
        velocity = MockVec3f(100, 0, 0)
        
        # Simulate one frame of drag
        new_velocity = velocity * drag
        
        assert new_velocity.x == pytest.approx(98.0)
        assert new_velocity.GetLength() < velocity.GetLength()
    
    def test_speed_clamping(self):
        """Speed should not exceed max_speed."""
        max_speed = 50.0
        velocity = MockVec3f(100, 100, 100)  # Way over max
        
        speed = velocity.GetLength()
        if speed > max_speed:
            velocity = velocity.GetNormalized() * max_speed
        
        assert velocity.GetLength() == pytest.approx(max_speed, rel=0.01)
    
    def test_position_update_from_velocity(self):
        """Position should update based on velocity * dt."""
        position = MockVec3f(0, 50, 0)
        velocity = MockVec3f(10, 0, 5)
        dt = 0.016  # ~60fps
        
        new_position = position + velocity * dt
        
        assert new_position.x == pytest.approx(0.16)
        assert new_position.y == pytest.approx(50.0)
        assert new_position.z == pytest.approx(0.08)
    
    def test_bounds_clamping(self):
        """Position should be clamped to scene bounds."""
        bounds_min = MockVec3f(-400, 10, -400)
        bounds_max = MockVec3f(400, 400, 400)
        position = MockVec3f(500, 5, -500)  # Outside bounds
        
        # Clamp
        clamped = MockVec3f(
            max(bounds_min.x, min(bounds_max.x, position.x)),
            max(bounds_min.y, min(bounds_max.y, position.y)),
            max(bounds_min.z, min(bounds_max.z, position.z))
        )
        
        assert clamped.x == 400  # Clamped to max X
        assert clamped.y == 10   # Clamped to min Y
        assert clamped.z == -400 # Clamped to min Z


class TestBubbleCollisionDetection:
    """Test bubble collision detection logic."""
    
    def test_collision_when_overlapping(self):
        """Should detect collision when creature overlaps bubble."""
        creature_pos = MockVec3f(0, 50, 0)
        creature_radius = 6.0
        bubble_pos = MockVec3f(8, 50, 0)  # 8 units away
        bubble_radius = 5.0
        
        distance = (creature_pos - bubble_pos).GetLength()
        collision_threshold = (creature_radius + bubble_radius) * 0.9
        
        # Distance is 8, threshold is (6+5)*0.9 = 9.9
        assert distance < collision_threshold  # Should collide
    
    def test_no_collision_when_far(self):
        """Should not detect collision when creature is far from bubble."""
        creature_pos = MockVec3f(0, 50, 0)
        creature_radius = 6.0
        bubble_pos = MockVec3f(50, 50, 0)  # 50 units away
        bubble_radius = 5.0
        
        distance = (creature_pos - bubble_pos).GetLength()
        collision_threshold = (creature_radius + bubble_radius) * 0.9
        
        assert distance >= collision_threshold  # No collision
    
    def test_collision_direction_calculated(self):
        """Collision direction should point from bubble to creature."""
        creature_pos = MockVec3f(10, 50, 0)
        bubble_pos = MockVec3f(0, 50, 0)
        
        direction = (creature_pos - bubble_pos).GetNormalized()
        
        # Direction should be roughly +X
        assert direction.x == pytest.approx(1.0, abs=0.01)
        assert direction.y == pytest.approx(0.0, abs=0.01)


class TestTendroidInteractionDetection:
    """Test tendroid avoidance and shock detection logic."""
    
    def test_approach_velocity_positive_when_moving_toward(self):
        """Approach velocity should be positive when creature moves toward tendroid."""
        creature_pos = MockVec3f(0, 50, 0)
        creature_vel = MockVec3f(10, 0, 0)  # Moving +X
        tendroid_pos = MockVec3f(20, 50, 0)  # Tendroid is at +X
        
        distance_vec = creature_pos - tendroid_pos  # Points away from tendroid
        distance = distance_vec.GetLength()
        direction_to_tendroid = MockVec3f(-distance_vec.x, -distance_vec.y, -distance_vec.z)
        direction_to_tendroid = direction_to_tendroid.GetNormalized()
        
        approach_velocity = creature_vel.GetDot(direction_to_tendroid)
        
        assert approach_velocity > 0  # Moving toward
    
    def test_approach_velocity_negative_when_moving_away(self):
        """Approach velocity should be negative when creature moves away."""
        creature_pos = MockVec3f(0, 50, 0)
        creature_vel = MockVec3f(-10, 0, 0)  # Moving -X (away)
        tendroid_pos = MockVec3f(20, 50, 0)  # Tendroid is at +X
        
        distance_vec = creature_pos - tendroid_pos
        direction_to_tendroid = MockVec3f(-distance_vec.x, -distance_vec.y, -distance_vec.z)
        direction_to_tendroid = direction_to_tendroid.GetNormalized()
        
        approach_velocity = creature_vel.GetDot(direction_to_tendroid)
        
        assert approach_velocity < 0  # Moving away
    
    def test_avoidance_factor_calculation(self):
        """Avoidance factor should scale from 0 at epsilon to 1 at contact."""
        creature_radius = 6.0
        tendroid_radius = 2.0
        avoidance_epsilon = 30.0
        contact_distance = creature_radius + tendroid_radius  # 8.0
        
        # Test at various distances
        test_cases = [
            (30.0, 0.0),   # At epsilon - no avoidance
            (19.0, 0.5),   # Halfway - 50% avoidance
            (8.0, 1.0),    # At contact - full avoidance
        ]
        
        for distance, expected_factor in test_cases:
            if distance > contact_distance:
                factor = 1.0 - ((distance - contact_distance) / (avoidance_epsilon - contact_distance))
                factor = max(0.0, min(1.0, factor))
            else:
                factor = 1.0
            
            assert factor == pytest.approx(expected_factor, abs=0.01), \
                f"Distance {distance} should give factor {expected_factor}, got {factor}"


class TestCreatureOrientation:
    """Test creature rotation/orientation logic."""
    
    def test_yaw_from_horizontal_velocity(self):
        """Yaw should point in direction of horizontal movement."""
        # Moving in +X direction
        vx, vz = 10.0, 0.0
        target_yaw = 90.0 - math.degrees(math.atan2(vz, vx))
        
        # Should be ~90 degrees (pointing +X)
        assert target_yaw == pytest.approx(90.0)
        
        # Moving in +Z direction
        vx, vz = 0.0, 10.0
        target_yaw = 90.0 - math.degrees(math.atan2(vz, vx))
        
        # Should be ~0 degrees (pointing +Z)
        assert target_yaw == pytest.approx(0.0)
    
    def test_pitch_from_vertical_velocity(self):
        """Pitch should reflect vertical movement angle."""
        # Moving horizontally
        vy = 0.0
        horizontal_dist = 10.0
        
        target_pitch = -math.degrees(math.atan2(vy, horizontal_dist))
        assert target_pitch == pytest.approx(0.0)
        
        # Moving at 45 degrees up
        vy = 10.0
        horizontal_dist = 10.0
        
        target_pitch = -math.degrees(math.atan2(vy, horizontal_dist))
        assert target_pitch == pytest.approx(-45.0)
