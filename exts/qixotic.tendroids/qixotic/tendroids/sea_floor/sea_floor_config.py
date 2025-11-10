"""
Sea floor configuration

Defines all parameters for terrain generation.
"""

from dataclasses import dataclass


@dataclass
class SeaFloorConfig:
  """Configuration for sea floor terrain generation."""
  
  # Dimensions
  width: float = 800.0
  depth: float = 800.0
  
  # Height variation
  amplitude: float = 32.0  # Increased from 24.0 for dramatic terrain (±16 units)
  frequency: float = 0.01  # Reduced for fewer, larger undulations
  octaves: int = 3
  
  # Mesh resolution (number of subdivisions)
  resolution_x: int = 60
  resolution_y: int = 60
  
  # USD paths
  parent_path: str = "/Environment"
  mesh_name: str = "sea_floor"
  
  @property
  def mesh_path(self) -> str:
    """Full USD path to sea floor mesh."""
    return f"{self.parent_path}/{self.mesh_name}"
  
  @property
  def grid_spacing_x(self) -> float:
    """Spacing between grid points in X direction."""
    return self.width / self.resolution_x
  
  @property
  def grid_spacing_y(self) -> float:
    """Spacing between grid points in Y direction."""
    return self.depth / self.resolution_y
