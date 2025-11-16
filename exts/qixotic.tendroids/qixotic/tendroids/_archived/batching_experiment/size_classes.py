"""
Size class definitions for batched Tendroid rendering

Defines three size classes (small/medium/large) with radius ranges
and provides utilities for distributing Tendroids across classes.
"""

import random
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class SizeClass:
  """
  Defines a size class with radius range and segment count.
  
  Attributes:
      name: Class identifier (SMALL, MEDIUM, LARGE)
      min_radius: Minimum radius for this class
      max_radius: Maximum radius for this class
      num_segments: Vertical resolution (segments per Tendroid)
  """
  name: str
  min_radius: float
  max_radius: float
  num_segments: int
  
  def get_representative_radius(self) -> float:
    """Get the representative radius for this class (midpoint)."""
    return (self.min_radius + self.max_radius) / 2.0


# Define the three size classes
SIZE_CLASSES = {
  'SMALL': SizeClass(
    name='SMALL',
    min_radius=8.0,
    max_radius=9.0,
    num_segments=16
  ),
  'MEDIUM': SizeClass(
    name='MEDIUM',
    min_radius=9.0,
    max_radius=11.0,
    num_segments=16
  ),
  'LARGE': SizeClass(
    name='LARGE',
    min_radius=11.0,
    max_radius=12.0,
    num_segments=16
  )
}


def distribute_across_classes(count: int) -> dict:
  """
  Distribute a count of Tendroids across size classes.
  
  Uses random distribution to create natural variation while
  ensuring all size classes are represented.
  
  Args:
      count: Total number of Tendroids to distribute
  
  Returns:
      Dictionary mapping size class name to count
      Example: {'SMALL': 5, 'MEDIUM': 6, 'LARGE': 4}
  """
  if count <= 0:
    return {'SMALL': 0, 'MEDIUM': 0, 'LARGE': 0}
  
  # Ensure at least one of each class if count >= 3
  if count >= 3:
    distribution = {'SMALL': 1, 'MEDIUM': 1, 'LARGE': 1}
    remaining = count - 3
  else:
    distribution = {'SMALL': 0, 'MEDIUM': 0, 'LARGE': 0}
    remaining = count
  
  # Randomly distribute remaining Tendroids
  class_names = ['SMALL', 'MEDIUM', 'LARGE']
  for _ in range(remaining):
    chosen_class = random.choice(class_names)
    distribution[chosen_class] += 1
  
  return distribution


def assign_size_class(radius: float) -> str:
  """
  Assign a size class based on radius.
  
  Args:
      radius: Tendroid radius
  
  Returns:
      Size class name ('SMALL', 'MEDIUM', or 'LARGE')
  """
  if radius < SIZE_CLASSES['SMALL'].max_radius:
    return 'SMALL'
  elif radius < SIZE_CLASSES['MEDIUM'].max_radius:
    return 'MEDIUM'
  else:
    return 'LARGE'


def get_random_radius_for_class(class_name: str) -> float:
  """
  Get a random radius within a size class range.
  
  Args:
      class_name: Size class name
  
  Returns:
      Random radius within the class range
  """
  size_class = SIZE_CLASSES[class_name]
  return random.uniform(size_class.min_radius, size_class.max_radius)


def create_size_class_batches(tendroid_count: int) -> List[Tuple[str, int]]:
  """
  Create size class batches for a given Tendroid count.
  
  Returns list of (class_name, count) tuples in creation order,
  randomly intermixed for natural appearance.
  
  Args:
      tendroid_count: Total number of Tendroids
  
  Returns:
      List of (class_name, count) for each batch
      Example: [('SMALL', 1), ('MEDIUM', 1), ('SMALL', 1), ...]
  """
  distribution = distribute_across_classes(tendroid_count)
  
  # Create individual assignments
  assignments = []
  for class_name, count in distribution.items():
    for _ in range(count):
      assignments.append(class_name)
  
  # Shuffle for random intermixing
  random.shuffle(assignments)
  
  # Convert to batches (group consecutive same-class items)
  batches = []
  if not assignments:
    return batches
  
  current_class = assignments[0]
  current_count = 1
  
  for class_name in assignments[1:]:
    if class_name == current_class:
      current_count += 1
    else:
      batches.append((current_class, current_count))
      current_class = class_name
      current_count = 1
  
  # Add final batch
  batches.append((current_class, current_count))
  
  return batches
