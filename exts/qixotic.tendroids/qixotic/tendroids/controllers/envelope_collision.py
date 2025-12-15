"""
Envelope Collision Detection - Geometric collision algorithms

Pure geometry functions for detecting collisions with the creature
envelope capsule. These functions work without PhysX for unit testing.

Implements TEND-14: Unit tests for envelope collision detection.
"""

import math
from dataclasses import dataclass
from typing import Tuple


@dataclass
class Vec3:
  """Simple 3D vector for collision calculations."""
  x: float = 0.0
  y: float = 0.0
  z: float = 0.0

  def __add__(self, other: 'Vec3') -> 'Vec3':
    return Vec3(self.x + other.x, self.y + other.y, self.z + other.z)

  def __sub__(self, other: 'Vec3') -> 'Vec3':
    return Vec3(self.x - other.x, self.y - other.y, self.z - other.z)

  def __mul__(self, scalar: float) -> 'Vec3':
    return Vec3(self.x * scalar, self.y * scalar, self.z * scalar)

  def __truediv__(self, scalar: float) -> 'Vec3':
    return Vec3(self.x / scalar, self.y / scalar, self.z / scalar)

  def dot(self, other: 'Vec3') -> float:
    return self.x * other.x + self.y * other.y + self.z * other.z

  def length(self) -> float:
    return math.sqrt(self.dot(self))

  def length_squared(self) -> float:
    return self.dot(self)

  def normalized(self) -> 'Vec3':
    length = self.length()
    if length < 1e-8:
      return Vec3(0, 0, 0)
    return self / length

  def cross(self, other: 'Vec3') -> 'Vec3':
    return Vec3(
      self.y * other.z - self.z * other.y,
      self.z * other.x - self.x * other.z,
      self.x * other.y - self.y * other.x
    )


@dataclass
class Capsule:
  """
  Capsule collision shape.

  Defined by center position, axis direction, half-height, and radius.
  The capsule extends along the axis from center - axis*half_height
  to center + axis*half_height, with hemispherical caps of given radius.
  """
  center: Vec3
  axis: Vec3  # Unit vector along capsule length
  half_height: float
  radius: float

  @property
  def point_a(self) -> Vec3:
    """Bottom endpoint of cylinder axis."""
    return self.center - self.axis * self.half_height

  @property
  def point_b(self) -> Vec3:
    """Top endpoint of cylinder axis."""
    return self.center + self.axis * self.half_height

  @property
  def total_length(self) -> float:
    """Total length including hemispherical caps."""
    return 2 * self.half_height + 2 * self.radius


@dataclass
class CollisionResult:
  """Result of a collision detection query."""
  hit: bool
  distance: float = 0.0  # Distance from point to surface (negative = inside)
  contact_point: Vec3 = None  # Closest point on capsule surface
  contact_normal: Vec3 = None  # Normal pointing outward from capsule
  contact_type: str = "none"  # "cylinder", "cap_a", "cap_b", "none"


def closest_point_on_segment(point: Vec3, seg_a: Vec3, seg_b: Vec3) -> Tuple[Vec3, float]:
  """
  Find closest point on line segment to a given point.

  Args:
      point: Query point
      seg_a: Segment start
      seg_b: Segment end

  Returns:
      Tuple of (closest_point, parameter_t) where t in [0,1]
  """
  ab = seg_b - seg_a
  ab_length_sq = ab.length_squared()

  if ab_length_sq < 1e-10:
    # Degenerate segment
    return seg_a, 0.0

  # Project point onto line
  ap = point - seg_a
  t = ap.dot(ab) / ab_length_sq

  # Clamp to segment
  t = max(0.0, min(1.0, t))

  closest = seg_a + ab * t
  return closest, t


def point_capsule_collision(
  point: Vec3,
  capsule: Capsule,
  contact_offset: float = 0.0
) -> CollisionResult:
  """
  Test collision between a point and a capsule.

  The effective radius is capsule.radius + contact_offset.

  Args:
      point: Query point position
      capsule: Capsule collision shape
      contact_offset: Additional offset for early contact detection

  Returns:
      CollisionResult with hit status and contact info
  """
  effective_radius = capsule.radius + contact_offset

  # Find closest point on capsule axis segment
  closest_on_axis, t = closest_point_on_segment(
    point, capsule.point_a, capsule.point_b
  )

  # Vector from axis to point
  to_point = point - closest_on_axis
  distance_to_axis = to_point.length()

  # Distance from surface (negative = inside)
  distance_to_surface = distance_to_axis - effective_radius

  # Determine contact type
  if t <= 0.0:
    contact_type = "cap_a"
  elif t >= 1.0:
    contact_type = "cap_b"
  else:
    contact_type = "cylinder"

  # Calculate contact normal (outward from capsule)
  if distance_to_axis > 1e-8:
    contact_normal = to_point.normalized()
  else:
    # Point is on axis - use arbitrary perpendicular
    contact_normal = Vec3(1, 0, 0)
    if abs(capsule.axis.x) > 0.9:
      contact_normal = Vec3(0, 1, 0)

  # Contact point on surface
  contact_point = closest_on_axis + contact_normal * effective_radius

  return CollisionResult(
    hit=(distance_to_surface <= 0),
    distance=distance_to_surface,
    contact_point=contact_point,
    contact_normal=contact_normal,
    contact_type=contact_type
  )


def sphere_capsule_collision(
  sphere_center: Vec3,
  sphere_radius: float,
  capsule: Capsule,
  contact_offset: float = 0.0
) -> CollisionResult:
  """
  Test collision between a sphere and a capsule.

  This is equivalent to point-capsule with expanded radius.

  Args:
      sphere_center: Center of sphere
      sphere_radius: Radius of sphere
      capsule: Capsule collision shape
      contact_offset: Additional offset for early contact detection

  Returns:
      CollisionResult with hit status and contact info
  """
  # Sphere-capsule is point-capsule with combined radii
  effective_offset = sphere_radius + contact_offset
  return point_capsule_collision(sphere_center, capsule, effective_offset)


def calculate_approach_velocity(
  object_pos: Vec3,
  object_vel: Vec3,
  capsule: Capsule
) -> float:
  """
  Calculate how fast an object is approaching the capsule.

  Positive = moving toward capsule
  Negative = moving away from capsule

  Args:
      object_pos: Object position
      object_vel: Object velocity vector
      capsule: Capsule collision shape

  Returns:
      Approach velocity (positive = approaching)
  """
  # Find direction from object to closest point on capsule
  closest_on_axis, _ = closest_point_on_segment(
    object_pos, capsule.point_a, capsule.point_b
  )

  to_capsule = closest_on_axis - object_pos
  distance = to_capsule.length()

  if distance < 1e-8:
    return 0.0

  direction_to_capsule = to_capsule / distance

  # Dot product gives approach velocity
  return object_vel.dot(direction_to_capsule)


def is_glancing_contact(
  collision: CollisionResult,
  object_velocity: Vec3,
  glancing_threshold: float = 0.5
) -> bool:
  """
  Determine if a contact is a glancing blow.

  A glancing contact has the velocity mostly tangent to the surface.

  Args:
      collision: Collision result with contact normal
      object_velocity: Object velocity at time of contact
      glancing_threshold: Cos(angle) threshold (0.5 = 60 degrees)

  Returns:
      True if contact is glancing
  """
  if not collision.hit or collision.contact_normal is None:
    return False

  speed = object_velocity.length()
  if speed < 1e-8:
    return False

  vel_normalized = object_velocity.normalized()

  # Dot product with normal gives cos(angle to surface)
  # 0 = perfectly tangent, 1 = head-on
  normal_component = abs(vel_normalized.dot(collision.contact_normal))

  return normal_component < glancing_threshold


def is_head_on_contact(
  collision: CollisionResult,
  object_velocity: Vec3,
  head_on_threshold: float = 0.7
) -> bool:
  """
  Determine if a contact is head-on.

  A head-on contact has the velocity mostly perpendicular to surface.

  Args:
      collision: Collision result with contact normal
      object_velocity: Object velocity at time of contact
      head_on_threshold: Cos(angle) threshold (0.7 = ~45 degrees)

  Returns:
      True if contact is head-on
  """
  if not collision.hit or collision.contact_normal is None:
    return False

  speed = object_velocity.length()
  if speed < 1e-8:
    return False

  vel_normalized = object_velocity.normalized()
  normal_component = abs(vel_normalized.dot(collision.contact_normal))

  return normal_component >= head_on_threshold
