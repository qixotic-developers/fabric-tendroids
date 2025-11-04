"""
Core Tendroid class with Warp-based smooth vertex deformation

Manages a single Tendroid creature with GPU-accelerated breathing animation.
"""

import carb
from .tendroid_builder import TendroidBuilder
from .tendroid_lifecycle import TendroidLifecycle


class Tendroid:
  """
  A single Tendroid creature with smooth vertex deformation.
  
  Uses Warp for GPU-accelerated mesh deformation to create realistic
  breathing animation with a single traveling bulge effect.
  
  IMPORTANT: Glass/transparent materials disable animation to prevent GPU crashes.
  
  This class focuses on core animation logic, delegating:
  - Creation to TendroidBuilder
  - Lifecycle management to TendroidLifecycle
  """
  
  def __init__(
    self,
    name: str,
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    num_segments: int = 32,
    radial_resolution: int = 16
  ):
    """
    Initialize Tendroid.
    
    Args:
        name: Unique identifier
        position: (x, y, z) world position
        radius: Cylinder radius
        length: Total length
        num_segments: Vertical resolution (higher = smoother)
        radial_resolution: Circumference resolution
    """
    self.name = name
    self.position = position
    self.radius = radius
    self.length = length
    self.num_segments = num_segments
    self.radial_resolution = radial_resolution
    
    # USD references
    self.base_path = None
    self.mesh_path = None
    self.mesh_prim = None
    
    # Component objects (initialized by TendroidBuilder)
    self.warp_deformer = None
    self.breathing_animator = None
    self.material_safety = None
    self.mesh_updater = None
    
    # Internal state
    self.deform_start_height = 0.0
    self._initial_vertices = None
    self.is_created = False
    self.is_active = True
    
    carb.log_info(f"[Tendroid] Initialized '{name}' at {position}")
  
  def create(self, stage, parent_path: str = "/World/Tendroids") -> bool:
    """
    Create Tendroid geometry in USD stage.
    
    Delegates to TendroidBuilder for creation logic.
    
    Args:
        stage: USD stage
        parent_path: Parent prim path
    
    Returns:
        Success status
    """
    return TendroidBuilder.create_in_stage(self, stage, parent_path)
  
  def update(self, dt: float):
    """
    Update animation for current frame.
    
    SAFETY: Checks for glass material periodically and blocks updates.
    
    Args:
        dt: Delta time (seconds)
    """
    if not self.is_created or not self.is_active:
      return
    
    # No components initialized
    if not all([self.warp_deformer, self.breathing_animator,
                self.material_safety, self.mesh_updater]):
      return
    
    # Periodic material safety check
    if self.material_safety.should_check_now():
      self.material_safety.check_material()
    
    # CRITICAL: Block all updates for glass materials
    if not self.material_safety.is_safe_for_animation():
      return
    
    try:
      # Get wave parameters
      wave_params = self.breathing_animator.update(dt)
      
      # Apply deformation if wave is active
      if wave_params['active']:
        deformed_vertices = self.warp_deformer.update(
          wave_center=wave_params['wave_center'],
          bulge_length=wave_params['bulge_length'],
          amplitude=wave_params['amplitude']
        )
        
        # Update mesh in USD
        self.mesh_updater.update_vertices(deformed_vertices)
      
      # Check for bubble emission
      if self.breathing_animator.should_emit_bubble():
        self._emit_bubble()
    
    except Exception as e:
      carb.log_error(f"[Tendroid] Update failed for '{self.name}': {e}")
  
  def _emit_bubble(self):
    """Emit bubble from top (Phase 2 feature)."""
    carb.log_info(f"[Tendroid] '{self.name}' emitting bubble!")
  
  # === Lifecycle delegation methods ===
  
  def set_active(self, active: bool):
    """Enable/disable animation. Delegates to TendroidLifecycle."""
    TendroidLifecycle.set_active(self, active)
  
  def set_breathing_parameters(self, **kwargs):
    """Update breathing animation parameters. Delegates to TendroidLifecycle."""
    TendroidLifecycle.set_breathing_parameters(self, **kwargs)
  
  def destroy(self, stage):
    """Remove from stage and cleanup resources. Delegates to TendroidLifecycle."""
    TendroidLifecycle.destroy(self, stage)
  
  def get_top_position(self) -> tuple:
    """Get world position of top for bubble emission. Delegates to TendroidLifecycle."""
    return TendroidLifecycle.get_top_position(self)
  
  def is_animation_enabled(self) -> bool:
    """Check if animation is enabled. Delegates to TendroidLifecycle."""
    return TendroidLifecycle.is_animation_enabled(self)
  
  def get_status_message(self) -> str:
    """Get human-readable status message. Delegates to TendroidLifecycle."""
    return TendroidLifecycle.get_status_message(self)
