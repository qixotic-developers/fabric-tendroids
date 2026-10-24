"""
Deflection Calculation Helpers

TEND-22: Deflection proportionality system (height-based)
TEND-23: Surface normals for deflection direction

Pure calculation functions for deflection amounts and directions.
"""

import math
from dataclasses import dataclass
from typing import Tuple

from .approach_calculators import ApproachResult, TendroidGeometry
from .deflection_config import ApproachType, DeflectionLimits


@dataclass
class DeflectionResult:
  """Result of deflection calculation."""
  deflection_angle: float  # Radians
  deflection_direction: Tuple[float, float, float]  # Unit vector
  deflection_axis: Tuple[float, float, float]  # Rotation axis
  apply_deflection: bool  # True if deflection should be applied


# =============================================================================
# TEND-22: Height-Based Deflection Proportionality
# =============================================================================

def calculate_height_ratio(contact_y: float, base_y: float, height: float) -> float:
  """
  Calculate normalized height ratio along tendroid.

  TEND-22: height_ratio = (contact_y - base_y) / cylinder_height

  Args:
      contact_y: Y-coordinate of contact point
      base_y: Y-coordinate of tendroid base
      height: Total height of tendroid cylinder

  Returns:
      0.0 at base, 1.0 at tip
  """
  if height <= 0:
    return 0.0
  ratio = (contact_y - base_y) / height
  return max(0.0, min(1.0, ratio))


def lerp_deflection(
  min_deflection: float,
  max_deflection: float,
  height_ratio: float
) -> float:
  """
  Linear interpolation of deflection based on height.

  TEND-22 Formula:
      deflection = lerp(minimum_deflection, maximum_deflection, height_ratio)

  Args:
      min_deflection: Minimum bend angle at base (radians)
      max_deflection: Maximum bend angle at tip (radians)
      height_ratio: 0.0 (base) to 1.0 (tip)

  Returns:
      Interpolated deflection angle in radians
  """
  t = max(0.0, min(1.0, height_ratio))
  return min_deflection + t * (max_deflection - min_deflection)


def calculate_proportional_deflection(
  approach: ApproachResult,
  limits: DeflectionLimits,
  detection_range: float = 31.0
) -> float:
  """
  Calculate deflection angle proportional to contact height and distance.

  TEND-22: Full implementation with distance falloff.

  Deflection is:
  - Proportional to height (higher = more deflection)
  - Inversely proportional to distance (closer = more deflection)

  Args:
      approach: ApproachResult with height_ratio and distance
      limits: DeflectionLimits configuration
      detection_range: Maximum detection distance for scaling

  Returns:
      Deflection angle in radians
  """
  if not approach.is_within_range:
    return 0.0

  # Height-based interpolation
  base_deflection = lerp_deflection(
    limits.minimum_deflection,
    limits.maximum_deflection,
    approach.height_ratio
  )

  # Distance-based scaling (inverse relationship)
  # At distance 0, full deflection (factor = 1.0)
  # At detection_range, minimal deflection (factor ~= 0.1)
  if approach.distance <= 0:
    distance_factor = 1.0
  else:
    # Normalize distance to 0-1 range based on detection_range
    normalized_dist = min(approach.distance / detection_range, 1.0)
    # Smooth falloff: 1.0 at distance=0, ~0.1 at distance=range
    distance_factor = (1.0 - normalized_dist) ** 0.5

  return base_deflection * distance_factor


# =============================================================================
# TEND-23: Surface Normal Calculations
# =============================================================================

def calculate_cylinder_normal(
  point: Tuple[float, float, float],
  tendroid: TendroidGeometry
) -> Tuple[float, float, float]:
  """
  Calculate surface normal at a point on tendroid cylinder.

  TEND-23: Normal at contact point on tendroid cylinder.

  For cylindrical surface, normal is radial from center axis
  in XZ plane (Y component is 0 for vertical cylinder).

  Args:
      point: (x, y, z) point near cylinder surface
      tendroid: TendroidGeometry

  Returns:
      (nx, ny, nz) unit normal vector pointing outward
  """
  px, py, pz = point

  # Vector from cylinder axis to point (XZ plane)
  dx = px - tendroid.center_x
  dz = pz - tendroid.center_z

  magnitude = math.sqrt(dx * dx + dz * dz)

  if magnitude < 1e-6:
    # Point on axis, use default normal
    return (1.0, 0.0, 0.0)

  # Normalized radial direction
  nx = dx / magnitude
  nz = dz / magnitude

  return (nx, 0.0, nz)


def calculate_deflection_direction(
  contact_normal: Tuple[float, float, float]
) -> Tuple[float, float, float]:
  """
  Calculate deflection direction from contact normal.

  TEND-23: Deflection direction = opposite of contact normal.
  Tendroid bends away from the creature.

  Args:
      contact_normal: Surface normal at contact point

  Returns:
      Unit vector for deflection direction
  """
  nx, ny, nz = contact_normal
  return (-nx, -ny, -nz)


def calculate_bend_axis(
  deflection_direction: Tuple[float, float, float],
  up_vector: Tuple[float, float, float] = (0.0, 1.0, 0.0)
) -> Tuple[float, float, float]:
  """
  Calculate rotation axis for bending.

  The bend axis is perpendicular to both the deflection direction
  and the tendroid's up vector. This creates a "bowing" effect.

  Args:
      deflection_direction: Direction tendroid should bend
      up_vector: Tendroid's vertical axis (default Y-up)

  Returns:
      Unit rotation axis for bending transform
  """
  dx, dy, dz = deflection_direction
  ux, uy, uz = up_vector

  # Cross product: up × deflection = bend axis
  ax = uy * dz - uz * dy
  ay = uz * dx - ux * dz
  az = ux * dy - uy * dx

  magnitude = math.sqrt(ax * ax + ay * ay + az * az)

  if magnitude < 1e-6:
    # Parallel vectors, use arbitrary perpendicular
    return (0.0, 0.0, 1.0)

  return (ax / magnitude, ay / magnitude, az / magnitude)


def calculate_deflection(
  approach: ApproachResult,
  tendroid: TendroidGeometry,
  limits: DeflectionLimits,
  detection_range: float = 31.0
) -> DeflectionResult:
  """
  Calculate complete deflection result for approach.

  TEND-22 + TEND-23: Combined height-based deflection with proper direction.

  Args:
      approach: ApproachResult from approach detection
      tendroid: Tendroid geometry
      limits: Deflection limits configuration
      detection_range: Maximum detection distance for scaling

  Returns:
      DeflectionResult with angle, direction, and axis
  """
  # No deflection if not within range
  if not approach.is_within_range or approach.approach_type == ApproachType.NONE:
    return DeflectionResult(
      deflection_angle=0.0,
      deflection_direction=(0.0, 0.0, 0.0),
      deflection_axis=(0.0, 0.0, 1.0),
      apply_deflection=False
    )

  # Calculate proportional deflection angle
  deflection_angle = calculate_proportional_deflection(
    approach, limits, detection_range
  )

  # Calculate directions
  deflection_dir = calculate_deflection_direction(approach.contact_normal)
  bend_axis = calculate_bend_axis(deflection_dir)

  return DeflectionResult(
    deflection_angle=deflection_angle,
    deflection_direction=deflection_dir,
    deflection_axis=bend_axis,
    apply_deflection=deflection_angle > 0.001  # Threshold for visible effect
  )


def smooth_deflection_transition(
  current_angle: float,
  target_angle: float,
  dt: float,
  deflection_rate: float,
  recovery_rate: float
) -> float:
  """
  Smoothly transition between deflection angles.

  Uses different rates for deflecting vs recovering.

  Args:
      current_angle: Current deflection angle
      target_angle: Target deflection angle
      dt: Delta time in seconds
      deflection_rate: Rate when increasing deflection
      recovery_rate: Rate when decreasing deflection

  Returns:
      New deflection angle after transition
  """
  diff = target_angle - current_angle

  if abs(diff) < 0.001:
    return target_angle

  # Use appropriate rate
  rate = deflection_rate if diff > 0 else recovery_rate
  max_change = rate * dt

  if abs(diff) <= max_change:
    return target_angle

  return current_angle + math.copysign(max_change, diff)
