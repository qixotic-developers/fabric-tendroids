"""
Sea floor helper functions for height calculations

Handles Perlin noise generation and height queries with bilinear interpolation.
"""

import carb
import numpy as np
from .sea_floor_config import SeaFloorConfig

# Module-level cached height map
_height_map = None
_config = None
_noise_module = None


def _get_noise_module():
  """Lazy import of noise module."""
  global _noise_module
  if _noise_module is None:
    try:
      import noise
      _noise_module = noise
    except ImportError:
      carb.log_error("[SeaFloorHelper] Noise module not installed. Installing...")
      try:
        import omni.kit.pipapi
        omni.kit.pipapi.install("noise>=1.2.2", module="noise")
        import noise
        _noise_module = noise
        carb.log_info("[SeaFloorHelper] Noise module installed successfully")
      except Exception as e:
        carb.log_error(f"[SeaFloorHelper] Failed to install noise module: {e}")
        raise
  return _noise_module


def initialize_height_map(config: SeaFloorConfig = None):
  """
  Generate and cache the height map.
  
  Args:
      config: Configuration for terrain generation
  """
  global _height_map, _config
  
  if config is None:
    config = SeaFloorConfig()
  
  _config = config
  
  # Get noise module
  noise = _get_noise_module()
  
  # Generate height map using Perlin noise
  _height_map = np.zeros((config.resolution_y + 1, config.resolution_x + 1))
  
  half_width = config.width / 2.0
  half_depth = config.depth / 2.0
  
  min_height = float('inf')
  max_height = float('-inf')
  
  for y_idx in range(config.resolution_y + 1):
    for x_idx in range(config.resolution_x + 1):
      # Convert grid indices to world coordinates
      x = -half_width + (x_idx * config.grid_spacing_x)
      z = -half_depth + (y_idx * config.grid_spacing_y)
      
      # Generate Perlin noise with proper octave accumulation
      height = 0.0
      amplitude = config.amplitude
      frequency = config.frequency
      max_amplitude = 0.0
      
      for octave in range(config.octaves):
        noise_val = noise.pnoise2(
          x * frequency,
          z * frequency,
          octaves=1,
          persistence=0.5,
          lacunarity=2.0,
          repeatx=1024,
          repeaty=1024,
          base=42
        )
        height += noise_val * amplitude
        max_amplitude += amplitude
        
        amplitude *= 0.5
        frequency *= 2.0
      
      # Normalize to use full amplitude range
      height = (height / max_amplitude) * config.amplitude
      
      _height_map[y_idx, x_idx] = height
      
      # Track min/max for debugging
      min_height = min(min_height, height)
      max_height = max(max_height, height)
  
  carb.log_info(
    f"[SeaFloorHelper] Generated height map: "
    f"{config.resolution_x + 1}x{config.resolution_y + 1} grid, "
    f"height range: [{min_height:.2f}, {max_height:.2f}]"
  )


def get_height_at(x: float, y: float) -> float:
  """
  Get floor height at world position using bilinear interpolation.
  
  Args:
      x: World X coordinate
      y: World Y coordinate (depth)
  
  Returns:
      Z height at position (0.0 if outside bounds or not initialized)
  """
  global _height_map, _config
  
  if _height_map is None or _config is None:
    return 0.0
  
  # Convert world coords to grid space
  half_width = _config.width / 2.0
  half_depth = _config.depth / 2.0
  
  # Check bounds
  if (x < -half_width or x > half_width or 
      y < -half_depth or y > half_depth):
    return 0.0
  
  # Map to grid indices (fractional)
  grid_x = (x + half_width) / _config.grid_spacing_x
  grid_y = (y + half_depth) / _config.grid_spacing_y
  
  # Get integer indices for corners
  x0 = int(np.floor(grid_x))
  y0 = int(np.floor(grid_y))
  x1 = min(x0 + 1, _config.resolution_x)
  y1 = min(y0 + 1, _config.resolution_y)
  
  # Get fractional parts
  fx = grid_x - x0
  fy = grid_y - y0
  
  # Bilinear interpolation
  h00 = _height_map[y0, x0]
  h10 = _height_map[y0, x1]
  h01 = _height_map[y1, x0]
  h11 = _height_map[y1, x1]
  
  h0 = h00 * (1 - fx) + h10 * fx
  h1 = h01 * (1 - fx) + h11 * fx
  
  return h0 * (1 - fy) + h1 * fy
