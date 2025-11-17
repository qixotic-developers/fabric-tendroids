"""
Core Tendroid class with dual animation mode support and bubble emission

Manages a single Tendroid creature with either transform-based or
vertex deformation animation, plus bubble emission capability.
"""

import carb
from .tendroid_builder import TendroidBuilder
from .tendroid_lifecycle import TendroidLifecycle
from ..animation.animation_mode import AnimationMode


class Tendroid:
  """
  A single Tendroid creature with configurable animation mode and bubble emission.
  
  Animation Modes:
  - TRANSFORM: Scale individual segment cylinders (Phase 1, stable fallback)
  - VERTEX_DEFORM: GPU-accelerated mesh deformation (Phase 2A, high-performance)
  
  IMPORTANT: Glass/transparent materials disable animation to prevent GPU crashes.
  
  This class focuses on core animation logic, delegating:
  - Creation to TendroidBuilder
  - Lifecycle management to TendroidLifecycle
  - Bubble emission to BubbleManager (via scene manager)
  """
  
  def __init__(
    self,
    name: str,
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    num_segments: int = 32,
    radial_resolution: int = 16,
    animation_mode: AnimationMode = AnimationMode.VERTEX_DEFORM,
    bubble_manager = None
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
        animation_mode: TRANSFORM or VERTEX_DEFORM
        bubble_manager: Optional BubbleManager instance for bubble emission
    """
    self.name = name
    self.position = position
    self.radius = radius
    self.length = length
    self.num_segments = num_segments
    self.radial_resolution = radial_resolution
    self.animation_mode = animation_mode
    self.bubble_manager = bubble_manager
    
    # USD references
    self.base_path = None
    self.mesh_path = None
    self.mesh_prim = None
    
    # Component objects (initialized by TendroidBuilder)
    self.warp_deformer = None  # Used in VERTEX_DEFORM mode
    self.breathing_animator = None
    self.material_safety = None
    self.mesh_updater = None  # Phase 1 updater (TRANSFORM mode)
    self.vertex_deform_helper = None  # Phase 2A updater (VERTEX_DEFORM mode)
    
    # Internal state
    self.deform_start_height = 0.0
    self._initial_vertices = None
    self.is_created = False
    self.is_active = True
    
    # Bubble emission state
    self._last_bubble_emission = -999.0  # Time of last bubble
    self._min_bubble_interval = 0.1  # Minimum seconds between bubbles
    
    carb.log_info(
      f"[Tendroid] Initialized '{name}' at {position}, "
      f"mode={animation_mode}, bubbles={'enabled' if bubble_manager else 'disabled'}"
    )
  
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
  
  def update(self, dt: float, current_time: float = 0.0):
    """
    Update animation for current frame.
    
    Routes to appropriate update method based on animation_mode.
    Handles bubble emission when breathing wave reaches top.
    
    SAFETY: Checks for glass material periodically and blocks updates.
    
    Args:
        dt: Delta time (seconds)
        current_time: Absolute time (for bubble timing)
    """
    if not self.is_created or not self.is_active:
      return
    
    # No components initialized
    if not self.breathing_animator or not self.material_safety:
      return
    
    # Periodic material safety check
    if self.material_safety.should_check_now():
      self.material_safety.check_material()
    
    # CRITICAL: Block all updates for glass materials
    if not self.material_safety.is_safe_for_animation():
      return
    
    # Route to animation-mode-specific update
    if self.animation_mode == AnimationMode.VERTEX_DEFORM:
      self._update_vertex_deform(dt, current_time)
    else:  # TRANSFORM mode
      self._update_transform(dt)
  
  def _update_vertex_deform(self, dt: float, current_time: float):
    """
    Update using vertex deformation (Phase 2A).
    
    Supports both FastMeshUpdater (C++) and Python fallback.
    Handles bubble emission when wave reaches top.
    """
    if not self.warp_deformer:
      return
    
    # Check which updater is available
    has_fast_updater = (self.vertex_deform_helper and 
                        self.vertex_deform_helper.is_initialized())
    has_fallback = self.mesh_updater and self.mesh_updater.is_valid()
    
    if not (has_fast_updater or has_fallback):
      return
    
    try:
      # Get wave parameters
      wave_params = self.breathing_animator.update(dt)
      
      # Apply deformation if wave is active
      if wave_params['active']:
        deformed_vertices = self.warp_deformer.update(
          wave_center=wave_params['wave_center'],
          bulge_length=wave_params['bulge_length'],
          amplitude=wave_params['amplitude'],
          wave_growth_distance=wave_params.get('wave_growth_distance', 0.0),
          distance_traveled=wave_params.get('distance_traveled', 0.0)
        )
        
        # Update mesh via FastMeshUpdater or fallback
        if has_fast_updater:
          self.vertex_deform_helper.update_vertices(deformed_vertices)
        else:
          self.mesh_updater.update_vertices(deformed_vertices)
      
      # Check for bubble emission
      if self.bubble_manager and self._should_emit_bubble(current_time):
        if self.breathing_animator.should_emit_bubble():
          self._emit_bubble()
          self._last_bubble_emission = current_time
    
    except Exception as e:
      carb.log_error(
        f"[Tendroid] Vertex deform update failed for '{self.name}': {e}"
      )
  
  def _update_transform(self, dt: float):
    """
    Update using transform scaling (Phase 1 fallback).
    
    Requires: mesh_updater
    
    NOTE: Transform mode not yet implemented - placeholder for future.
    """
    carb.log_warn(
      f"[Tendroid] Transform mode not yet implemented for '{self.name}'"
    )
  
  def _should_emit_bubble(self, current_time: float) -> bool:
    """
    Check if enough time has passed since last bubble.
    
    Args:
        current_time: Absolute time (seconds)
    
    Returns:
        True if ready to emit bubble
    """
    return (current_time - self._last_bubble_emission) >= self._min_bubble_interval
  
  def _emit_bubble(self):
    """
    Emit bubble from top of tendroid.
    
    Calculates emission position and max deformation diameter,
    then delegates to BubbleManager.
    """
    if not self.bubble_manager:
      return
    
    try:
      # Get top position
      top_position = self.get_top_position()
      
      # Calculate max deformation diameter
      # Max diameter = base_radius * (1 + amplitude) * 2
      max_deformation_diameter = self.radius * (1.0 + self.breathing_animator.amplitude) * 2.0
      
      # Emit bubble via manager
      self.bubble_manager.emit_bubble(
        tendroid_name=self.name,
        position=top_position,
        max_deformation_diameter=max_deformation_diameter
      )
      
      carb.log_info(
        f"[Tendroid] '{self.name}' emitted bubble, diameter={max_deformation_diameter:.1f}"
      )
    
    except Exception as e:
      carb.log_error(f"[Tendroid] Failed to emit bubble from '{self.name}': {e}")
  
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
  
  def get_animation_mode_name(self) -> str:
    """Get human-readable animation mode name."""
    return str(self.animation_mode)
