"""
Approach Tracker Helpers - Track approach_minimum threshold for recovery

Tracks distance from creature to tendroid surface during recovery,
accounting for the fact that the tendroid is also moving back to its
normal position. Recovery completes when creature distance exceeds
approach_minimum threshold.

Implements TEND-29: Track approach_minimum during creature movement.
Implements TEND-112: Create approach_tracker_helpers.py module.
Implements TEND-113: Implement distance tracking to tendroid surface.
Implements TEND-114: Implement threshold crossing detection.
Implements TEND-115: Handle moving tendroid surface coordinates.
"""

import math
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Tuple


class RecoveryPhase(Enum):
    """Phases of the recovery tracking process."""
    INACTIVE = auto()      # Not tracking (no contact occurred)
    TRACKING = auto()      # Actively tracking distance during recovery
    THRESHOLD_CROSSED = auto()  # Distance exceeded approach_minimum
    COMPLETE = auto()      # Recovery finished


@dataclass
class TendroidSurfacePoint:
    """
    Represents a point on the tendroid surface.
    
    The tendroid surface moves during recovery as the tendroid
    returns to its normal position. This tracks both the current
    and rest positions.
    """
    # Current surface position (may be deflected)
    current_x: float = 0.0
    current_y: float = 0.0
    current_z: float = 0.0
    
    # Rest position (where surface will return to)
    rest_x: float = 0.0
    rest_y: float = 0.0
    rest_z: float = 0.0
    
    # Surface normal pointing outward from tendroid
    normal_x: float = 1.0
    normal_y: float = 0.0
    normal_z: float = 0.0
    
    @property
    def current_position(self) -> Tuple[float, float, float]:
        """Current surface position as tuple."""
        return (self.current_x, self.current_y, self.current_z)
    
    @property
    def rest_position(self) -> Tuple[float, float, float]:
        """Rest surface position as tuple."""
        return (self.rest_x, self.rest_y, self.rest_z)
    
    @property
    def normal(self) -> Tuple[float, float, float]:
        """Surface normal as tuple."""
        return (self.normal_x, self.normal_y, self.normal_z)
    
    def deflection_amount(self) -> float:
        """Calculate how far surface is from rest position."""
        dx = self.current_x - self.rest_x
        dy = self.current_y - self.rest_y
        dz = self.current_z - self.rest_z
        return math.sqrt(dx * dx + dy * dy + dz * dz)


@dataclass
class ApproachTrackerStatus:
    """
    Current status of approach threshold tracking.
    
    Tracks the creature's distance to the tendroid surface
    throughout the recovery process.
    """
    phase: RecoveryPhase = RecoveryPhase.INACTIVE
    
    # Current distance from creature to tendroid surface
    current_distance: float = float('inf')
    
    # Threshold that must be exceeded for recovery
    threshold_distance: float = 0.15  # approach_minimum default
    
    # Minimum distance recorded during this recovery
    min_distance_recorded: float = float('inf')
    
    # Maximum distance recorded during this recovery
    max_distance_recorded: float = 0.0
    
    # Number of distance updates processed
    update_count: int = 0
    
    # Total recovery tracking sessions completed
    recovery_count: int = 0


def calculate_distance_to_surface(
    creature_pos: Tuple[float, float, float],
    surface_point: TendroidSurfacePoint,
) -> float:
    """
    Calculate distance from creature to tendroid surface point.
    
    Uses the current (possibly deflected) surface position,
    not the rest position. This ensures accurate tracking
    while the tendroid is recovering.
    
    Args:
        creature_pos: (x, y, z) creature world position
        surface_point: Current tendroid surface information
        
    Returns:
        Distance in meters from creature to surface
    """
    cx, cy, cz = creature_pos
    
    # Distance to current (moving) surface position
    dx = cx - surface_point.current_x
    dy = cy - surface_point.current_y
    dz = cz - surface_point.current_z
    
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def calculate_signed_distance_to_surface(
    creature_pos: Tuple[float, float, float],
    surface_point: TendroidSurfacePoint,
) -> float:
    """
    Calculate signed distance from creature to tendroid surface.
    
    Positive = creature is outside tendroid (in normal direction)
    Negative = creature is inside tendroid (shouldn't happen)
    
    Args:
        creature_pos: (x, y, z) creature world position
        surface_point: Current tendroid surface information
        
    Returns:
        Signed distance (positive = outside, negative = inside)
    """
    cx, cy, cz = creature_pos
    
    # Vector from surface to creature
    dx = cx - surface_point.current_x
    dy = cy - surface_point.current_y
    dz = cz - surface_point.current_z
    
    # Project onto surface normal
    dot = (
        dx * surface_point.normal_x +
        dy * surface_point.normal_y +
        dz * surface_point.normal_z
    )
    
    return dot


def start_tracking(
    status: ApproachTrackerStatus,
    threshold: float,
    initial_distance: float,
) -> ApproachTrackerStatus:
    """
    Start tracking distance for recovery.
    
    Called when contact occurs and recovery begins.
    
    Args:
        status: Current tracker status
        threshold: approach_minimum threshold distance
        initial_distance: Distance at start of tracking
        
    Returns:
        Updated status with tracking active
    """
    return ApproachTrackerStatus(
        phase=RecoveryPhase.TRACKING,
        current_distance=initial_distance,
        threshold_distance=threshold,
        min_distance_recorded=initial_distance,
        max_distance_recorded=initial_distance,
        update_count=1,
        recovery_count=status.recovery_count,
    )


def update_distance(
    status: ApproachTrackerStatus,
    creature_pos: Tuple[float, float, float],
    surface_point: TendroidSurfacePoint,
) -> ApproachTrackerStatus:
    """
    Update tracked distance with new creature position.
    
    Recalculates distance accounting for moving tendroid surface.
    Checks if threshold has been crossed.
    
    Args:
        status: Current tracker status
        creature_pos: Current creature world position
        surface_point: Current tendroid surface point (may have moved)
        
    Returns:
        Updated status with new distance and phase
    """
    if status.phase != RecoveryPhase.TRACKING:
        return status
    
    # Calculate distance to current (moving) surface
    distance = calculate_distance_to_surface(creature_pos, surface_point)
    
    # Update statistics
    new_min = min(status.min_distance_recorded, distance)
    new_max = max(status.max_distance_recorded, distance)
    
    # Check if threshold crossed
    new_phase = status.phase
    if distance > status.threshold_distance:
        new_phase = RecoveryPhase.THRESHOLD_CROSSED
    
    return ApproachTrackerStatus(
        phase=new_phase,
        current_distance=distance,
        threshold_distance=status.threshold_distance,
        min_distance_recorded=new_min,
        max_distance_recorded=new_max,
        update_count=status.update_count + 1,
        recovery_count=status.recovery_count,
    )


def check_threshold_crossed(status: ApproachTrackerStatus) -> bool:
    """
    Check if the approach_minimum threshold has been crossed.
    
    Args:
        status: Current tracker status
        
    Returns:
        True if creature distance exceeds threshold
    """
    if status.phase == RecoveryPhase.THRESHOLD_CROSSED:
        return True
    if status.phase == RecoveryPhase.COMPLETE:
        return True
    return status.current_distance > status.threshold_distance


def complete_recovery(
    status: ApproachTrackerStatus,
) -> ApproachTrackerStatus:
    """
    Mark recovery as complete.
    
    Called after threshold is crossed and all recovery
    effects (color fade, etc.) have finished.
    
    Args:
        status: Current tracker status
        
    Returns:
        Updated status with recovery complete
    """
    return ApproachTrackerStatus(
        phase=RecoveryPhase.COMPLETE,
        current_distance=status.current_distance,
        threshold_distance=status.threshold_distance,
        min_distance_recorded=status.min_distance_recorded,
        max_distance_recorded=status.max_distance_recorded,
        update_count=status.update_count,
        recovery_count=status.recovery_count + 1,
    )


def reset_tracker(
    status: ApproachTrackerStatus,
) -> ApproachTrackerStatus:
    """
    Reset tracker to inactive state.
    
    Called after recovery completes to prepare for next contact.
    Preserves recovery_count for statistics.
    
    Args:
        status: Current tracker status
        
    Returns:
        Reset status ready for next tracking session
    """
    return ApproachTrackerStatus(
        phase=RecoveryPhase.INACTIVE,
        current_distance=float('inf'),
        threshold_distance=status.threshold_distance,
        min_distance_recorded=float('inf'),
        max_distance_recorded=0.0,
        update_count=0,
        recovery_count=status.recovery_count,
    )


def update_surface_point(
    surface: TendroidSurfacePoint,
    new_current: Tuple[float, float, float],
    new_normal: Optional[Tuple[float, float, float]] = None,
) -> TendroidSurfacePoint:
    """
    Update surface point with new current position.
    
    Called each frame as tendroid returns to rest position.
    Rest position remains unchanged.
    
    Args:
        surface: Current surface point
        new_current: New current position
        new_normal: Optional new normal direction
        
    Returns:
        Updated surface point
    """
    nx, ny, nz = new_normal if new_normal else surface.normal
    
    return TendroidSurfacePoint(
        current_x=new_current[0],
        current_y=new_current[1],
        current_z=new_current[2],
        rest_x=surface.rest_x,
        rest_y=surface.rest_y,
        rest_z=surface.rest_z,
        normal_x=nx,
        normal_y=ny,
        normal_z=nz,
    )


def create_surface_point_from_contact(
    contact_point: Tuple[float, float, float],
    surface_normal: Tuple[float, float, float],
    rest_offset: float = 0.0,
) -> TendroidSurfacePoint:
    """
    Create surface point from contact event data.
    
    Args:
        contact_point: Point where contact occurred
        surface_normal: Normal pointing away from tendroid
        rest_offset: Distance surface will move back (deflection amount)
        
    Returns:
        Surface point with current and rest positions
    """
    cx, cy, cz = contact_point
    nx, ny, nz = surface_normal
    
    # Rest position is current position minus deflection along normal
    # (surface was pushed inward, rest is further out)
    rest_x = cx + nx * rest_offset
    rest_y = cy + ny * rest_offset
    rest_z = cz + nz * rest_offset
    
    return TendroidSurfacePoint(
        current_x=cx,
        current_y=cy,
        current_z=cz,
        rest_x=rest_x,
        rest_y=rest_y,
        rest_z=rest_z,
        normal_x=nx,
        normal_y=ny,
        normal_z=nz,
    )


def get_recovery_progress(status: ApproachTrackerStatus) -> float:
    """
    Calculate recovery progress as percentage.
    
    0.0 = just contacted (at minimum distance)
    1.0 = threshold crossed (recovery complete)
    
    Args:
        status: Current tracker status
        
    Returns:
        Progress from 0.0 to 1.0
    """
    if status.phase == RecoveryPhase.INACTIVE:
        return 0.0
    if status.phase == RecoveryPhase.COMPLETE:
        return 1.0
    
    # Progress based on distance traveled
    min_dist = status.min_distance_recorded
    threshold = status.threshold_distance
    current = status.current_distance
    
    if threshold <= min_dist:
        return 1.0  # Already past threshold
    
    # Linear interpolation
    travel_needed = threshold - min_dist
    travel_done = current - min_dist
    
    progress = travel_done / travel_needed if travel_needed > 0 else 1.0
    return max(0.0, min(1.0, progress))


def is_tracking_active(status: ApproachTrackerStatus) -> bool:
    """Check if distance tracking is currently active."""
    return status.phase == RecoveryPhase.TRACKING


def is_recovery_complete(status: ApproachTrackerStatus) -> bool:
    """Check if recovery has completed."""
    return status.phase in (
        RecoveryPhase.THRESHOLD_CROSSED,
        RecoveryPhase.COMPLETE,
    )


def get_phase_name(status: ApproachTrackerStatus) -> str:
    """Get human-readable name of current phase."""
    return status.phase.name
