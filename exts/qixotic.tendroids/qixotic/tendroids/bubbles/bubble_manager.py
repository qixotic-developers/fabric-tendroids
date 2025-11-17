"""
Bubble manager for Tendroids

Manages bubble creation, animation, and lifecycle for all Tendroids.
"""

import carb
from .bubble import Bubble
from .bubble_config import BubbleConfig, DEFAULT_BUBBLE_CONFIG
from .bubble_helpers import create_bubble_sphere


class BubbleManager:
  """
  Central bubble management system.
  
  Handles bubble emission, updates, and cleanup for all Tendroids.
  """
  
  def __init__(self, stage, config: BubbleConfig = None):
    """
    Initialize bubble manager.
    
    Args:
        stage: USD stage
        config: BubbleConfig instance (uses default if None)
    """
    self.stage = stage
    self.config = config or DEFAULT_BUBBLE_CONFIG
    
    # Track bubbles per tendroid
    self.bubbles = {}  # {tendroid_name: [Bubble, ...]}
    self.bubble_counter = 0
    
    # Parent path for bubble prims
    self.bubble_parent_path = "/World/Bubbles"
    self._ensure_bubble_parent()
    
    carb.log_info("[BubbleManager] Initialized")
  
  def _ensure_bubble_parent(self):
    """Create /World/Bubbles parent if needed."""
    if not self.stage.GetPrimAtPath(self.bubble_parent_path):
      from pxr import UsdGeom
      UsdGeom.Scope.Define(self.stage, self.bubble_parent_path)
      carb.log_info(
        f"[BubbleManager] Created bubble parent at '{self.bubble_parent_path}'"
      )
  
  def emit_bubble(
    self,
    tendroid_name: str,
    position: tuple,
    max_deformation_diameter: float
  ):
    """
    Emit a bubble from a tendroid.
    
    Args:
        tendroid_name: Name of emitting tendroid
        position: (x, y, z) emission position
        max_deformation_diameter: Max diameter from breathing wave
    """
    # Initialize tendroid's bubble list if needed
    if tendroid_name not in self.bubbles:
      self.bubbles[tendroid_name] = []
    
    # Check bubble limit per tendroid
    active_count = len([b for b in self.bubbles[tendroid_name] if b.is_alive])
    if active_count >= self.config.max_bubbles_per_tendroid:
      if self.config.debug_logging:
        carb.log_warn(
          f"[BubbleManager] Tendroid '{tendroid_name}' at bubble limit "
          f"({self.config.max_bubbles_per_tendroid})"
        )
      return
    
    # Calculate bubble diameter
    diameter = max_deformation_diameter * self.config.diameter_multiplier
    diameter = max(self.config.min_diameter, min(diameter, self.config.max_diameter))
    
    # Create bubble instance
    self.bubble_counter += 1
    bubble_id = f"bubble_{tendroid_name}_{self.bubble_counter:04d}"
    
    bubble = Bubble(
      bubble_id=bubble_id,
      initial_position=position,
      diameter=diameter,
      config=self.config,
      stage=self.stage
    )
    
    # Create USD geometry
    prim_path = f"{self.bubble_parent_path}/{bubble_id}"
    success = create_bubble_sphere(
      stage=self.stage,
      prim_path=prim_path,
      position=position,
      diameter=diameter,
      resolution=self.config.resolution,
      config=self.config
    )
    
    if success:
      bubble.prim_path = prim_path
      bubble.prim = self.stage.GetPrimAtPath(prim_path)
      self.bubbles[tendroid_name].append(bubble)
      
      if self.config.debug_logging:
        carb.log_info(
          f"[BubbleManager] Emitted bubble '{bubble_id}' from '{tendroid_name}'"
        )
    else:
      carb.log_error(
        f"[BubbleManager] Failed to create bubble geometry for '{bubble_id}'"
      )
  
  def update(self, dt: float):
    """
    Update all bubbles.
    
    Args:
        dt: Delta time (seconds)
    """
    # Update each tendroid's bubbles
    for tendroid_name in list(self.bubbles.keys()):
      bubbles = self.bubbles[tendroid_name]
      
      # Update living bubbles
      for bubble in bubbles:
        if bubble.is_alive:
          bubble.update(dt)
      
      # Remove dead bubbles
      dead_bubbles = [b for b in bubbles if not b.is_alive]
      for bubble in dead_bubbles:
        bubble.destroy()
        bubbles.remove(bubble)
      
      # Clean up empty tendroid entries
      if len(bubbles) == 0:
        del self.bubbles[tendroid_name]
  
  def clear_tendroid_bubbles(self, tendroid_name: str):
    """
    Remove all bubbles for a specific tendroid.
    
    Args:
        tendroid_name: Name of tendroid
    """
    if tendroid_name in self.bubbles:
      for bubble in self.bubbles[tendroid_name]:
        bubble.destroy()
      del self.bubbles[tendroid_name]
      
      if self.config.debug_logging:
        carb.log_info(
          f"[BubbleManager] Cleared bubbles for '{tendroid_name}'"
        )
  
  def clear_all_bubbles(self):
    """Remove all bubbles from all tendroids."""
    for tendroid_name in list(self.bubbles.keys()):
      self.clear_tendroid_bubbles(tendroid_name)
    
    carb.log_info("[BubbleManager] Cleared all bubbles")
  
  def get_bubble_count(self, tendroid_name: str = None) -> int:
    """
    Get bubble count.
    
    Args:
        tendroid_name: Specific tendroid (None for total)
    
    Returns:
        Number of active bubbles
    """
    if tendroid_name:
      if tendroid_name in self.bubbles:
        return len([b for b in self.bubbles[tendroid_name] if b.is_alive])
      return 0
    
    # Total across all tendroids
    total = 0
    for bubbles in self.bubbles.values():
      total += len([b for b in bubbles if b.is_alive])
    return total
