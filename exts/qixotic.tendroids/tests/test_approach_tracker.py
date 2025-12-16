"""
Unit Tests for Approach Tracker Helpers

TEND-29: Track approach_minimum during creature movement.
TEND-116: Add unit tests for approach tracking.

Run with: python -m pytest tests/test_approach_tracker.py -v
"""


import unittest
import sys
from unittest.mock import MagicMock

# Mock warp and carb before imports
sys.modules['warp'] = MagicMock()
sys.modules['carb'] = MagicMock()

from qixotic.tendroids.contact.approach_tracker_helpers import (
    RecoveryPhase,
    TendroidSurfacePoint,
    ApproachTrackerStatus,
    calculate_distance_to_surface,
    calculate_signed_distance_to_surface,
    start_tracking,
    update_distance,
    check_threshold_crossed,
    complete_recovery,
    reset_tracker,
    update_surface_point,
    create_surface_point_from_contact,
    get_recovery_progress,
    is_tracking_active,
    is_recovery_complete,
    get_phase_name,
)


class TestTendroidSurfacePoint(unittest.TestCase):
    """Tests for TendroidSurfacePoint dataclass."""
    
    def test_default_values(self):
        """Test default surface point values."""
        surface = TendroidSurfacePoint()
        
        self.assertEqual(surface.current_position, (0.0, 0.0, 0.0))
        self.assertEqual(surface.rest_position, (0.0, 0.0, 0.0))
        self.assertEqual(surface.normal, (1.0, 0.0, 0.0))
    
    def test_custom_values(self):
        """Test surface point with custom values."""
        surface = TendroidSurfacePoint(
            current_x=1.0, current_y=2.0, current_z=3.0,
            rest_x=1.5, rest_y=2.0, rest_z=3.0,
            normal_x=0.0, normal_y=1.0, normal_z=0.0,
        )
        
        self.assertEqual(surface.current_position, (1.0, 2.0, 3.0))
        self.assertEqual(surface.rest_position, (1.5, 2.0, 3.0))
        self.assertEqual(surface.normal, (0.0, 1.0, 0.0))
    
    def test_deflection_amount_zero(self):
        """Test deflection when at rest position."""
        surface = TendroidSurfacePoint(
            current_x=1.0, current_y=2.0, current_z=3.0,
            rest_x=1.0, rest_y=2.0, rest_z=3.0,
        )
        
        self.assertAlmostEqual(surface.deflection_amount(), 0.0)
    
    def test_deflection_amount_nonzero(self):
        """Test deflection when pushed inward."""
        surface = TendroidSurfacePoint(
            current_x=0.0, current_y=0.0, current_z=0.0,
            rest_x=0.3, rest_y=0.4, rest_z=0.0,  # 0.5m away
        )
        
        self.assertAlmostEqual(surface.deflection_amount(), 0.5)


class TestDistanceCalculations(unittest.TestCase):
    """Tests for distance calculation functions."""
    
    def test_calculate_distance_to_surface_on_surface(self):
        """Test distance when creature is at surface."""
        surface = TendroidSurfacePoint(
            current_x=1.0, current_y=0.0, current_z=0.0,
        )
        creature_pos = (1.0, 0.0, 0.0)
        
        distance = calculate_distance_to_surface(creature_pos, surface)
        
        self.assertAlmostEqual(distance, 0.0)
    
    def test_calculate_distance_to_surface_away(self):
        """Test distance when creature is away from surface."""
        surface = TendroidSurfacePoint(
            current_x=0.0, current_y=0.0, current_z=0.0,
        )
        creature_pos = (0.3, 0.4, 0.0)  # 0.5m away
        
        distance = calculate_distance_to_surface(creature_pos, surface)
        
        self.assertAlmostEqual(distance, 0.5)
    
    def test_calculate_signed_distance_positive(self):
        """Test signed distance when outside (positive)."""
        surface = TendroidSurfacePoint(
            current_x=0.0, current_y=0.0, current_z=0.0,
            normal_x=1.0, normal_y=0.0, normal_z=0.0,
        )
        creature_pos = (0.5, 0.0, 0.0)  # In normal direction
        
        signed_dist = calculate_signed_distance_to_surface(creature_pos, surface)
        
        self.assertAlmostEqual(signed_dist, 0.5)
    
    def test_calculate_signed_distance_negative(self):
        """Test signed distance when inside (negative)."""
        surface = TendroidSurfacePoint(
            current_x=0.0, current_y=0.0, current_z=0.0,
            normal_x=1.0, normal_y=0.0, normal_z=0.0,
        )
        creature_pos = (-0.3, 0.0, 0.0)  # Opposite to normal
        
        signed_dist = calculate_signed_distance_to_surface(creature_pos, surface)
        
        self.assertAlmostEqual(signed_dist, -0.3)


class TestTrackerLifecycle(unittest.TestCase):
    """Tests for tracker state lifecycle."""
    
    def test_initial_status(self):
        """Test default status is inactive."""
        status = ApproachTrackerStatus()
        
        self.assertEqual(status.phase, RecoveryPhase.INACTIVE)
        self.assertEqual(status.current_distance, float('inf'))
        self.assertEqual(status.update_count, 0)
        self.assertFalse(is_tracking_active(status))
    
    def test_start_tracking(self):
        """Test starting tracking on contact."""
        status = ApproachTrackerStatus()
        
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        
        self.assertEqual(status.phase, RecoveryPhase.TRACKING)
        self.assertEqual(status.current_distance, 0.02)
        self.assertEqual(status.threshold_distance, 0.15)
        self.assertEqual(status.min_distance_recorded, 0.02)
        self.assertEqual(status.update_count, 1)
        self.assertTrue(is_tracking_active(status))
    
    def test_update_distance_increases(self):
        """Test distance update as creature moves away."""
        status = ApproachTrackerStatus()
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        
        surface = TendroidSurfacePoint()
        creature_pos = (0.10, 0.0, 0.0)  # 10cm away
        
        status = update_distance(status, creature_pos, surface)
        
        self.assertAlmostEqual(status.current_distance, 0.10)
        self.assertEqual(status.min_distance_recorded, 0.02)  # Preserved
        self.assertAlmostEqual(status.max_distance_recorded, 0.10)
        self.assertEqual(status.update_count, 2)
    
    def test_threshold_crossing_detection(self):
        """Test detection when threshold is crossed."""
        status = ApproachTrackerStatus()
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        
        surface = TendroidSurfacePoint()
        creature_pos = (0.20, 0.0, 0.0)  # 20cm away, past threshold
        
        status = update_distance(status, creature_pos, surface)
        
        self.assertEqual(status.phase, RecoveryPhase.THRESHOLD_CROSSED)
        self.assertTrue(check_threshold_crossed(status))
        self.assertTrue(is_recovery_complete(status))
    
    def test_complete_recovery(self):
        """Test marking recovery as complete."""
        status = ApproachTrackerStatus()
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        
        surface = TendroidSurfacePoint()
        creature_pos = (0.20, 0.0, 0.0)
        status = update_distance(status, creature_pos, surface)
        status = complete_recovery(status)
        
        self.assertEqual(status.phase, RecoveryPhase.COMPLETE)
        self.assertEqual(status.recovery_count, 1)
    
    def test_reset_tracker(self):
        """Test resetting tracker for next contact."""
        status = ApproachTrackerStatus()
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        status = complete_recovery(status)
        status = reset_tracker(status)
        
        self.assertEqual(status.phase, RecoveryPhase.INACTIVE)
        self.assertEqual(status.current_distance, float('inf'))
        self.assertEqual(status.recovery_count, 1)  # Preserved
        self.assertFalse(is_tracking_active(status))


class TestMovingSurface(unittest.TestCase):
    """Tests for handling moving tendroid surface."""
    
    def test_update_surface_point(self):
        """Test updating surface position as tendroid returns."""
        surface = TendroidSurfacePoint(
            current_x=0.0, current_y=0.0, current_z=0.0,
            rest_x=0.1, rest_y=0.0, rest_z=0.0,
        )
        
        # Surface moves halfway back
        surface = update_surface_point(surface, new_current=(0.05, 0.0, 0.0))
        
        self.assertEqual(surface.current_position, (0.05, 0.0, 0.0))
        self.assertEqual(surface.rest_position, (0.1, 0.0, 0.0))  # Unchanged
    
    def test_create_surface_point_from_contact(self):
        """Test creating surface point from contact event."""
        contact_point = (1.0, 0.5, 0.0)
        surface_normal = (1.0, 0.0, 0.0)
        rest_offset = 0.05  # Surface was pushed 5cm inward
        
        surface = create_surface_point_from_contact(
            contact_point, surface_normal, rest_offset
        )
        
        self.assertEqual(surface.current_position, (1.0, 0.5, 0.0))
        self.assertEqual(surface.rest_position, (1.05, 0.5, 0.0))
        self.assertEqual(surface.normal, (1.0, 0.0, 0.0))
    
    def test_distance_accounts_for_moving_surface(self):
        """Test that distance calculation uses current, not rest position."""
        # Surface deflected inward by 5cm
        surface = TendroidSurfacePoint(
            current_x=0.95, current_y=0.0, current_z=0.0,
            rest_x=1.0, rest_y=0.0, rest_z=0.0,
        )
        creature_pos = (1.10, 0.0, 0.0)
        
        distance = calculate_distance_to_surface(creature_pos, surface)
        
        # Distance to current position (1.10 - 0.95 = 0.15)
        self.assertAlmostEqual(distance, 0.15)
        # Not distance to rest position (1.10 - 1.0 = 0.10)


class TestRecoveryProgress(unittest.TestCase):
    """Tests for recovery progress calculation."""
    
    def test_progress_at_start(self):
        """Test progress is 0 at start of tracking."""
        status = ApproachTrackerStatus()
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        
        progress = get_recovery_progress(status)
        
        self.assertAlmostEqual(progress, 0.0, places=2)
    
    def test_progress_midway(self):
        """Test progress at midpoint."""
        status = ApproachTrackerStatus()
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        
        surface = TendroidSurfacePoint()
        # Midpoint: 0.02 + (0.15 - 0.02) / 2 = 0.085
        creature_pos = (0.085, 0.0, 0.0)
        status = update_distance(status, creature_pos, surface)
        
        progress = get_recovery_progress(status)
        
        self.assertAlmostEqual(progress, 0.5, places=1)
    
    def test_progress_at_threshold(self):
        """Test progress is 1.0 at threshold."""
        status = ApproachTrackerStatus()
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        
        surface = TendroidSurfacePoint()
        creature_pos = (0.16, 0.0, 0.0)  # Past threshold
        status = update_distance(status, creature_pos, surface)
        
        progress = get_recovery_progress(status)
        
        self.assertAlmostEqual(progress, 1.0)
    
    def test_progress_inactive(self):
        """Test progress is 0 when inactive."""
        status = ApproachTrackerStatus()
        
        progress = get_recovery_progress(status)
        
        self.assertEqual(progress, 0.0)


class TestUtilityFunctions(unittest.TestCase):
    """Tests for utility functions."""
    
    def test_is_tracking_active_false(self):
        """Test tracking active check when inactive."""
        status = ApproachTrackerStatus()
        
        self.assertFalse(is_tracking_active(status))
    
    def test_is_tracking_active_true(self):
        """Test tracking active check when tracking."""
        status = start_tracking(
            ApproachTrackerStatus(),
            threshold=0.15,
            initial_distance=0.02
        )
        
        self.assertTrue(is_tracking_active(status))
    
    def test_is_recovery_complete_false(self):
        """Test recovery complete check during tracking."""
        status = start_tracking(
            ApproachTrackerStatus(),
            threshold=0.15,
            initial_distance=0.02
        )
        
        self.assertFalse(is_recovery_complete(status))
    
    def test_is_recovery_complete_threshold_crossed(self):
        """Test recovery complete when threshold crossed."""
        status = ApproachTrackerStatus(
            phase=RecoveryPhase.THRESHOLD_CROSSED
        )
        
        self.assertTrue(is_recovery_complete(status))
    
    def test_get_phase_name(self):
        """Test getting human-readable phase name."""
        status = ApproachTrackerStatus(phase=RecoveryPhase.TRACKING)
        
        self.assertEqual(get_phase_name(status), "TRACKING")


class TestEdgeCases(unittest.TestCase):
    """Tests for edge cases and boundary conditions."""
    
    def test_update_when_inactive_no_change(self):
        """Test that update does nothing when inactive."""
        status = ApproachTrackerStatus()
        surface = TendroidSurfacePoint()
        creature_pos = (0.10, 0.0, 0.0)
        
        updated = update_distance(status, creature_pos, surface)
        
        self.assertEqual(updated.phase, RecoveryPhase.INACTIVE)
        self.assertEqual(updated.update_count, 0)
    
    def test_threshold_exactly_at_minimum(self):
        """Test when creature is exactly at threshold."""
        status = start_tracking(
            ApproachTrackerStatus(),
            threshold=0.15,
            initial_distance=0.02
        )
        
        surface = TendroidSurfacePoint()
        creature_pos = (0.15, 0.0, 0.0)  # Exactly at threshold
        
        status = update_distance(status, creature_pos, surface)
        
        # Should still be tracking (need to exceed, not equal)
        self.assertEqual(status.phase, RecoveryPhase.TRACKING)
    
    def test_creature_moves_closer_then_away(self):
        """Test tracking when creature briefly moves closer."""
        status = start_tracking(
            ApproachTrackerStatus(),
            threshold=0.15,
            initial_distance=0.05
        )
        
        surface = TendroidSurfacePoint()
        
        # Move closer
        status = update_distance(status, (0.03, 0.0, 0.0), surface)
        self.assertEqual(status.min_distance_recorded, 0.03)
        
        # Move away
        status = update_distance(status, (0.08, 0.0, 0.0), surface)
        self.assertEqual(status.min_distance_recorded, 0.03)  # Min preserved
        
        # Cross threshold
        status = update_distance(status, (0.20, 0.0, 0.0), surface)
        self.assertEqual(status.phase, RecoveryPhase.THRESHOLD_CROSSED)
    
    def test_multiple_recovery_sessions(self):
        """Test multiple contact/recovery cycles."""
        status = ApproachTrackerStatus()
        surface = TendroidSurfacePoint()
        
        # First contact
        status = start_tracking(status, threshold=0.15, initial_distance=0.02)
        status = update_distance(status, (0.20, 0.0, 0.0), surface)
        status = complete_recovery(status)
        self.assertEqual(status.recovery_count, 1)
        
        # Reset
        status = reset_tracker(status)
        
        # Second contact
        status = start_tracking(status, threshold=0.15, initial_distance=0.03)
        status = update_distance(status, (0.18, 0.0, 0.0), surface)
        status = complete_recovery(status)
        self.assertEqual(status.recovery_count, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
