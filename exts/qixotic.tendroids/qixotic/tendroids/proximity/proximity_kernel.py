"""
Proximity Kernel Controller

Orchestrates GPU-accelerated proximity detection between creatures and tendroids.
Manages kernel launches, data transfers, and result retrieval.

TEND-16: Implement proximity kernel for single tendroid
TEND-2: Proximity Detection System (Epic)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import carb
import warp as wp

from .proximity_config import ApproachParameters, DEFAULT_APPROACH_PARAMS
# Import kernels from helper
from .proximity_kernel_helper import (compute_zone_based_force_kernel, horizontal_distance_kernel)


@dataclass
class ProximityResult:
  """Result from single tendroid proximity check."""

  creature_idx: int
  tendroid_idx: int
  surface_distance: float
  zone: str
  force: Tuple[float, float, float]

  @property
  def is_contact(self) -> bool:
    return self.zone == "contact"

  @property
  def is_detected(self) -> bool:
    return self.zone != "idle"


class SingleTendroidProximity:
  """
  Proximity detector for single creature against single tendroid.

  Provides GPU-accelerated distance calculation and force computation
  using horizontal (XZ plane) distance to tendroid surface.

  TEND-16: Single tendroid proximity kernel implementation

  Usage:
      detector = SingleTendroidProximity()
      detector.configure(tendroid_pos, tendroid_radius)

      # Each frame
      result = detector.check_proximity(creature_pos)
      if result.is_contact:
          apply_shock(result.force)
  """

  def __init__(
    self,
    approach_params: Optional[ApproachParameters] = None,
    device: str = "cuda:0"
  ):
    """
    Initialize proximity detector.

    Args:
        approach_params: Distance thresholds for zones
        device: GPU device to use
    """
    self._params = approach_params or DEFAULT_APPROACH_PARAMS
    self._device = device

    # Tendroid configuration
    self._tendroid_pos: Optional[Tuple[float, float, float]] = None
    self._tendroid_radius: float = 0.1

    # Force configuration
    self._force_strengths = {
      "contact": 10.0,
      "recovering": 5.0,
      "approaching": 2.0,
      "detected": 0.5,
    }

    # GPU arrays (lazy allocation)
    self._creature_pos_gpu: Optional[wp.array] = None
    self._distances_gpu: Optional[wp.array] = None
    self._directions_gpu: Optional[wp.array] = None
    self._forces_gpu: Optional[wp.array] = None
    self._zones_gpu: Optional[wp.array] = None

    self._configured = False

  def configure(
    self,
    tendroid_position: Tuple[float, float, float],
    tendroid_radius: float,
    force_strengths: Optional[Dict[str, float]] = None
  ):
    """
    Configure the tendroid to detect proximity against.

    Args:
        tendroid_position: (x, y, z) center position
        tendroid_radius: Cylinder radius
        force_strengths: Optional override for zone force magnitudes
    """
    self._tendroid_pos = tendroid_position
    self._tendroid_radius = tendroid_radius

    if force_strengths:
      self._force_strengths.update(force_strengths)

    self._configured = True
    carb.log_info(
      f"[SingleTendroidProximity] Configured: pos={tendroid_position}, "
      f"radius={tendroid_radius}"
    )

  def update_tendroid_position(self, position: Tuple[float, float, float]):
    """Update tendroid position without full reconfiguration."""
    self._tendroid_pos = position

  def check_proximity(
    self,
    creature_position: Tuple[float, float, float]
  ) -> ProximityResult:
    """
    Check proximity for single creature position.

    TEND-72: Uses horizontal distance calculation
    TEND-73: Computes repulsion force vector

    Args:
        creature_position: (x, y, z) creature center

    Returns:
        ProximityResult with distance, zone, and force
    """
    if not self._configured:
      raise RuntimeError("Detector not configured - call configure() first")

    # Allocate single-element GPU arrays
    self._ensure_arrays_allocated(1)

    # Copy creature position to GPU
    self._creature_pos_gpu = wp.array(
      [creature_position], dtype=wp.vec3, device=self._device
    )

    tendroid_vec = wp.vec3(
      self._tendroid_pos[0],
      self._tendroid_pos[1],
      self._tendroid_pos[2]
    )

    # Launch horizontal distance kernel (TEND-72)
    wp.launch(
      kernel=horizontal_distance_kernel,
      dim=1,
      inputs=[
        self._creature_pos_gpu,
        tendroid_vec,
        self._tendroid_radius,
        self._distances_gpu,
        self._directions_gpu,
      ],
      device=self._device
    )

    # Launch zone-based force kernel (TEND-73)
    wp.launch(
      kernel=compute_zone_based_force_kernel,
      dim=1,
      inputs=[
        self._distances_gpu,
        self._directions_gpu,
        self._params.approach_epsilon,
        self._params.approach_minimum,
        self._params.warning_distance,
        self._params.detection_radius,
        self._force_strengths["contact"],
        self._force_strengths["recovering"],
        self._force_strengths["approaching"],
        self._force_strengths["detected"],
        self._forces_gpu,
        self._zones_gpu,
      ],
      device=self._device
    )

    # Sync and retrieve results
    wp.synchronize()

    distance = float(self._distances_gpu.numpy()[0])
    zone_idx = int(self._zones_gpu.numpy()[0])
    force_vec = self._forces_gpu.numpy()[0]

    zone_names = ["contact", "recovering", "approaching", "detected", "idle"]
    zone_name = zone_names[zone_idx] if zone_idx < len(zone_names) else "idle"

    return ProximityResult(
      creature_idx=0,
      tendroid_idx=0,
      surface_distance=distance,
      zone=zone_name,
      force=(float(force_vec[0]), float(force_vec[1]), float(force_vec[2]))
    )

  def check_proximity_batch(
    self,
    creature_positions: List[Tuple[float, float, float]]
  ) -> List[ProximityResult]:
    """
    Check proximity for multiple creature positions.

    GPU-accelerated batch processing for efficiency.

    Args:
        creature_positions: List of (x, y, z) positions

    Returns:
        List of ProximityResult for each creature
    """
    if not self._configured:
      raise RuntimeError("Detector not configured - call configure() first")

    count = len(creature_positions)
    if count == 0:
      return []

    self._ensure_arrays_allocated(count)

    # Copy positions to GPU
    self._creature_pos_gpu = wp.array(
      creature_positions, dtype=wp.vec3, device=self._device
    )

    tendroid_vec = wp.vec3(
      self._tendroid_pos[0],
      self._tendroid_pos[1],
      self._tendroid_pos[2]
    )

    # Launch distance kernel
    wp.launch(
      kernel=horizontal_distance_kernel,
      dim=count,
      inputs=[
        self._creature_pos_gpu,
        tendroid_vec,
        self._tendroid_radius,
        self._distances_gpu,
        self._directions_gpu,
      ],
      device=self._device
    )

    # Launch force kernel
    wp.launch(
      kernel=compute_zone_based_force_kernel,
      dim=count,
      inputs=[
        self._distances_gpu,
        self._directions_gpu,
        self._params.approach_epsilon,
        self._params.approach_minimum,
        self._params.warning_distance,
        self._params.detection_radius,
        self._force_strengths["contact"],
        self._force_strengths["recovering"],
        self._force_strengths["approaching"],
        self._force_strengths["detected"],
        self._forces_gpu,
        self._zones_gpu,
      ],
      device=self._device
    )

    wp.synchronize()

    # Retrieve results
    distances = self._distances_gpu.numpy()
    zones = self._zones_gpu.numpy()
    forces = self._forces_gpu.numpy()

    zone_names = ["contact", "recovering", "approaching", "detected", "idle"]

    results = []
    for i in range(count):
      zone_idx = int(zones[i])
      zone_name = zone_names[zone_idx] if zone_idx < len(zone_names) else "idle"

      results.append(ProximityResult(
        creature_idx=i,
        tendroid_idx=0,
        surface_distance=float(distances[i]),
        zone=zone_name,
        force=(float(forces[i][0]), float(forces[i][1]), float(forces[i][2]))
      ))

    return results

  def _ensure_arrays_allocated(self, count: int):
    """Allocate GPU arrays if needed."""
    needs_alloc = (
      self._distances_gpu is None or
      self._distances_gpu.shape[0] != count
    )

    if needs_alloc:
      self._distances_gpu = wp.zeros(count, dtype=float, device=self._device)
      self._directions_gpu = wp.zeros(count, dtype=wp.vec3, device=self._device)
      self._forces_gpu = wp.zeros(count, dtype=wp.vec3, device=self._device)
      self._zones_gpu = wp.zeros(count, dtype=int, device=self._device)

  def destroy(self):
    """Release GPU resources."""
    self._creature_pos_gpu = None
    self._distances_gpu = None
    self._directions_gpu = None
    self._forces_gpu = None
    self._zones_gpu = None
    self._configured = False
