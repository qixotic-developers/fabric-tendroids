"""
Tests for Velocity Fade Helpers

Tests the velocity fade system for smooth deceleration after repulsion.

TEND-31: Implement repel velocity fade.
TEND-125: Add unit tests for velocity fade.
"""

import math
import pytest
import sys
from unittest.mock import MagicMock

# Mock warp and carb before imports
sys.modules['warp'] = MagicMock()
sys.modules['carb'] = MagicMock()

from qixotic.tendroids.contact.velocity_fade_helpers import (
    FadeMode,
    VelocityFadeConfig,
    VelocityFadeStatus,
    create_fade_status,
    apply_initial_velocity,
    velocity_from_force,
    update_velocity,
    get_displacement,
    get_fade_progress,
    reset_velocity,
    is_velocity_active,
    is_velocity_stopped,
    get_current_speed,
    get_velocity_direction,
)


class TestCreateFadeStatus:
    """Tests for creating velocity fade status."""
    
    def test_initial_status_is_stopped(self):
        """New status starts stopped."""
        status = create_fade_status()
        assert status.is_stopped
        assert not status.is_active
    
    def test_initial_velocity_is_zero(self):
        """New status has zero velocity."""
        status = create_fade_status()
        assert status.velocity == (0.0, 0.0, 0.0)
        assert status.speed == 0.0


class TestApplyInitialVelocity:
    """Tests for applying initial repulsion velocity."""
    
    def test_apply_velocity_activates(self):
        """Applying velocity activates fade."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        assert status.is_active
        assert not status.is_stopped
    
    def test_velocity_stored_correctly(self):
        """Applied velocity is stored."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 2.0, 3.0))
        
        assert status.velocity == (1.0, 2.0, 3.0)
        assert status.initial_velocity == (1.0, 2.0, 3.0)
    
    def test_zero_velocity_stays_stopped(self):
        """Zero velocity keeps status stopped."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (0.0, 0.0, 0.0))
        
        assert status.is_stopped
        assert not status.is_active
    
    def test_tracking_resets_on_apply(self):
        """Tracking values reset when applying new velocity."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        assert status.elapsed_time == 0.0
        assert status.distance_traveled == 0.0


class TestVelocityFromForce:
    """Tests for converting force to velocity."""
    
    def test_unit_force_unit_mass(self):
        """Unit force with unit mass gives expected velocity."""
        velocity = velocity_from_force((100.0, 0.0, 0.0), mass=1.0, delta_time=0.01)
        
        # v = F * dt / m = 100 * 0.01 / 1 = 1.0
        assert abs(velocity[0] - 1.0) < 0.001
        assert velocity[1] == 0.0
        assert velocity[2] == 0.0
    
    def test_higher_mass_lower_velocity(self):
        """Higher mass results in lower velocity."""
        v1 = velocity_from_force((100.0, 0.0, 0.0), mass=1.0, delta_time=0.01)
        v2 = velocity_from_force((100.0, 0.0, 0.0), mass=2.0, delta_time=0.01)
        
        assert v2[0] < v1[0]
        assert abs(v2[0] - v1[0] / 2) < 0.001


class TestUpdateVelocity:
    """Tests for velocity decay updates."""
    
    def test_velocity_decreases_over_time(self):
        """Velocity decreases with updates."""
        config = VelocityFadeConfig(fade_duration=1.0, decay_rate=3.0)
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        initial_speed = status.speed
        status = update_velocity(status, delta_time=0.1, config=config)
        
        assert status.speed < initial_speed
    
    def test_velocity_approaches_zero(self):
        """Velocity approaches zero over multiple updates."""
        config = VelocityFadeConfig(
            fade_duration=0.5,
            decay_rate=5.0,
            velocity_epsilon=0.001,
        )
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        # Run many updates
        for _ in range(100):
            status = update_velocity(status, delta_time=0.016, config=config)
        
        assert status.is_stopped
        assert status.speed < config.velocity_epsilon
    
    def test_elapsed_time_accumulates(self):
        """Elapsed time tracks correctly."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        status = update_velocity(status, delta_time=0.1)
        assert abs(status.elapsed_time - 0.1) < 0.001
        
        status = update_velocity(status, delta_time=0.1)
        assert abs(status.elapsed_time - 0.2) < 0.001
    
    def test_distance_accumulates(self):
        """Distance traveled accumulates."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        status = update_velocity(status, delta_time=0.1)
        assert status.distance_traveled > 0
    
    def test_stopped_status_unchanged(self):
        """Already stopped status stays stopped."""
        status = create_fade_status()
        # Don't apply velocity - stays stopped
        
        status = update_velocity(status, delta_time=0.1)
        
        assert status.is_stopped
        assert status.speed == 0.0


class TestFadeModes:
    """Tests for different fade modes."""
    
    def test_time_based_fade(self):
        """Time-based fade decays over duration."""
        config = VelocityFadeConfig(
            fade_mode=FadeMode.TIME_BASED,
            fade_duration=1.0,
            decay_rate=3.0,
        )
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        # Update for half the duration
        for _ in range(31):  # ~0.5s at 60fps
            status = update_velocity(status, delta_time=0.016, config=config)
        
        # Should be significantly reduced but not stopped
        assert 0.1 < status.speed < 0.9
    
    def test_distance_based_fade(self):
        """Distance-based fade decays over distance."""
        config = VelocityFadeConfig(
            fade_mode=FadeMode.DISTANCE_BASED,
            fade_distance=0.5,
            decay_rate=3.0,
        )
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        # Update until traveled some distance
        for _ in range(20):
            status = update_velocity(status, delta_time=0.016, config=config)
        
        assert status.distance_traveled > 0
        assert status.speed < 1.0
    
    def test_hybrid_uses_faster_decay(self):
        """Hybrid mode uses whichever decays faster."""
        config = VelocityFadeConfig(
            fade_mode=FadeMode.HYBRID,
            fade_duration=1.0,
            fade_distance=0.1,  # Very short distance
            decay_rate=3.0,
        )
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        # Short distance should cause fast decay
        for _ in range(10):
            status = update_velocity(status, delta_time=0.016, config=config)
        
        # Should decay faster than time-only mode
        assert status.speed < 0.5


class TestGetDisplacement:
    """Tests for position displacement calculation."""
    
    def test_displacement_proportional_to_velocity(self):
        """Displacement scales with velocity."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (2.0, 0.0, 0.0))
        
        dx, dy, dz = get_displacement(status, delta_time=0.1)
        
        assert abs(dx - 0.2) < 0.001  # 2.0 * 0.1 = 0.2
        assert dy == 0.0
        assert dz == 0.0
    
    def test_displacement_proportional_to_time(self):
        """Displacement scales with time step."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        d1 = get_displacement(status, delta_time=0.1)
        d2 = get_displacement(status, delta_time=0.2)
        
        assert abs(d2[0] - d1[0] * 2) < 0.001


class TestGetFadeProgress:
    """Tests for fade progress calculation."""
    
    def test_progress_starts_at_zero(self):
        """Fresh fade starts at 0 progress."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        progress = get_fade_progress(status)
        assert progress == 0.0
    
    def test_progress_increases_with_decay(self):
        """Progress increases as velocity decays."""
        config = VelocityFadeConfig(fade_duration=2.0, decay_rate=2.0)
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        # Use smaller time step to avoid reaching stopped state
        status = update_velocity(status, delta_time=0.1, config=config)
        progress = get_fade_progress(status, config)
        
        assert 0.0 < progress < 1.0
    
    def test_progress_reaches_one_when_stopped(self):
        """Progress is 1.0 when stopped."""
        config = VelocityFadeConfig(
            fade_duration=0.1,
            decay_rate=10.0,
            velocity_epsilon=0.01,
        )
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        
        # Run until stopped
        for _ in range(100):
            status = update_velocity(status, delta_time=0.016, config=config)
        
        progress = get_fade_progress(status, config)
        assert progress == 1.0


class TestResetVelocity:
    """Tests for velocity reset."""
    
    def test_reset_clears_velocity(self):
        """Reset clears all velocity."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 2.0, 3.0))
        status = reset_velocity(status)
        
        assert status.velocity == (0.0, 0.0, 0.0)
        assert status.initial_velocity == (0.0, 0.0, 0.0)
    
    def test_reset_clears_tracking(self):
        """Reset clears tracking values."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        status = update_velocity(status, delta_time=0.1)
        status = reset_velocity(status)
        
        assert status.elapsed_time == 0.0
        assert status.distance_traveled == 0.0
    
    def test_reset_sets_stopped(self):
        """Reset sets stopped state."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        status = reset_velocity(status)
        
        assert status.is_stopped
        assert not status.is_active


class TestQueryFunctions:
    """Tests for query helper functions."""
    
    def test_is_velocity_active(self):
        """Active check is accurate."""
        status = create_fade_status()
        assert not is_velocity_active(status)
        
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        assert is_velocity_active(status)
    
    def test_is_velocity_stopped(self):
        """Stopped check is accurate."""
        status = create_fade_status()
        assert is_velocity_stopped(status)
        
        status = apply_initial_velocity(status, (1.0, 0.0, 0.0))
        assert not is_velocity_stopped(status)
    
    def test_get_current_speed(self):
        """Speed calculation is correct."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (3.0, 4.0, 0.0))
        
        speed = get_current_speed(status)
        assert abs(speed - 5.0) < 0.001  # 3-4-5 triangle
    
    def test_get_velocity_direction(self):
        """Direction is normalized."""
        status = create_fade_status()
        status = apply_initial_velocity(status, (3.0, 4.0, 0.0))
        
        direction = get_velocity_direction(status)
        
        assert direction is not None
        assert abs(direction[0] - 0.6) < 0.001
        assert abs(direction[1] - 0.8) < 0.001
        assert direction[2] == 0.0
    
    def test_get_velocity_direction_zero(self):
        """Zero velocity returns None direction."""
        status = create_fade_status()
        direction = get_velocity_direction(status)
        
        assert direction is None


class TestDragCoefficient:
    """Tests for optional drag coefficient."""
    
    def test_drag_accelerates_decay(self):
        """Drag coefficient causes faster decay."""
        config_no_drag = VelocityFadeConfig(drag_coefficient=0.0, fade_duration=2.0)
        config_with_drag = VelocityFadeConfig(drag_coefficient=2.0, fade_duration=2.0)
        
        status1 = create_fade_status()
        status1 = apply_initial_velocity(status1, (1.0, 0.0, 0.0))
        
        status2 = create_fade_status()
        status2 = apply_initial_velocity(status2, (1.0, 0.0, 0.0))
        
        # Update both
        for _ in range(10):
            status1 = update_velocity(status1, delta_time=0.016, config=config_no_drag)
            status2 = update_velocity(status2, delta_time=0.016, config=config_with_drag)
        
        # Drag should cause faster decay
        assert status2.speed < status1.speed


class TestVelocityFadeStatus:
    """Tests for VelocityFadeStatus dataclass properties."""
    
    def test_speed_property(self):
        """Speed property calculates magnitude."""
        status = VelocityFadeStatus(
            velocity_x=3.0,
            velocity_y=4.0,
            velocity_z=0.0,
        )
        assert abs(status.speed - 5.0) < 0.001
    
    def test_initial_speed_property(self):
        """Initial speed property calculates magnitude."""
        status = VelocityFadeStatus(
            initial_velocity_x=6.0,
            initial_velocity_y=8.0,
            initial_velocity_z=0.0,
        )
        assert abs(status.initial_speed - 10.0) < 0.001
