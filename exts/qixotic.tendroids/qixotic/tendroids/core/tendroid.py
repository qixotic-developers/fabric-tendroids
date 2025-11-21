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
    self._frame_count = 0  # For debug logging
    self._current_wave_displacement = (0.0, 0.0, 0.0)  # Track wave offset for bubbles
  
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
  
  def update(self, dt: float, current_time: float = 0.0, wave_controller=None, tendroid_id: int = 0):
    """
    Update animation for current frame with optional wave effects.
    
    Routes to appropriate update method based on animation_mode.
    Handles bubble emission when breathing wave reaches top.
    Applies wave-based swaying motion if wave_controller provided.
    
    SAFETY: Checks for glass material periodically and blocks updates.
    
    Args:
        dt: Delta time (seconds)
        current_time: Absolute time (for bubble timing)
        wave_controller: Optional WaveController for ocean current effects
        tendroid_id: Unique ID for phase offset in wave motion
    """
    if not self.is_created or not self.is_active:
      return
    
    # Increment frame counter for debug logging
    self._frame_count += 1
    
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
      self._update_vertex_deform(dt, current_time, wave_controller, tendroid_id)
    else:  # TRANSFORM mode
      self._update_transform(dt, wave_controller, tendroid_id)
  
  def _update_vertex_deform(self, dt: float, current_time: float, wave_controller=None, tendroid_id: int = 0):
    """
    Update using vertex deformation (Phase 2A) with wave effects.
    
    Supports both FastMeshUpdater (C++) and Python fallback.
    Handles bubble emission via deformation synchronization.
    Applies wave-based displacement if controller provided.
    """
    if not self.warp_deformer:
      return
    
    # Debug log wave controller status on first frame
    if self._frame_count == 1:
      if wave_controller:
        carb.log_info(f"[Tendroid] Wave controller active for '{self.name}' (ID: {tendroid_id})")
      else:
        carb.log_warn(f"[Tendroid] No wave controller for '{self.name}'!")
    
    # Check which updater is available
    has_fast_updater = (self.vertex_deform_helper and 
                        self.vertex_deform_helper.is_initialized())
    has_fallback = self.mesh_updater and self.mesh_updater.is_valid()
    
    if not (has_fast_updater or has_fallback):
      return
    
    try:
      # Get wave parameters
      wave_params = self.breathing_animator.update(dt)
      
      # Update bubble manager with wave state (handles spawn, lock, release)
      if self.bubble_manager:
        # Get current top position including wave displacement
        top_pos = self.get_top_position()
        
        self.bubble_manager.update_tendroid_wave(
          tendroid_name=self.name,
          wave_params=wave_params,
          base_radius=self.radius,
          wave_speed=self.breathing_animator.wave_speed,
          top_position=top_pos
        )
      
      # Apply deformation if wave is active
      if wave_params['active']:
        deformed_vertices = self.warp_deformer.update(
          wave_center=wave_params['wave_center'],
          bulge_length=wave_params['bulge_length'],
          amplitude=wave_params['amplitude'],
          wave_growth_distance=wave_params.get('wave_growth_distance', 0.0),
          distance_traveled=wave_params.get('distance_traveled', 0.0)
        )
      else:
        # Get rest pose vertices even when not breathing
        deformed_vertices = self.warp_deformer.get_rest_vertices()
        
      # Apply wave displacement if controller provided (always, not just during breathing)
      if wave_controller and deformed_vertices is not None:
        # Get displacement for tendroid position
        wave_disp = wave_controller.get_displacement(self.position, tendroid_id)
        
        # Store the wave displacement at maximum height (for bubble emission)
        # The tip gets full displacement
        self._current_wave_displacement = (
          wave_disp[0] * 1.0,  # Full displacement at tip
          0.0,  # No vertical displacement
          wave_disp[2] * 1.0   # Full displacement at tip
        )
        
        # Debug logging
        if tendroid_id == 0 and self._frame_count % 60 == 0:  # Log every second for first tendroid
          carb.log_info(f"[Wave] Displacement: ({wave_disp[0]:.2f}, {wave_disp[1]:.2f}, {wave_disp[2]:.2f})")
          carb.log_info(f"[Wave] Vertices type: {type(deformed_vertices)}, count: {len(deformed_vertices)}")
          carb.log_info(f"[Wave] Wave active: {wave_params.get('active', False)}")
          
          # Log first vertex position for debugging
          if len(deformed_vertices) > 0:
            v0 = deformed_vertices[0]
            carb.log_info(f"[Wave] First vertex before: ({v0[0]:.2f}, {v0[1]:.2f}, {v0[2]:.2f})")
        
        # Convert to list if needed for modification
        from pxr import Vt, Gf
        if isinstance(deformed_vertices, Vt.Vec3fArray):
          # Work with Vt array directly
          num_verts = len(deformed_vertices)
          if num_verts > 0:
            # Find min and max Y to determine height range
            y_min = min(v[1] for v in deformed_vertices)
            y_max = max(v[1] for v in deformed_vertices)
            y_range = y_max - y_min if y_max > y_min else 1.0
            
            # Create new array with wave displacement
            modified_verts = Vt.Vec3fArray(num_verts)
            for i in range(num_verts):
              v = deformed_vertices[i]
              # Calculate height factor based on actual Y position
              height_factor = (v[1] - y_min) / y_range if y_range > 0 else 0.0
              # Smooth curve for more natural bending
              height_factor = height_factor * height_factor * (3.0 - 2.0 * height_factor)
              
              # Apply wave displacement
              modified_verts[i] = Gf.Vec3f(
                v[0] + wave_disp[0] * height_factor,
                v[1],  # Y unchanged
                v[2] + wave_disp[2] * height_factor
              )
            
            # Replace the array
            deformed_vertices = modified_verts
            
            # Debug: log that we modified vertices
            if tendroid_id == 0 and self._frame_count % 60 == 0:
              carb.log_info(f"[Wave] Modified {num_verts} vertices with wave displacement")
      
      # Update mesh via FastMeshUpdater or fallback (if we have vertices to update)
      if deformed_vertices is not None:
        # Debug log which updater we're using
        if tendroid_id == 0 and self._frame_count % 60 == 0:
          if has_fast_updater:
            carb.log_info("[Wave] Using FastMeshUpdater to apply vertices")
          else:
            carb.log_info("[Wave] Using Python mesh updater to apply vertices")
        
        if has_fast_updater:
          self.vertex_deform_helper.update_vertices(deformed_vertices)
        else:
          self.mesh_updater.update_vertices(deformed_vertices)
    
    except Exception as e:
      carb.log_error(
        f"[Tendroid] Vertex deform update failed for '{self.name}': {e}"
      )
  
  def _update_transform(self, dt: float, wave_controller=None, tendroid_id: int = 0):
    """
    Update using transform scaling (Phase 1 fallback) with wave effects.
    
    Requires: mesh_updater
    
    NOTE: Transform mode not yet implemented - placeholder for future.
    """
    carb.log_warn(
      f"[Tendroid] Transform mode not yet implemented for '{self.name}'"
    )
  

  
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
