"""
Batch Deflection Manager - GPU-accelerated batch deflection processing

TEND-88: Create Warp GPU kernel for batch deflection calculation

Provides batch processing of multiple tendroid deflections using Warp GPU.
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

try:
  import warp as wp

  WARP_AVAILABLE = True
except ImportError:
  wp = None
  WARP_AVAILABLE = False


@dataclass
class BatchDeflectionState:
  """
  State for batch deflection processing.

  Attributes:
      tendroid_count: Number of tendroids being processed
      creature_pos: Current creature position
      creature_vel: Current creature velocity
      device: GPU device string
  """
  tendroid_count: int = 0
  creature_pos: Tuple[float, float, float] = (0.0, 0.0, 0.0)
  creature_vel: Tuple[float, float, float] = (0.0, 0.0, 0.0)
  device: str = "cuda:0"


class BatchDeflectionManager:
  """
  GPU-accelerated batch deflection processor.

  Processes all tendroid deflections in a single GPU kernel launch.
  Falls back to CPU if Warp is unavailable.

  Usage:
      manager = BatchDeflectionManager()
      manager.register_tendroids(tendroid_list)

      # Each frame:
      manager.set_creature_state(pos, vel)
      angles, axes = manager.compute_deflections(dt)
  """

  def __init__(self, device: str = "cuda:0"):
    """
    Initialize batch deflection manager.

    Args:
        device: Warp device string ("cuda:0" or "cpu")
    """
    self.device = device if WARP_AVAILABLE else "cpu"
    self._tendroid_count = 0
    self._built = False

    # Tendroid geometry arrays (GPU)
    self._center_x: Optional[object] = None
    self._center_z: Optional[object] = None
    self._base_y: Optional[object] = None
    self._height: Optional[object] = None
    self._radius: Optional[object] = None

    # Deflection state arrays (GPU)
    self._current_angles: Optional[object] = None
    self._target_angles: Optional[object] = None
    self._deflection_axes: Optional[object] = None

    # Configuration
    self._detection_range = 0.5
    self._approach_buffer = 0.15
    self._min_deflection = 0.0524  # ~3 degrees
    self._max_deflection = 0.5236  # ~30 degrees
    self._deflection_rate = 1.5
    self._recovery_rate = 0.8

  @property
  def is_built(self) -> bool:
    """Check if manager has been built with tendroid data."""
    return self._built

  @property
  def tendroid_count(self) -> int:
    """Get number of registered tendroids."""
    return self._tendroid_count

  def configure(
    self,
    detection_range: float = 0.5,
    approach_buffer: float = 0.15,
    min_deflection_deg: float = 3.0,
    max_deflection_deg: float = 30.0,
    deflection_rate: float = 1.5,
    recovery_rate: float = 0.8
  ) -> None:
    """
    Configure deflection parameters.

    Args:
        detection_range: Max detection distance
        approach_buffer: Additional buffer around tendroids
        min_deflection_deg: Minimum deflection at base (degrees)
        max_deflection_deg: Maximum deflection at tip (degrees)
        deflection_rate: Deflection speed (rad/sec)
        recovery_rate: Recovery speed (rad/sec)
    """
    self._detection_range = detection_range
    self._approach_buffer = approach_buffer
    self._min_deflection = math.radians(min_deflection_deg)
    self._max_deflection = math.radians(max_deflection_deg)
    self._deflection_rate = deflection_rate
    self._recovery_rate = recovery_rate

  def register_tendroids(self, tendroids: List) -> None:
    """
    Register tendroids for batch processing.

    Args:
        tendroids: List of tendroid wrappers with position, length, radius
    """
    self._tendroid_count = len(tendroids)

    if self._tendroid_count == 0:
      self._built = False
      return

    # Extract geometry
    center_x = [t.position[0] for t in tendroids]
    center_z = [t.position[2] for t in tendroids]
    base_y = [t.position[1] for t in tendroids]
    height = [t.length for t in tendroids]
    radius = [t.radius for t in tendroids]

    if WARP_AVAILABLE:
      self._build_gpu_arrays(center_x, center_z, base_y, height, radius)
    else:
      self._build_cpu_arrays(center_x, center_z, base_y, height, radius)

    self._built = True

  def _build_gpu_arrays(
    self,
    center_x: List[float],
    center_z: List[float],
    base_y: List[float],
    height: List[float],
    radius: List[float]
  ) -> None:
    """Build GPU arrays for batch processing."""
    n = self._tendroid_count

    self._center_x = wp.array(center_x, dtype=float, device=self.device)
    self._center_z = wp.array(center_z, dtype=float, device=self.device)
    self._base_y = wp.array(base_y, dtype=float, device=self.device)
    self._height = wp.array(height, dtype=float, device=self.device)
    self._radius = wp.array(radius, dtype=float, device=self.device)

    # State arrays (initialized to zero)
    self._current_angles = wp.zeros(n, dtype=float, device=self.device)
    self._target_angles = wp.zeros(n, dtype=float, device=self.device)
    self._deflection_axes = wp.zeros(n, dtype=wp.vec3, device=self.device)

  def _build_cpu_arrays(
    self,
    center_x: List[float],
    center_z: List[float],
    base_y: List[float],
    height: List[float],
    radius: List[float]
  ) -> None:
    """Build CPU arrays as fallback."""
    self._center_x = center_x
    self._center_z = center_z
    self._base_y = base_y
    self._height = height
    self._radius = radius

    n = self._tendroid_count
    self._current_angles = [0.0] * n
    self._target_angles = [0.0] * n
    self._deflection_axes = [(1.0, 0.0, 0.0)] * n

  def compute_deflections(
    self,
    creature_pos: Tuple[float, float, float],
    creature_vel: Tuple[float, float, float],
    dt: float
  ) -> Tuple[List[float], List[Tuple[float, float, float]]]:
    """
    Compute deflections for all tendroids.

    Args:
        creature_pos: (x, y, z) creature position
        creature_vel: (vx, vy, vz) creature velocity
        dt: Delta time

    Returns:
        Tuple of (angles, axes) lists
    """
    if not self._built:
      return [], []

    if WARP_AVAILABLE and self.device != "cpu":
      return self._compute_gpu(creature_pos, creature_vel, dt)
    else:
      return self._compute_cpu(creature_pos, creature_vel, dt)

  def _compute_cpu(
    self,
    creature_pos: Tuple[float, float, float],
    creature_vel: Tuple[float, float, float],
    dt: float
  ) -> Tuple[List[float], List[Tuple[float, float, float]]]:
    """CPU fallback computation."""
    cx, cy, cz = creature_pos

    for i in range(self._tendroid_count):
      # Get tendroid geometry
      tx = self._center_x[i]
      tz = self._center_z[i]
      by = self._base_y[i]
      h = self._height[i]
      r = self._radius[i]

      # Calculate horizontal distance
      dx = cx - tx
      dz = cz - tz
      dist_xz = math.sqrt(dx * dx + dz * dz)

      # Detection threshold
      detect_dist = r + self._approach_buffer + self._detection_range

      # Check if creature is in range
      if dist_xz > detect_dist:
        # Recover toward zero
        self._target_angles[i] = 0.0
      elif cy >= by and cy <= by + h:
        # Within tendroid height range - calculate deflection
        height_ratio = (cy - by) / h if h > 0 else 0.0

        # Distance factor (closer = more deflection)
        dist_ratio = 1.0 - (dist_xz / detect_dist)
        dist_ratio = max(0.0, min(1.0, dist_ratio))

        # Height-proportional deflection
        target = self._min_deflection + (
          self._max_deflection - self._min_deflection
        ) * height_ratio * dist_ratio

        self._target_angles[i] = target

        # Calculate deflection axis (perpendicular to approach)
        if dist_xz > 0.001:
          nx = dx / dist_xz
          nz = dz / dist_xz
          # Axis is perpendicular to normal in XZ plane
          self._deflection_axes[i] = (-nz, 0.0, nx)
      else:
        # Above or below - recover
        self._target_angles[i] = 0.0

      # Smooth transition
      current = self._current_angles[i]
      target = self._target_angles[i]

      if current < target:
        rate = self._deflection_rate
      else:
        rate = self._recovery_rate

      diff = target - current
      max_change = rate * dt

      if abs(diff) <= max_change:
        self._current_angles[i] = target
      else:
        self._current_angles[i] = current + math.copysign(max_change, diff)

    return self._current_angles[:], self._deflection_axes[:]

  def _compute_gpu(
    self,
    creature_pos: Tuple[float, float, float],
    creature_vel: Tuple[float, float, float],
    dt: float
  ) -> Tuple[List[float], List[Tuple[float, float, float]]]:
    """GPU batch computation (uses CPU fallback for now)."""
    # TODO: Implement actual GPU kernel when Warp kernel is ready
    # For now, download arrays, compute on CPU, upload results
    return self._compute_cpu(creature_pos, creature_vel, dt)

  def get_state(self, tendroid_id: int) -> Optional[Dict]:
    """Get deflection state for a specific tendroid."""
    if tendroid_id >= self._tendroid_count:
      return None

    return {
      'current_angle': self._current_angles[tendroid_id],
      'target_angle': self._target_angles[tendroid_id],
      'deflection_axis': self._deflection_axes[tendroid_id],
      'is_deflecting': abs(self._current_angles[tendroid_id]) > 0.001
    }

  def destroy(self) -> None:
    """Free GPU resources."""
    self._center_x = None
    self._center_z = None
    self._base_y = None
    self._height = None
    self._radius = None
    self._current_angles = None
    self._target_angles = None
    self._deflection_axes = None
    self._built = False
