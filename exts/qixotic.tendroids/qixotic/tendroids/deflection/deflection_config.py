"""
Deflection System Configuration

TEND-3: Tendroid Deflection System
TEND-22: Deflection proportionality parameters

Defines bend angles, thresholds, and physics parameters
for tendroid deflection behavior.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import math


class ApproachType(Enum):
    """Types of creature approach trajectories."""
    VERTICAL = "vertical"     # Pass-over (Y-axis aware)
    HEAD_ON = "head_on"       # Direct approach
    PASS_BY = "pass_by"       # Lateral movement past tendroid
    NONE = "none"             # No approach detected


@dataclass
class DeflectionLimits:
    """
    Bend angle limits for tendroid deflection.
    
    TEND-22: Height-based proportionality uses these values.
    
    Angles in radians. Convert from degrees if needed:
        radians = degrees * (pi / 180)
    """
    
    # Minimum deflection at tendroid base
    minimum_deflection: float = 0.0524  # ~3 degrees
    
    # Maximum deflection at tendroid tip  
    maximum_deflection: float = 0.5236  # ~30 degrees
    
    # Recovery speed (radians per second)
    recovery_rate: float = 0.8
    
    # Deflection application speed
    deflection_rate: float = 1.5
    
    @classmethod
    def from_degrees(cls, min_deg: float, max_deg: float) -> 'DeflectionLimits':
        """Create limits from degree values."""
        return cls(
            minimum_deflection=math.radians(min_deg),
            maximum_deflection=math.radians(max_deg)
        )
    
    def to_degrees(self) -> Dict[str, float]:
        """Return limits in degrees for UI display."""
        return {
            "minimum_deg": math.degrees(self.minimum_deflection),
            "maximum_deg": math.degrees(self.maximum_deflection),
        }
    
    def validate(self) -> tuple:
        """Validate limit values."""
        if self.minimum_deflection < 0:
            return False, "minimum_deflection must be >= 0"
        if self.maximum_deflection <= self.minimum_deflection:
            return False, "maximum must be > minimum"
        if self.maximum_deflection > math.pi / 2:
            return False, "maximum_deflection cannot exceed 90 degrees"
        return True, "OK"


@dataclass  
class DetectionZones:
    """
    Distance thresholds for deflection triggering.
    
    All distances in meters, measured from tendroid surface.
    """
    
    # Tendroid cylinder radius
    tendroid_radius: float = 0.05  # 5cm default
    
    # Detection circle = tendroid_radius + approach_buffer
    approach_buffer: float = 0.15  # 15cm buffer
    
    # Minimum distance for deflection calculation
    approach_minimum: float = 0.04  # 4cm - matches PhysX contact offset
    
    # Maximum detection range
    detection_range: float = 0.5  # 50cm outer boundary
    
    @property
    def detection_radius(self) -> float:
        """Total detection radius from tendroid center."""
        return self.tendroid_radius + self.approach_buffer
    
    def get_distance_ratio(self, surface_distance: float) -> float:
        """
        Calculate normalized distance ratio.
        
        Args:
            surface_distance: Distance from tendroid surface
            
        Returns:
            0.0 at approach_minimum, 1.0 at detection_range
        """
        effective_range = self.detection_range - self.approach_minimum
        if effective_range <= 0:
            return 1.0
        clamped = max(self.approach_minimum, min(surface_distance, self.detection_range))
        return (clamped - self.approach_minimum) / effective_range


@dataclass
class DeflectionConfig:
    """
    Complete configuration for tendroid deflection system.
    
    TEND-3: Tendroid Deflection System
    """
    
    limits: DeflectionLimits = field(default_factory=DeflectionLimits)
    zones: DetectionZones = field(default_factory=DetectionZones)
    
    # Enable/disable specific approach types
    enable_vertical: bool = True
    enable_head_on: bool = True
    enable_pass_by: bool = True
    
    # Debug options
    debug_logging: bool = False
    debug_visualization: bool = False


# =============================================================================
# Presets
# =============================================================================

DEFLECTION_PRESETS: Dict[str, DeflectionConfig] = {
    "default": DeflectionConfig(),
    
    "sensitive": DeflectionConfig(
        limits=DeflectionLimits.from_degrees(5.0, 45.0),
        zones=DetectionZones(
            approach_buffer=0.25,
            detection_range=0.75,
        ),
    ),
    
    "subtle": DeflectionConfig(
        limits=DeflectionLimits.from_degrees(1.0, 15.0),
        zones=DetectionZones(
            approach_buffer=0.10,
            detection_range=0.30,
        ),
    ),
}

DEFAULT_CONFIG = DeflectionConfig()


def get_deflection_config(preset: Optional[str] = None) -> DeflectionConfig:
    """Get deflection configuration by preset name."""
    if preset is None:
        return DEFAULT_CONFIG
    return DEFLECTION_PRESETS.get(preset, DEFAULT_CONFIG)
