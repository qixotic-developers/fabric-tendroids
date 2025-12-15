"""
Velocity Fade Helpers - Smooth deceleration after repulsion

Manages the gradual decay of repulsion velocity, bringing the creature
to a natural stop. Supports both time-based and distance-based decay.

Implements TEND-31: Implement repel velocity fade.
Implements TEND-122: Create velocity_fade_controller.py module.
Implements TEND-123: Implement initial velocity application.
Implements TEND-124: Implement velocity fade over time/distance.
"""

import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple


class FadeMode(Enum):
    """How velocity should decay."""
    TIME_BASED = auto()      # Decay over fixed time duration
    DISTANCE_BASED = auto()  # Decay over travel distance
    HYBRID = auto()          # Combination of both (whichever completes first)


@dataclass
class VelocityFadeConfig:
    """Configuration for velocity fade behavior."""
    
    # Decay timing
    fade_duration: float = 1.0  # Seconds to fade to zero (time-based)
    fade_distance: float = 0.2  # Meters to travel before stopping (distance-based)
    
    # Decay curve
    decay_rate: float = 3.0  # Exponential decay rate (higher = faster initial decay)
    
    # Stopping thresholds
    velocity_epsilon: float = 0.001  # Velocity below this is considered stopped
    
    # Mode selection
    fade_mode: FadeMode = FadeMode.HYBRID
    
    # Optional drag (simulates resistance)
    drag_coefficient: float = 0.0  # Additional linear drag (0 = no drag)


@dataclass
class VelocityFadeStatus:
    """Current state of velocity fade."""
    
    # Current velocity components
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0
    
    # Initial velocity (for calculating fade progress)
    initial_velocity_x: float = 0.0
    initial_velocity_y: float = 0.0
    initial_velocity_z: float = 0.0
    
    # Tracking
    elapsed_time: float = 0.0      # Time since fade started
    distance_traveled: float = 0.0  # Total distance traveled
    
    # State
    is_active: bool = False  # Whether fade is in progress
    is_stopped: bool = True  # Whether velocity has reached zero
    
    @property
    def velocity(self) -> Tuple[float, float, float]:
        """Current velocity as tuple."""
        return (self.velocity_x, self.velocity_y, self.velocity_z)
    
    @property
    def initial_velocity(self) -> Tuple[float, float, float]:
        """Initial velocity as tuple."""
        return (self.initial_velocity_x, self.initial_velocity_y, self.initial_velocity_z)
    
    @property
    def speed(self) -> float:
        """Current speed magnitude."""
        return math.sqrt(
            self.velocity_x ** 2 +
            self.velocity_y ** 2 +
            self.velocity_z ** 2
        )
    
    @property
    def initial_speed(self) -> float:
        """Initial speed magnitude."""
        return math.sqrt(
            self.initial_velocity_x ** 2 +
            self.initial_velocity_y ** 2 +
            self.initial_velocity_z ** 2
        )


def create_fade_status() -> VelocityFadeStatus:
    """Create initial velocity fade status."""
    return VelocityFadeStatus()


def apply_initial_velocity(
    status: VelocityFadeStatus,
    velocity: Tuple[float, float, float],
) -> VelocityFadeStatus:
    """
    Apply initial repulsion velocity to start fade.
    
    Args:
        status: Current fade status
        velocity: Initial velocity vector (vx, vy, vz)
        
    Returns:
        New status with velocity applied
    """
    vx, vy, vz = velocity
    speed = math.sqrt(vx*vx + vy*vy + vz*vz)
    
    return VelocityFadeStatus(
        velocity_x=vx,
        velocity_y=vy,
        velocity_z=vz,
        initial_velocity_x=vx,
        initial_velocity_y=vy,
        initial_velocity_z=vz,
        elapsed_time=0.0,
        distance_traveled=0.0,
        is_active=speed > 0.0,
        is_stopped=speed == 0.0,
    )


def velocity_from_force(
    force: Tuple[float, float, float],
    mass: float = 1.0,
    delta_time: float = 0.016,  # ~60fps
) -> Tuple[float, float, float]:
    """
    Convert force impulse to velocity.
    
    Uses F = ma, so v = F * dt / m
    
    Args:
        force: Force vector (fx, fy, fz)
        mass: Creature mass (default 1.0 for unit response)
        delta_time: Time step for impulse
        
    Returns:
        Velocity vector
    """
    fx, fy, fz = force
    scale = delta_time / mass
    return (fx * scale, fy * scale, fz * scale)


def _calculate_decay_factor(
    elapsed_time: float,
    distance_traveled: float,
    config: VelocityFadeConfig,
) -> float:
    """
    Calculate velocity decay factor based on mode.
    
    Returns value from 1.0 (full velocity) to 0.0 (stopped).
    """
    if config.fade_mode == FadeMode.TIME_BASED:
        # Exponential decay over time
        if config.fade_duration <= 0:
            return 0.0
        t_ratio = elapsed_time / config.fade_duration
        return math.exp(-config.decay_rate * t_ratio)
    
    elif config.fade_mode == FadeMode.DISTANCE_BASED:
        # Exponential decay over distance
        if config.fade_distance <= 0:
            return 0.0
        d_ratio = distance_traveled / config.fade_distance
        return math.exp(-config.decay_rate * d_ratio)
    
    else:  # HYBRID
        # Use minimum of both (whichever decays faster)
        time_factor = 1.0
        dist_factor = 1.0
        
        if config.fade_duration > 0:
            t_ratio = elapsed_time / config.fade_duration
            time_factor = math.exp(-config.decay_rate * t_ratio)
        
        if config.fade_distance > 0:
            d_ratio = distance_traveled / config.fade_distance
            dist_factor = math.exp(-config.decay_rate * d_ratio)
        
        return min(time_factor, dist_factor)


def update_velocity(
    status: VelocityFadeStatus,
    delta_time: float,
    config: VelocityFadeConfig = None,
) -> VelocityFadeStatus:
    """
    Update velocity with decay applied.
    
    Call each frame to apply gradual deceleration.
    
    Args:
        status: Current fade status
        delta_time: Time since last update (seconds)
        config: Fade configuration
        
    Returns:
        Updated status with decayed velocity
    """
    if config is None:
        config = VelocityFadeConfig()
    
    if not status.is_active or status.is_stopped:
        return status
    
    # Calculate distance traveled this frame
    frame_distance = status.speed * delta_time
    
    # Update tracking
    new_elapsed = status.elapsed_time + delta_time
    new_distance = status.distance_traveled + frame_distance
    
    # Calculate decay factor
    decay = _calculate_decay_factor(new_elapsed, new_distance, config)
    
    # Apply decay to initial velocity (not current, to avoid compound decay issues)
    new_vx = status.initial_velocity_x * decay
    new_vy = status.initial_velocity_y * decay
    new_vz = status.initial_velocity_z * decay
    
    # Apply optional drag (additional linear damping)
    if config.drag_coefficient > 0:
        drag = 1.0 - (config.drag_coefficient * delta_time)
        drag = max(0.0, drag)  # Prevent negative
        new_vx *= drag
        new_vy *= drag
        new_vz *= drag
    
    # Check if stopped
    new_speed = math.sqrt(new_vx*new_vx + new_vy*new_vy + new_vz*new_vz)
    is_stopped = new_speed < config.velocity_epsilon
    
    if is_stopped:
        new_vx = 0.0
        new_vy = 0.0
        new_vz = 0.0
    
    return VelocityFadeStatus(
        velocity_x=new_vx,
        velocity_y=new_vy,
        velocity_z=new_vz,
        initial_velocity_x=status.initial_velocity_x,
        initial_velocity_y=status.initial_velocity_y,
        initial_velocity_z=status.initial_velocity_z,
        elapsed_time=new_elapsed,
        distance_traveled=new_distance,
        is_active=not is_stopped,
        is_stopped=is_stopped,
    )


def get_displacement(
    status: VelocityFadeStatus,
    delta_time: float,
) -> Tuple[float, float, float]:
    """
    Get position change for this frame.
    
    Use this to move the creature each frame.
    
    Args:
        status: Current velocity status
        delta_time: Time step
        
    Returns:
        Position delta (dx, dy, dz)
    """
    return (
        status.velocity_x * delta_time,
        status.velocity_y * delta_time,
        status.velocity_z * delta_time,
    )


def get_fade_progress(
    status: VelocityFadeStatus,
    config: VelocityFadeConfig = None,
) -> float:
    """
    Get fade progress as 0.0 to 1.0.
    
    0.0 = just started (full velocity)
    1.0 = completed (stopped)
    
    Useful for coordinating with other effects.
    """
    if config is None:
        config = VelocityFadeConfig()
    
    if status.is_stopped:
        return 1.0
    
    if not status.is_active:
        return 0.0
    
    initial = status.initial_speed
    if initial < config.velocity_epsilon:
        return 1.0
    
    current = status.speed
    # Progress is inverse of remaining velocity ratio
    return 1.0 - (current / initial)


def reset_velocity(status: VelocityFadeStatus) -> VelocityFadeStatus:
    """Reset velocity fade to inactive state."""
    return VelocityFadeStatus(
        velocity_x=0.0,
        velocity_y=0.0,
        velocity_z=0.0,
        initial_velocity_x=0.0,
        initial_velocity_y=0.0,
        initial_velocity_z=0.0,
        elapsed_time=0.0,
        distance_traveled=0.0,
        is_active=False,
        is_stopped=True,
    )


def is_velocity_active(status: VelocityFadeStatus) -> bool:
    """Check if velocity fade is currently in progress."""
    return status.is_active and not status.is_stopped


def is_velocity_stopped(status: VelocityFadeStatus) -> bool:
    """Check if velocity has faded to zero."""
    return status.is_stopped


def get_current_speed(status: VelocityFadeStatus) -> float:
    """Get current velocity magnitude."""
    return status.speed


def get_velocity_direction(
    status: VelocityFadeStatus,
) -> Optional[Tuple[float, float, float]]:
    """
    Get normalized velocity direction.
    
    Returns None if velocity is zero.
    """
    speed = status.speed
    if speed < 1e-8:
        return None
    
    return (
        status.velocity_x / speed,
        status.velocity_y / speed,
        status.velocity_z / speed,
    )
