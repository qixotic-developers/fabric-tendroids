"""
Test Case Definitions

Data structures for automated creature-tendroid interaction tests.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class TestWaypoint:
    """
    A point along the test animation path.
    
    Attributes:
        position: Absolute (x, y, z) world position
        fraction: 0.0 - 1.0 of total test duration to reach this point
    """
    position: Tuple[float, float, float]
    fraction: float  # 0.0 = start, 1.0 = end
    
    def __post_init__(self):
        if not 0.0 <= self.fraction <= 1.0:
            raise ValueError(f"fraction must be 0.0-1.0, got {self.fraction}")


@dataclass
class TestCase:
    """
    Definition of a single automated test.
    
    Attributes:
        id: Unique identifier (e.g., "head_on_contact_high")
        name: Display name (e.g., "Head-on Contact (HIGH)")
        category: Grouping for UI (head_on, off_center, pass_by, recovery, special)
        description: What this test validates
        waypoints: Sequence of positions with timing fractions
    """
    id: str
    name: str
    category: str
    description: str
    waypoints: List[TestWaypoint] = field(default_factory=list)
    
    def get_position_at_fraction(self, fraction: float) -> Tuple[float, float, float]:
        """
        Interpolate position at given fraction (0.0 - 1.0) of test duration.
        
        Uses linear interpolation between waypoints.
        """
        if not self.waypoints:
            return (0.0, 50.0, 0.0)
        
        # Clamp fraction
        fraction = max(0.0, min(1.0, fraction))
        
        # Find surrounding waypoints
        prev_wp = self.waypoints[0]
        next_wp = self.waypoints[-1]
        
        for i, wp in enumerate(self.waypoints):
            if wp.fraction >= fraction:
                next_wp = wp
                if i > 0:
                    prev_wp = self.waypoints[i - 1]
                break
            prev_wp = wp
        
        # Handle exact match or single waypoint
        if prev_wp.fraction == next_wp.fraction:
            return prev_wp.position
        
        # Linear interpolation between waypoints
        segment_fraction = (fraction - prev_wp.fraction) / (next_wp.fraction - prev_wp.fraction)
        
        return (
            prev_wp.position[0] + (next_wp.position[0] - prev_wp.position[0]) * segment_fraction,
            prev_wp.position[1] + (next_wp.position[1] - prev_wp.position[1]) * segment_fraction,
            prev_wp.position[2] + (next_wp.position[2] - prev_wp.position[2]) * segment_fraction,
        )
    
    def get_start_position(self) -> Tuple[float, float, float]:
        """Get the starting position (first waypoint)."""
        if self.waypoints:
            return self.waypoints[0].position
        return (0.0, 50.0, 0.0)


@dataclass 
class TestResult:
    """
    Results captured from a test run.
    
    Populated by TestController during/after test execution.
    """
    test_id: str
    duration: float
    timestamp: str = ""
    
    # Outcomes
    contact_occurred: bool = False
    contact_time: float = 0.0
    max_deflection_angle: float = 0.0
    repulsion_triggered: bool = False
    color_effect_triggered: bool = False
    input_locked: bool = False
    tendroid_recovered: bool = False
    
    def to_dict(self) -> dict:
        """Convert to dictionary for YAML serialization."""
        return {
            'test_id': self.test_id,
            'timestamp': self.timestamp,
            'duration': self.duration,
            'result': {
                'contact_occurred': self.contact_occurred,
                'contact_time': self.contact_time,
                'max_deflection_angle': self.max_deflection_angle,
                'repulsion_triggered': self.repulsion_triggered,
                'color_effect_triggered': self.color_effect_triggered,
                'input_locked': self.input_locked,
                'tendroid_recovered': self.tendroid_recovered,
            }
        }
