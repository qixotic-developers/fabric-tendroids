"""
Tests for Recovery Integration Helpers

Tests the integration between approach tracker and proximity detection system.

TEND-30: Recalculate absolute coordinates as tendroid returns.
TEND-120: Integrate with proximity detection system.
TEND-121: Add unit tests for coordinate calculations.
"""

import sys
from unittest.mock import MagicMock

# Mock warp and carb before imports to avoid extension dependencies
sys.modules['warp'] = MagicMock()
sys.modules['carb'] = MagicMock()

from qixotic.tendroids.recovery.recovery_integration_helpers import (
    RecoveryContext,
    create_recovery_context,
    start_recovery_tracking,
    update_recovery,
    finalize_recovery,
    reset_recovery_context,
    is_recovery_in_progress,
    is_threshold_crossed,
    get_recovery_progress,
    get_current_distance,
    get_surface_deflection,
    map_recovery_phase_to_proximity,
    map_proximity_to_recovery_phase,
)
from qixotic.tendroids.contact.approach_tracker_helpers import RecoveryPhase
from qixotic.tendroids.proximity.proximity_state import ProximityState
from qixotic.tendroids.proximity.proximity_config import ApproachParameters


class TestCreateRecoveryContext:
    """Tests for creating recovery context."""
    
    def test_default_context(self):
        """Default context has expected initial values."""
        context = create_recovery_context()
        
        assert context.tracker_status.phase == RecoveryPhase.INACTIVE
        assert context.proximity_state == ProximityState.IDLE
        assert context.previous_distance is None
    
    def test_custom_params(self):
        """Context uses provided parameters."""
        params = ApproachParameters(
            approach_epsilon=0.02,
            approach_minimum=0.10,
            warning_distance=0.20,
            detection_radius=0.50,
        )
        context = create_recovery_context(params)
        
        assert context.params.approach_minimum == 0.10
        assert context.tracker_status.threshold_distance == 0.10


class TestStartRecoveryTracking:
    """Tests for starting recovery after contact."""
    
    def test_start_tracking_sets_phase(self):
        """Starting tracking activates the tracker."""
        context = create_recovery_context()
        
        contact_point = (0.0, 0.0, 0.0)
        normal = (1.0, 0.0, 0.0)
        creature_pos = (0.05, 0.0, 0.0)
        
        updated = start_recovery_tracking(
            context, contact_point, normal, creature_pos
        )
        
        assert updated.tracker_status.phase == RecoveryPhase.TRACKING
    
    def test_start_tracking_records_initial_distance(self):
        """Initial distance is recorded correctly."""
        context = create_recovery_context()
        
        contact_point = (0.0, 0.0, 0.0)
        normal = (1.0, 0.0, 0.0)
        creature_pos = (0.05, 0.0, 0.0)  # 5cm away
        
        updated = start_recovery_tracking(
            context, contact_point, normal, creature_pos
        )
        
        assert abs(updated.tracker_status.current_distance - 0.05) < 0.001
    
    def test_start_tracking_with_deflection(self):
        """Deflection affects rest position calculation."""
        context = create_recovery_context()
        
        contact_point = (0.0, 0.0, 0.0)
        normal = (1.0, 0.0, 0.0)
        creature_pos = (0.05, 0.0, 0.0)
        deflection = 0.02  # 2cm deflection
        
        updated = start_recovery_tracking(
            context, contact_point, normal, creature_pos, deflection
        )
        
        # Rest position should be 2cm in normal direction from contact
        assert abs(updated.surface_point.rest_x - 0.02) < 0.001
        assert updated.surface_point.rest_y == 0.0
        assert updated.surface_point.rest_z == 0.0
    
    def test_proximity_state_becomes_retreating(self):
        """After contact, creature should be retreating."""
        context = create_recovery_context()
        
        contact_point = (0.0, 0.0, 0.0)
        normal = (1.0, 0.0, 0.0)
        creature_pos = (0.05, 0.0, 0.0)
        
        updated = start_recovery_tracking(
            context, contact_point, normal, creature_pos
        )
        
        # Should be retreating or still in contact zone depending on epsilon
        assert updated.proximity_state in (
            ProximityState.RETREATING,
            ProximityState.CONTACT,
        )


class TestUpdateRecovery:
    """Tests for updating recovery each frame."""
    
    def test_update_tracks_creature_movement(self):
        """Update follows creature position changes."""
        context = create_recovery_context()
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.05, 0.0, 0.0),
        )
        
        # Move creature further away
        updated = update_recovery(
            context,
            creature_pos=(0.10, 0.0, 0.0),  # Now 10cm away
            new_surface_pos=(0.0, 0.0, 0.0),
        )
        
        assert abs(updated.tracker_status.current_distance - 0.10) < 0.001
    
    def test_update_tracks_surface_movement(self):
        """Update accounts for tendroid surface returning."""
        context = create_recovery_context()
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.10, 0.0, 0.0),
            deflection_amount=0.02,
        )
        
        # Surface moves toward rest position (from 0 to 0.01, half way)
        updated = update_recovery(
            context,
            creature_pos=(0.10, 0.0, 0.0),  # Creature stationary
            new_surface_pos=(0.01, 0.0, 0.0),  # Surface returning
        )
        
        # Distance should be 10cm - 1cm = 9cm
        assert abs(updated.tracker_status.current_distance - 0.09) < 0.001
    
    def test_threshold_crossing_detected(self):
        """Crossing threshold changes phase."""
        params = ApproachParameters(
            approach_epsilon=0.02,
            approach_minimum=0.08,  # 8cm threshold
            warning_distance=0.20,
            detection_radius=0.50,
        )
        context = create_recovery_context(params)
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.03, 0.0, 0.0),  # Start at 3cm
        )
        
        # Move creature past threshold
        updated = update_recovery(
            context,
            creature_pos=(0.10, 0.0, 0.0),  # Now 10cm away (past 8cm)
            new_surface_pos=(0.0, 0.0, 0.0),
        )
        
        assert updated.tracker_status.phase == RecoveryPhase.THRESHOLD_CROSSED
        assert is_threshold_crossed(updated)


class TestFinalizeRecovery:
    """Tests for completing recovery."""
    
    def test_finalize_sets_complete(self):
        """Finalizing sets phase to COMPLETE."""
        context = create_recovery_context()
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.20, 0.0, 0.0),
        )
        
        finalized = finalize_recovery(context)
        
        assert finalized.tracker_status.phase == RecoveryPhase.COMPLETE
        assert finalized.proximity_state == ProximityState.RECOVERED
    
    def test_finalize_increments_recovery_count(self):
        """Each recovery increments count."""
        context = create_recovery_context()
        assert context.tracker_status.recovery_count == 0
        
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.20, 0.0, 0.0),
        )
        
        finalized = finalize_recovery(context)
        
        assert finalized.tracker_status.recovery_count == 1


class TestResetRecoveryContext:
    """Tests for resetting context."""
    
    def test_reset_preserves_recovery_count(self):
        """Reset keeps recovery count for statistics."""
        context = create_recovery_context()
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.20, 0.0, 0.0),
        )
        finalized = finalize_recovery(context)
        
        reset = reset_recovery_context(finalized)
        
        assert reset.tracker_status.recovery_count == 1
        assert reset.tracker_status.phase == RecoveryPhase.INACTIVE


class TestQueryFunctions:
    """Tests for query helper functions."""
    
    def test_is_recovery_in_progress(self):
        """Query accurately reports tracking state."""
        context = create_recovery_context()
        assert not is_recovery_in_progress(context)
        
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.05, 0.0, 0.0),
        )
        assert is_recovery_in_progress(context)
    
    def test_get_recovery_progress(self):
        """Progress calculation returns valid range."""
        params = ApproachParameters(
            approach_epsilon=0.02,
            approach_minimum=0.10,
            warning_distance=0.20,
            detection_radius=0.50,
        )
        context = create_recovery_context(params)
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.03, 0.0, 0.0),  # Start near contact
        )
        
        progress = get_recovery_progress(context)
        assert 0.0 <= progress <= 1.0
    
    def test_get_current_distance(self):
        """Distance query returns tracked distance."""
        context = create_recovery_context()
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.08, 0.0, 0.0),
        )
        
        distance = get_current_distance(context)
        assert abs(distance - 0.08) < 0.001
    
    def test_get_surface_deflection(self):
        """Deflection query returns remaining deflection."""
        context = create_recovery_context()
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.05, 0.0, 0.0),
            deflection_amount=0.02,
        )
        
        # Current position is at contact (0,0,0), rest is at (0.02,0,0)
        deflection = get_surface_deflection(context)
        assert abs(deflection - 0.02) < 0.001


class TestPhaseMappings:
    """Tests for phase/state mapping functions."""
    
    def test_recovery_phase_to_proximity(self):
        """Recovery phases map to appropriate proximity states."""
        assert map_recovery_phase_to_proximity(RecoveryPhase.INACTIVE) == ProximityState.IDLE
        assert map_recovery_phase_to_proximity(RecoveryPhase.TRACKING) == ProximityState.RETREATING
        assert map_recovery_phase_to_proximity(RecoveryPhase.THRESHOLD_CROSSED) == ProximityState.RECOVERED
        assert map_recovery_phase_to_proximity(RecoveryPhase.COMPLETE) == ProximityState.RECOVERED
    
    def test_proximity_to_recovery_phase(self):
        """Proximity states map to appropriate recovery phases."""
        assert map_proximity_to_recovery_phase(ProximityState.IDLE) == RecoveryPhase.INACTIVE
        assert map_proximity_to_recovery_phase(ProximityState.APPROACHING) == RecoveryPhase.INACTIVE
        assert map_proximity_to_recovery_phase(ProximityState.CONTACT) == RecoveryPhase.TRACKING
        assert map_proximity_to_recovery_phase(ProximityState.RETREATING) == RecoveryPhase.TRACKING
        assert map_proximity_to_recovery_phase(ProximityState.RECOVERED) == RecoveryPhase.COMPLETE


class TestFullRecoveryCycle:
    """Integration tests for complete recovery cycle."""
    
    def test_full_cycle(self):
        """Complete recovery cycle from contact to recovered."""
        params = ApproachParameters(
            approach_epsilon=0.02,  # 2cm
            approach_minimum=0.08,  # 8cm
            warning_distance=0.20,
            detection_radius=0.50,
        )
        
        # 1. Create context
        context = create_recovery_context(params)
        assert context.proximity_state == ProximityState.IDLE
        
        # 2. Contact occurs at origin, creature is just past epsilon
        context = start_recovery_tracking(
            context,
            contact_point=(0.0, 0.0, 0.0),
            surface_normal=(1.0, 0.0, 0.0),
            creature_pos=(0.03, 0.0, 0.0),  # 3cm away
            deflection_amount=0.01,  # 1cm deflection
        )
        assert is_recovery_in_progress(context)
        
        # 3. Creature retreats, surface returns - several updates
        # Note: distance = creature_x - surface_x
        # Threshold is 8cm, so need distance > 8cm
        positions = [
            ((0.04, 0.0, 0.0), (0.002, 0.0, 0.0)),  # 4cm - 0.2cm = 3.8cm distance
            ((0.05, 0.0, 0.0), (0.004, 0.0, 0.0)),  # 5cm - 0.4cm = 4.6cm
            ((0.06, 0.0, 0.0), (0.006, 0.0, 0.0)),  # 6cm - 0.6cm = 5.4cm
            ((0.07, 0.0, 0.0), (0.008, 0.0, 0.0)),  # 7cm - 0.8cm = 6.2cm
            ((0.10, 0.0, 0.0), (0.01, 0.0, 0.0)),   # 10cm - 1cm = 9cm > 8cm threshold!
        ]
        
        for creature_pos, surface_pos in positions:
            context = update_recovery(context, creature_pos, surface_pos)
        
        # 4. Should have crossed threshold
        assert is_threshold_crossed(context)
        assert context.tracker_status.phase == RecoveryPhase.THRESHOLD_CROSSED
        
        # 5. Finalize recovery
        context = finalize_recovery(context)
        assert context.tracker_status.phase == RecoveryPhase.COMPLETE
        assert context.proximity_state == ProximityState.RECOVERED
        
        # 6. Reset for next cycle
        context = reset_recovery_context(context)
        assert context.tracker_status.phase == RecoveryPhase.INACTIVE
        assert context.tracker_status.recovery_count == 1
