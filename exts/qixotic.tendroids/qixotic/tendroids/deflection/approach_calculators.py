"""
Approach Calculators - Distance and approach type detection

TEND-19: Vertical (Y-axis) proximity calculation for pass-over
TEND-20: Head-on approach detection  
TEND-21: Pass-by approach detection

Pure calculation functions - no state, testable independently.
"""

import math
from dataclasses import dataclass
from typing import Tuple

from .deflection_config import ApproachType, DetectionZones


@dataclass
class TendroidGeometry:
  """
  Tendroid cylinder geometry for proximity calculations.

  Coordinate system:
  - Y-axis is vertical (up)
  - Base is at base_y, tip at base_y + height
  - Cylinder centered at (center_x, center_z) in XZ plane
  """
  center_x: float
  center_z: float
  base_y: float
  height: float
  radius: float

  @property
  def tip_y(self) -> float:
    """Y coordinate of tendroid tip."""
    return self.base_y + self.height

  @property
  def center_y(self) -> float:
    """Y coordinate of tendroid center."""
    return self.base_y + self.height / 2.0


@dataclass
class ApproachResult:
  """Result of approach type detection."""
  approach_type: ApproachType
  distance: float  # Distance to tendroid surface
  height_ratio: float  # 0.0=base, 1.0=tip (for vertical)
  contact_y: float  # Y-coordinate of contact point
  contact_normal: Tuple[float, float, float]  # Surface normal
  is_within_range: bool  # True if within detection zone


# =============================================================================
# TEND-19: Vertical (Y-axis) Proximity Calculation
# =============================================================================

def calculate_vertical_proximity(
  creature_pos: Tuple[float, float, float],
  tendroid: TendroidGeometry,
  zones: DetectionZones
) -> ApproachResult:
  """
  Calculate vertical (pass-over) proximity for Y-axis aware deflection.

  TEND-19 Implementation:
  - Creature Y must be between base_y and tip_y to trigger
  - Deflection proportional to height above base
  - Uses horizontal (XZ) distance for proximity check

  Args:
      creature_pos: (x, y, z) creature position
      tendroid: Tendroid cylinder geometry
      zones: Detection zone thresholds

  Returns:
      ApproachResult with vertical approach data
  """
  cx, cy, cz = creature_pos

  # Check if creature Y is within tendroid height range
  if cy < tendroid.base_y or cy > tendroid.tip_y:
    return ApproachResult(
      approach_type=ApproachType.NONE,
      distance=float('inf'),
      height_ratio=0.0,
      contact_y=tendroid.base_y,
      contact_normal=(0.0, 0.0, 0.0),
      is_within_range=False
    )

  # Calculate horizontal distance (XZ plane only)
  dx = cx - tendroid.center_x
  dz = cz - tendroid.center_z
  horizontal_dist = math.sqrt(dx * dx + dz * dz)

  # Distance from tendroid surface
  surface_distance = horizontal_dist - tendroid.radius

  # Check if within detection range
  is_within = surface_distance <= zones.detection_range

  # Calculate height ratio: 0.0 at base, 1.0 at tip
  height_ratio = (cy - tendroid.base_y) / tendroid.height
  height_ratio = max(0.0, min(1.0, height_ratio))

  # Contact point is at creature's Y level on tendroid surface
  contact_y = cy

  # Surface normal points from tendroid center toward creature (XZ plane)
  if horizontal_dist > 1e-6:
    nx = dx / horizontal_dist
    nz = dz / horizontal_dist
  else:
    nx, nz = 1.0, 0.0  # Default normal if exactly on axis

  return ApproachResult(
    approach_type=ApproachType.VERTICAL if is_within else ApproachType.NONE,
    distance=max(0.0, surface_distance),
    height_ratio=height_ratio,
    contact_y=contact_y,
    contact_normal=(nx, 0.0, nz),
    is_within_range=is_within
  )


# =============================================================================
# TEND-20: Head-On Approach Detection
# =============================================================================

def calculate_head_on_approach(
  creature_pos: Tuple[float, float, float],
  creature_velocity: Tuple[float, float, float],
  tendroid: TendroidGeometry,
  zones: DetectionZones,
  head_on_threshold: float = 0.7
) -> ApproachResult:
  """
  Calculate head-on approach for direct creature movement toward tendroid.

  TEND-20 Implementation:
  - Distance measured from creature to tendroid surface
  - Deflection inversely proportional to distance
  - Surface normals used for deflection direction

  Args:
      creature_pos: (x, y, z) creature position
      creature_velocity: (vx, vy, vz) creature velocity
      tendroid: Tendroid cylinder geometry
      zones: Detection zone thresholds
      head_on_threshold: Cos(angle) threshold for head-on detection

  Returns:
      ApproachResult with head-on approach data
  """
  cx, cy, cz = creature_pos
  vx, vy, vz = creature_velocity

  # Find closest point on tendroid axis to creature
  # Clamp creature Y to tendroid height range for axis projection
  axis_y = max(tendroid.base_y, min(cy, tendroid.tip_y))

  # Vector from axis to creature (in XZ plane)
  dx = cx - tendroid.center_x
  dz = cz - tendroid.center_z
  horizontal_dist = math.sqrt(dx * dx + dz * dz)

  # 3D distance from axis
  dy = cy - axis_y
  dist_from_axis = math.sqrt(horizontal_dist * horizontal_dist + dy * dy)

  # Surface distance
  surface_distance = dist_from_axis - tendroid.radius

  # Surface normal (from tendroid toward creature)
  if dist_from_axis > 1e-6:
    nx = dx / dist_from_axis
    ny = dy / dist_from_axis
    nz = dz / dist_from_axis
  else:
    nx, ny, nz = 1.0, 0.0, 0.0

  # Check if velocity is directed toward tendroid (head-on)
  velocity_mag = math.sqrt(vx * vx + vy * vy + vz * vz)
  is_head_on = False

  if velocity_mag > 1e-6:
    # Normalize velocity
    vel_norm_x = vx / velocity_mag
    vel_norm_y = vy / velocity_mag
    vel_norm_z = vz / velocity_mag

    # Dot product: negative normal (toward tendroid)
    approach_dot = -(vel_norm_x * nx + vel_norm_y * ny + vel_norm_z * nz)
    is_head_on = approach_dot >= head_on_threshold

  # Within range and approaching head-on?
  is_within = surface_distance <= zones.detection_range and is_head_on

  # Height ratio for deflection proportionality
  height_ratio = (axis_y - tendroid.base_y) / tendroid.height
  height_ratio = max(0.0, min(1.0, height_ratio))

  return ApproachResult(
    approach_type=ApproachType.HEAD_ON if is_within else ApproachType.NONE,
    distance=max(0.0, surface_distance),
    height_ratio=height_ratio,
    contact_y=axis_y,
    contact_normal=(nx, ny, nz),
    is_within_range=is_within
  )


# =============================================================================
# TEND-21: Pass-By Approach Detection
# =============================================================================

def calculate_pass_by_approach(
  creature_pos: Tuple[float, float, float],
  creature_velocity: Tuple[float, float, float],
  tendroid: TendroidGeometry,
  zones: DetectionZones,
  tangent_threshold: float = 0.5
) -> ApproachResult:
  """
  Calculate pass-by approach for lateral creature movement past tendroid.

  TEND-21 Implementation:
  - Detection circle = tendroid_radius + approach_buffer
  - Circle centered on tendroid's center line
  - Deflection based on minimum distance from creature to surface

  Args:
      creature_pos: (x, y, z) creature position
      creature_velocity: (vx, vy, vz) creature velocity
      tendroid: Tendroid cylinder geometry
      zones: Detection zone thresholds
      tangent_threshold: Threshold for tangent velocity detection

  Returns:
      ApproachResult with pass-by approach data
  """
  cx, cy, cz = creature_pos
  vx, vy, vz = creature_velocity

  # Check Y range (only detect within tendroid height)
  if cy < tendroid.base_y or cy > tendroid.tip_y:
    return ApproachResult(
      approach_type=ApproachType.NONE,
      distance=float('inf'),
      height_ratio=0.0,
      contact_y=tendroid.base_y,
      contact_normal=(0.0, 0.0, 0.0),
      is_within_range=False
    )

  # Horizontal distance in XZ plane
  dx = cx - tendroid.center_x
  dz = cz - tendroid.center_z
  horizontal_dist = math.sqrt(dx * dx + dz * dz)

  # Surface distance
  surface_distance = horizontal_dist - tendroid.radius

  # Detection circle radius
  detection_circle = zones.detection_radius

  # Check if inside detection circle
  in_circle = horizontal_dist <= detection_circle

  # Surface normal (XZ plane)
  if horizontal_dist > 1e-6:
    nx = dx / horizontal_dist
    nz = dz / horizontal_dist
  else:
    nx, nz = 1.0, 0.0

  # Check for tangential (pass-by) velocity
  velocity_mag = math.sqrt(vx * vx + vz * vz)  # XZ velocity only
  is_tangent = False

  if velocity_mag > 1e-6:
    vel_norm_x = vx / velocity_mag
    vel_norm_z = vz / velocity_mag

    # Dot product with normal (0 = perpendicular = passing by)
    normal_component = abs(vel_norm_x * nx + vel_norm_z * nz)
    is_tangent = normal_component < tangent_threshold

  is_within = in_circle and (is_tangent or velocity_mag < 1e-6)

  # Height ratio
  height_ratio = (cy - tendroid.base_y) / tendroid.height
  height_ratio = max(0.0, min(1.0, height_ratio))

  return ApproachResult(
    approach_type=ApproachType.PASS_BY if is_within else ApproachType.NONE,
    distance=max(0.0, surface_distance),
    height_ratio=height_ratio,
    contact_y=cy,
    contact_normal=(nx, 0.0, nz),
    is_within_range=is_within
  )


def detect_approach_type(
  creature_pos: Tuple[float, float, float],
  creature_velocity: Tuple[float, float, float],
  tendroid: TendroidGeometry,
  zones: DetectionZones
) -> ApproachResult:
  """
  Detect the dominant approach type for creature-tendroid interaction.

  Priority: HEAD_ON > PASS_BY > VERTICAL > NONE

  Args:
      creature_pos: (x, y, z) creature position
      creature_velocity: (vx, vy, vz) creature velocity
      tendroid: Tendroid geometry
      zones: Detection zones

  Returns:
      ApproachResult for the dominant approach type
  """
  # Try head-on first (highest priority)
  head_on = calculate_head_on_approach(
    creature_pos, creature_velocity, tendroid, zones
  )
  if head_on.approach_type == ApproachType.HEAD_ON:
    return head_on

  # Try pass-by second
  pass_by = calculate_pass_by_approach(
    creature_pos, creature_velocity, tendroid, zones
  )
  if pass_by.approach_type == ApproachType.PASS_BY:
    return pass_by

  # Try vertical last
  vertical = calculate_vertical_proximity(creature_pos, tendroid, zones)
  if vertical.approach_type == ApproachType.VERTICAL:
    return vertical

  # No approach detected
  return ApproachResult(
    approach_type=ApproachType.NONE,
    distance=float('inf'),
    height_ratio=0.0,
    contact_y=tendroid.base_y,
    contact_normal=(0.0, 0.0, 0.0),
    is_within_range=False
  )
