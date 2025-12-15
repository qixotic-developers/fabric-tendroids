"""
Proximity Detection Configuration Constants

Defines grid dimensions, search radii, and detection thresholds
for GPU-accelerated creature-tendroid proximity detection.

TEND-15: Warp Hash Grid infrastructure
TEND-17: approach_epsilon and approach_minimum parameters
TEND-68: Define approach_epsilon parameter with default value
TEND-69: Define approach_minimum parameter with default value
TEND-70: Add parameters to config file
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional


class DistanceUnit(Enum):
  """Distance measurement units."""
  METERS = "m"
  CENTIMETERS = "cm"
  MILLIMETERS = "mm"


@dataclass
class GridConfig:
  """Hash Grid dimensional configuration."""

  dim_x: int = 128
  dim_y: int = 64
  dim_z: int = 128
  cell_size: float = 1.0
  device: str = "cuda:0"

  def get_grid_bounds(self) -> tuple:
    """Calculate world-space bounds covered by grid."""
    half_x = (self.dim_x * self.cell_size) / 2.0
    half_y = (self.dim_y * self.cell_size) / 2.0
    half_z = (self.dim_z * self.cell_size) / 2.0
    return ((-half_x, -half_y, -half_z), (half_x, half_y, half_z))


@dataclass
class ApproachParameters:
  """
  Distance parameters for creature-tendroid proximity detection.

  TEND-17: These parameters define the zones around a tendroid
  that trigger different creature behaviors.

  All distances are in METERS and measured from tendroid surface.
  Use RELATIVE distances (from surface) not absolute coordinates.

  Zone Diagram (cross-section view):

      |<-------- detection_radius -------->|
      |                                    |
      |    |<--- warning_distance --->|    |
      |    |                          |    |
      |    |  |<- approach_min ->|    |    |
      |    |  |                  |    |    |
      |    |  | |<-epsilon->|    |    |    |
      |    |  | |  TENDROID |    |    |    |
      |    |  | |___________|    |    |    |
      |    |  |   CONTACT        |    |    |
      |    |  |__________________|    |    |
      |    |       RECOVERING         |    |
      |    |__________________________|    |
      |          APPROACHING               |
      |____________________________________|
                  DETECTED
  """

  # TEND-68: approach_epsilon - Contact trigger distance
  # When creature distance < epsilon, contact is triggered
  # Matches PhysX contactOffset for consistency
  approach_epsilon: float = 0.04  # 4cm - danger zone

  # TEND-69: approach_minimum - Recovery threshold distance
  # Creature must retreat beyond this to be "recovered"
  # Prevents oscillation at boundary
  approach_minimum: float = 0.15  # 15cm - safe clearance

  # Warning distance - early detection for smoother avoidance
  warning_distance: float = 0.25  # 25cm - start slowing

  # Detection radius - maximum query distance
  detection_radius: float = 1.0  # 1m - outer boundary

  def validate(self) -> tuple:
    """
    Validate parameter consistency.

    Returns:
        Tuple of (is_valid, error_message)
    """
    if self.approach_epsilon <= 0:
      return False, "approach_epsilon must be positive"
    if self.approach_minimum <= self.approach_epsilon:
      return False, "approach_minimum must be > approach_epsilon"
    if self.warning_distance <= self.approach_minimum:
      return False, "warning_distance must be > approach_minimum"
    if self.detection_radius <= self.warning_distance:
      return False, "detection_radius must be > warning_distance"
    return True, "OK"

  def to_centimeters(self) -> Dict[str, float]:
    """Return parameters in centimeters for display."""
    return {
      "approach_epsilon_cm": self.approach_epsilon * 100,
      "approach_minimum_cm": self.approach_minimum * 100,
      "warning_distance_cm": self.warning_distance * 100,
      "detection_radius_cm": self.detection_radius * 100,
    }

  def get_zone(self, distance: float) -> str:
    """
    Determine which zone a distance falls into.

    Args:
        distance: Distance from tendroid surface in meters

    Returns:
        Zone name: "contact", "recovering", "approaching", "detected", "idle"
    """
    if distance <= self.approach_epsilon:
      return "contact"
    elif distance <= self.approach_minimum:
      return "recovering"
    elif distance <= self.warning_distance:
      return "approaching"
    elif distance <= self.detection_radius:
      return "detected"
    else:
      return "idle"


# Backwards compatibility alias
ProximityConfig = ApproachParameters

# ============================================================================
# Presets for different scenarios
# ============================================================================

APPROACH_PRESETS: Dict[str, ApproachParameters] = {
  # Default balanced preset
  "default": ApproachParameters(
    approach_epsilon=0.04,
    approach_minimum=0.15,
    warning_distance=0.25,
    detection_radius=1.0,
  ),

  # Tight tolerances for small creatures
  "small_creature": ApproachParameters(
    approach_epsilon=0.02,  # 2cm
    approach_minimum=0.08,  # 8cm
    warning_distance=0.15,  # 15cm
    detection_radius=0.5,  # 50cm
  ),

  # Generous spacing for large creatures
  "large_creature": ApproachParameters(
    approach_epsilon=0.08,  # 8cm
    approach_minimum=0.25,  # 25cm
    warning_distance=0.50,  # 50cm
    detection_radius=2.0,  # 2m
  ),

  # Sensitive detection for demo/testing
  "sensitive": ApproachParameters(
    approach_epsilon=0.10,  # 10cm - easy to trigger
    approach_minimum=0.30,  # 30cm
    warning_distance=0.60,  # 60cm
    detection_radius=1.5,  # 1.5m
  ),
}

SCENE_PRESETS = {
  "small": GridConfig(dim_x=64, dim_y=32, dim_z=64, cell_size=0.5),
  "medium": GridConfig(dim_x=128, dim_y=64, dim_z=128, cell_size=1.0),
  "large": GridConfig(dim_x=256, dim_y=128, dim_z=256, cell_size=2.0),
}

# Default instances
DEFAULT_GRID_CONFIG = GridConfig()
DEFAULT_PROXIMITY_CONFIG = ApproachParameters()
DEFAULT_APPROACH_PARAMS = DEFAULT_PROXIMITY_CONFIG  # Alias


# ============================================================================
# Factory functions
# ============================================================================

def get_grid_config(preset: Optional[str] = None) -> GridConfig:
  """Get grid configuration by preset name."""
  if preset is None:
    return DEFAULT_GRID_CONFIG
  return SCENE_PRESETS.get(preset, DEFAULT_GRID_CONFIG)


def get_proximity_config() -> ApproachParameters:
  """Get default proximity configuration."""
  return DEFAULT_PROXIMITY_CONFIG


def get_approach_params(preset: Optional[str] = None) -> ApproachParameters:
  """
  Get approach parameters by preset name.

  Args:
      preset: One of "default", "small_creature", "large_creature", "sensitive"

  Returns:
      ApproachParameters instance
  """
  if preset is None:
    return DEFAULT_APPROACH_PARAMS
  return APPROACH_PRESETS.get(preset, DEFAULT_APPROACH_PARAMS)


def create_custom_approach_params(
  epsilon_cm: float,
  minimum_cm: float,
  warning_cm: float,
  detection_cm: float
) -> ApproachParameters:
  """
  Create custom approach parameters from centimeter values.

  Args:
      epsilon_cm: Contact trigger distance in cm
      minimum_cm: Recovery threshold in cm
      warning_cm: Warning zone start in cm
      detection_cm: Detection radius in cm

  Returns:
      ApproachParameters instance (values converted to meters)
  """
  params = ApproachParameters(
    approach_epsilon=epsilon_cm / 100.0,
    approach_minimum=minimum_cm / 100.0,
    warning_distance=warning_cm / 100.0,
    detection_radius=detection_cm / 100.0,
  )
  valid, msg = params.validate()
  if not valid:
    raise ValueError(f"Invalid parameters: {msg}")
  return params
