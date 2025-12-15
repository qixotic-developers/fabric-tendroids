"""
Hash Grid Helper Functions

Utility functions for grid operations, position updates, and neighbor queries.

TEND-66: Implement grid rebuild on position updates
TEND-67: Integrate HashGrid with simulation loop
"""

from typing import List, Optional, Tuple

import carb
import warp as wp


@wp.kernel
def copy_positions_kernel(
  src: wp.array(dtype=wp.vec3),
  dst: wp.array(dtype=wp.vec3),
  offset: int
):
  """Copy positions from source to destination with offset."""
  tid = wp.tid()
  dst[offset + tid] = src[tid]


@wp.kernel
def find_neighbors_kernel(
  grid: wp.uint64,
  query_points: wp.array(dtype=wp.vec3),
  all_points: wp.array(dtype=wp.vec3),
  radius: float,
  neighbor_counts: wp.array(dtype=int),
  neighbor_indices: wp.array(dtype=int),
  max_neighbors: int
):
  """
  Find neighbors within radius for each query point.

  Args:
      grid: Hash grid ID
      query_points: Points to query from
      all_points: All points in the grid
      radius: Search radius
      neighbor_counts: Output count per query point
      neighbor_indices: Output neighbor indices (flattened)
      max_neighbors: Maximum neighbors per point
  """
  tid = wp.tid()
  query = query_points[tid]

  count = int(0)
  base_idx = tid * max_neighbors

  # Query hash grid for neighbors
  query_result = wp.hash_grid_query(grid, query, radius)

  for idx in query_result:
    if count < max_neighbors:
      # Calculate actual distance
      neighbor_pos = all_points[idx]
      diff = query - neighbor_pos
      dist_sq = wp.dot(diff, diff)

      if dist_sq <= radius * radius:
        neighbor_indices[base_idx + count] = idx
        count = count + 1

  neighbor_counts[tid] = count


@wp.kernel
def compute_distances_kernel(
  query_points: wp.array(dtype=wp.vec3),
  target_points: wp.array(dtype=wp.vec3),
  distances: wp.array(dtype=float)
):
  """
  Compute distances between corresponding query and target points.

  Args:
      query_points: Source points
      target_points: Target points
      distances: Output distances
  """
  tid = wp.tid()
  diff = query_points[tid] - target_points[tid]
  distances[tid] = wp.length(diff)


@wp.kernel
def compute_closest_distances_kernel(
  grid: wp.uint64,
  query_points: wp.array(dtype=wp.vec3),
  all_points: wp.array(dtype=wp.vec3),
  radius: float,
  closest_distances: wp.array(dtype=float),
  closest_indices: wp.array(dtype=int)
):
  """
  Find closest point and distance for each query point.

  Args:
      grid: Hash grid ID
      query_points: Points to query from
      all_points: All points in the grid
      radius: Search radius
      closest_distances: Output closest distance per query
      closest_indices: Output closest point index per query
  """
  tid = wp.tid()
  query = query_points[tid]

  min_dist = radius * 2.0  # Start with large value
  min_idx = int(-1)

  query_result = wp.hash_grid_query(grid, query, radius)

  for idx in query_result:
    neighbor_pos = all_points[idx]
    diff = query - neighbor_pos
    dist = wp.length(diff)

    if dist < min_dist:
      min_dist = dist
      min_idx = idx

  closest_distances[tid] = min_dist
  closest_indices[tid] = min_idx


def combine_position_arrays(
  creatures_gpu: Optional[wp.array],
  tendroids_gpu: Optional[wp.array],
  device: str = "cuda:0"
) -> Tuple[Optional[wp.array], int, int]:
  """
  Combine creature and tendroid positions into single array.

  Args:
      creatures_gpu: Creature position array on GPU
      tendroids_gpu: Tendroid position array on GPU
      device: Target device

  Returns:
      Tuple of (combined_array, creature_start_idx, tendroid_start_idx)
  """
  creature_count = creatures_gpu.shape[0] if creatures_gpu is not None else 0
  tendroid_count = tendroids_gpu.shape[0] if tendroids_gpu is not None else 0
  total = creature_count + tendroid_count

  if total == 0:
    return None, 0, 0

  combined = wp.zeros(total, dtype=wp.vec3, device=device)

  creature_start = 0
  tendroid_start = creature_count

  if creatures_gpu is not None and creature_count > 0:
    wp.launch(
      kernel=copy_positions_kernel,
      dim=creature_count,
      inputs=[creatures_gpu, combined, 0],
      device=device
    )

  if tendroids_gpu is not None and tendroid_count > 0:
    wp.launch(
      kernel=copy_positions_kernel,
      dim=tendroid_count,
      inputs=[tendroids_gpu, combined, tendroid_start],
      device=device
    )

  return combined, creature_start, tendroid_start


def update_positions_from_list(
  positions: List[Tuple[float, float, float]],
  existing_gpu: Optional[wp.array],
  device: str = "cuda:0"
) -> wp.array:
  """
  Update GPU array from CPU position list.

  Args:
      positions: New positions from CPU
      existing_gpu: Existing GPU array (for size validation)
      device: Target device

  Returns:
      Updated GPU array
  """
  if existing_gpu is not None and len(positions) != existing_gpu.shape[0]:
    carb.log_warn(
      f"[HashGridHelper] Position count changed: {existing_gpu.shape[0]} -> {len(positions)}"
    )

  return wp.array(positions, dtype=wp.vec3, device=device)
