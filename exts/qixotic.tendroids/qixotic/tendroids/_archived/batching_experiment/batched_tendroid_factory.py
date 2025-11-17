"""
Factory for creating Tendroids with size-class batch metadata

Creates Tendroids organized into size classes for batched rendering.
"""

import random
import carb
from ..core.tendroid import Tendroid
from ..core.size_classes import (
  SIZE_CLASSES,
  distribute_across_classes,
  get_random_radius_for_class
)


class BatchedTendroidFactory:
  """
  Creates Tendroids with size-class organization for batched rendering.
  
  Distributes Tendroids across three size classes (SMALL, MEDIUM, LARGE)
  and tags each with batch metadata for efficient GPU processing.
  """
  
  @staticmethod
  def create_batch(
    stage,
    count: int = 15,
    spawn_area: tuple = (200, 200),
    radius_range: tuple = (8, 12),
    num_segments: int = 16
  ):
    """
    Create a batch of Tendroids with size-class organization.
    
    Args:
        stage: USD stage
        count: Number of Tendroids to create
        spawn_area: (width, depth) of spawning area
        radius_range: Ignored - uses size class ranges instead
        num_segments: Segments per Tendroid
    
    Returns:
        List of created Tendroid instances
    """
    # Distribute across size classes
    distribution = distribute_across_classes(count)
    
    carb.log_info(
      f"[BatchedTendroidFactory] Creating {count} Tendroids in size-class batches"
    )
    carb.log_info(
      f"[BatchedTendroidFactory] Size distribution: "
      f"S:{distribution['SMALL']}, M:{distribution['MEDIUM']}, L:{distribution['LARGE']}"
    )
    
    tendroids = []
    tendroid_index = 0
    
    # Create Tendroids for each size class
    for class_name in ['SMALL', 'MEDIUM', 'LARGE']:
      class_count = distribution[class_name]
      if class_count == 0:
        continue
      
      size_class = SIZE_CLASSES[class_name]
      
      for _ in range(class_count):
        # Random radius within size class range
        radius = get_random_radius_for_class(class_name)
        
        # Random position in spawn area
        position = BatchedTendroidFactory._get_random_position(
          spawn_area, tendroids, radius
        )
        
        # Create Tendroid
        tendroid = Tendroid(
          name=f"Tendroid_{tendroid_index:02d}_{class_name}",
          position=position,
          radius=radius,
          length=100.0,  # Standard length
          num_segments=size_class.num_segments
        )
        
        # Add batch metadata
        tendroid.batch_metadata = {
          'size_class': class_name,
          'batch_index': len(tendroids),
          'class_radius': size_class.get_representative_radius()
        }
        
        # Build in scene using create() method
        if tendroid.create(stage):
          tendroids.append(tendroid)
          tendroid_index += 1
        else:
          carb.log_warn(
            f"[BatchedTendroidFactory] Failed to build {tendroid.name}"
          )
    
    carb.log_info(
      f"[BatchedTendroidFactory] Created {len(tendroids)} Tendroids"
    )
    
    return tendroids
  
  @staticmethod
  def _get_random_position(
    spawn_area: tuple,
    existing_tendroids: list,
    radius: float
  ) -> tuple:
    """
    Get random position with collision avoidance.
    
    Args:
        spawn_area: (width, depth) bounds
        existing_tendroids: Already placed Tendroids
        radius: Radius of Tendroid being placed
    
    Returns:
        (x, y, z) position tuple
    """
    global x, y, z
    width, depth = spawn_area
    min_separation = 20.0  # Minimum distance between Tendroids
    
    for attempt in range(200):
      x = random.uniform(-width/2, width/2)
      z = random.uniform(-depth/2, depth/2)
      y = 0.0  # Ground level
      
      position = (x, y, z)
      
      # Check collision with existing Tendroids
      if BatchedTendroidFactory._is_valid_position(
        position, existing_tendroids, min_separation
      ):
        return position
    
    # Fallback: return position anyway (better than failing)
    carb.log_warn(
      f"[BatchedTendroidFactory] Could not find collision-free position "
      f"after 200 attempts"
    )
    return x, y, z
  
  @staticmethod
  def _is_valid_position(
    position: tuple,
    existing_tendroids: list,
    min_separation: float
  ) -> bool:
    """Check if position is far enough from existing Tendroids."""
    x, y, z = position
    
    for tendroid in existing_tendroids:
      tx, ty, tz = tendroid.position
      
      # Calculate XZ distance (ignore Y)
      dx = x - tx
      dz = z - tz
      distance = (dx*dx + dz*dz) ** 0.5
      
      if distance < min_separation:
        return False
    
    return True
