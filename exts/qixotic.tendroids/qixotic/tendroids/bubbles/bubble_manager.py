"""
Bubble manager with deformation synchronization

Manages bubble creation, deformation-locked movement, release,
and pop effects for all Tendroids.
"""

import carb
from .bubble import Bubble
from .bubble_config import BubbleConfig, DEFAULT_BUBBLE_CONFIG
from .bubble_helpers import create_bubble_sphere
from .deformation_tracker import DeformationWaveTracker
from .bubble_particle import PopParticleManager


class BubbleManager:
  """
  Central bubble management with deformation wave coordination.
  
  Coordinates:
  - Bubble spawning when wave becomes visible
  - Locked-phase tracking of deformation center
  - Release detection when wave contracts
  - Free-rise physics after release
  - Pop detection and particle spray effects
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
    
    # Track bubbles and wave state per tendroid
    self.bubbles = {}  # {tendroid_name: [Bubble, ...]}
    self.wave_trackers = {}  # {tendroid_name: DeformationWaveTracker}
    self.bubble_spawned_this_cycle = {}  # {tendroid_name: bool}
    self.tendroid_positions = {}  # {tendroid_name: (x, y, z)}
    
    self.bubble_counter = 0
    
    # Pop particle manager
    self.particle_manager = PopParticleManager(stage, config)
    
    # Parent path for bubble prims
    self.bubble_parent_path = "/World/Bubbles"
    self._ensure_bubble_parent()
  
  def _ensure_bubble_parent(self):
    """Create /World/Bubbles parent if needed."""
    if not self.stage.GetPrimAtPath(self.bubble_parent_path):
      from pxr import UsdGeom
      UsdGeom.Scope.Define(self.stage, self.bubble_parent_path)
  
  def register_tendroid(
    self,
    tendroid_name: str,
    cylinder_length: float,
    deform_start_height: float,
    position: tuple = (0, 0, 0)
  ):
    """
    Register tendroid for bubble tracking.
    
    Args:
        tendroid_name: Unique tendroid identifier
        cylinder_length: Total cylinder length
        deform_start_height: Y position where deformation begins
        position: (x, y, z) world position of tendroid base
    """
    if tendroid_name not in self.wave_trackers:
      self.wave_trackers[tendroid_name] = DeformationWaveTracker(
        cylinder_length=cylinder_length,
        deform_start_height=deform_start_height
      )
      self.bubbles[tendroid_name] = []
      self.bubble_spawned_this_cycle[tendroid_name] = False
      self.tendroid_positions[tendroid_name] = position
  
  def update_tendroid_wave(
    self,
    tendroid_name: str,
    wave_params: dict,
    base_radius: float,
    wave_speed: float
  ):
    """
    Update deformation wave state for tendroid.
    
    Called each frame by tendroid to provide wave data.
    
    Args:
        tendroid_name: Tendroid identifier
        wave_params: Dict from BreathingAnimator.update()
        base_radius: Cylinder base radius
        wave_speed: Deformation wave speed
    """
    if tendroid_name not in self.wave_trackers:
      carb.log_warn(
        f"[BubbleManager] Tendroid '{tendroid_name}' not registered"
      )
      return
    
    tracker = self.wave_trackers[tendroid_name]
    tracker.update(wave_params, base_radius)
    
    # Check for bubble spawn
    should_spawn, spawn_y, initial_diameter = tracker.should_spawn_bubble()
    
    if should_spawn and not self.bubble_spawned_this_cycle[tendroid_name]:
      self._spawn_bubble(
        tendroid_name=tendroid_name,
        spawn_y=spawn_y,
        initial_diameter=initial_diameter,
        wave_speed=wave_speed,
        base_radius=base_radius
      )
      self.bubble_spawned_this_cycle[tendroid_name] = True
    
    # Reset spawn flag when wave becomes inactive
    if not wave_params['active']:
      self.bubble_spawned_this_cycle[tendroid_name] = False
    
    # Update locked bubbles
    self._update_locked_bubbles(tendroid_name, tracker, base_radius)
  
  def _spawn_bubble(
    self,
    tendroid_name: str,
    spawn_y: float,
    initial_diameter: float,
    wave_speed: float,
    base_radius: float
  ):
    """
    Create new bubble at spawn position.
    
    Args:
        tendroid_name: Tendroid identifier
        spawn_y: Y position to spawn at
        initial_diameter: Initial bubble diameter (will grow)
        wave_speed: Speed of deformation wave
        base_radius: Cylinder base radius
    """
    # Check bubble limit
    active_count = len([b for b in self.bubbles[tendroid_name] if b.is_alive])
    if active_count >= self.config.max_bubbles_per_tendroid:
      return
    
    # Get tendroid's actual position
    tendroid_pos = self.tendroid_positions.get(tendroid_name, (0.0, 0.0, 0.0))
    spawn_position = (tendroid_pos[0], spawn_y, tendroid_pos[2])
    
    # Create bubble instance
    self.bubble_counter += 1
    bubble_id = f"bubble_{tendroid_name}_{self.bubble_counter:04d}"
    
    bubble = Bubble(
      bubble_id=bubble_id,
      initial_position=spawn_position,
      initial_diameter=initial_diameter,
      deform_wave_speed=wave_speed,
      base_radius=base_radius,
      config=self.config,
      stage=self.stage
    )
    
    # Create USD geometry
    prim_path = f"{self.bubble_parent_path}/{bubble_id}"
    success = create_bubble_sphere(
      stage=self.stage,
      prim_path=prim_path,
      position=spawn_position,
      diameter=initial_diameter,
      resolution=self.config.resolution,
      config=self.config
    )
    
    if success:
      bubble.prim_path = prim_path
      bubble.prim = self.stage.GetPrimAtPath(prim_path)
      self.bubbles[tendroid_name].append(bubble)
  
  def _update_locked_bubbles(self, tendroid_name: str, tracker: DeformationWaveTracker, base_radius: float):
    """
    Update bubbles in locked phase and detect pops.
    
    Args:
        tendroid_name: Tendroid identifier
        tracker: DeformationWaveTracker for this tendroid
        base_radius: Cylinder base radius
    """
    popped_bubbles = []
    
    for bubble in self.bubbles[tendroid_name]:
      if bubble.is_locked():
        # Calculate diameter at bubble's BOTTOM position to prevent wall clipping
        bubble_center_y = bubble.physics.position[1]
        bubble_radius = bubble.physics.diameter / 2.0
        vertical_stretch = bubble.physics.vertical_stretch
        bubble_bottom_y = bubble_center_y - (bubble_radius * vertical_stretch)
        
        # Get target diameter at bubble BOTTOM
        target_diameter = tracker.get_deformation_at_height(bubble_bottom_y, base_radius) * 2.0
        
        # Apply diameter multiplier from config
        target_diameter *= self.config.diameter_multiplier
        
        # Update bubble with deformation center and target diameter
        bubble.update_locked(
          dt=1.0/60.0,
          deform_center_y=tracker.wave_center,
          deform_radius=target_diameter / 2.0  # Pass as radius for Bubble wrapper
        )
        
        # Check if bubble popped during update
        if bubble.has_popped:
          popped_bubbles.append(bubble)
        
        # Check if bubble should be released (top clears cylinder)
        bubble_radius = bubble.physics.get_radius()
        if tracker.should_release_bubble(bubble.physics.position[1], bubble_radius):
          bubble.release()
    
    # Handle popped bubbles
    for bubble in popped_bubbles:
      self._handle_bubble_pop(bubble)

  def _handle_bubble_pop(self, bubble: Bubble):
    """
    Handle bubble pop event - create particle spray.
    
    Args:
        bubble: Bubble that just popped
    """
    pop_position = bubble.get_pop_position()
    
    # Create particle spray at pop location
    self.particle_manager.create_pop_spray(pop_position)
  
  def update(self, dt: float):
    """
    Update all bubbles (released phase only) and particles.
    
    Locked bubbles are updated via update_tendroid_wave().
    
    Args:
        dt: Delta time (seconds)
    """
    popped_bubbles = []
    
    for tendroid_name in list(self.bubbles.keys()):
      bubbles = self.bubbles[tendroid_name]
      
      # Update released bubbles
      for bubble in bubbles:
        if bubble.is_released():
          bubble.update_released(dt)
          
          # Check if bubble popped during update
          if bubble.has_popped:
            popped_bubbles.append(bubble)
      
      # Remove dead bubbles
      dead_bubbles = [b for b in bubbles if not b.is_alive]
      for bubble in dead_bubbles:
        bubble.destroy()
        bubbles.remove(bubble)
    
    # Handle any pops that occurred
    for bubble in popped_bubbles:
      self._handle_bubble_pop(bubble)
    
    # Update pop particles
    self.particle_manager.update(dt)
  
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
      
      if tendroid_name in self.wave_trackers:
        del self.wave_trackers[tendroid_name]
      
      if tendroid_name in self.bubble_spawned_this_cycle:
        del self.bubble_spawned_this_cycle[tendroid_name]
      
      if tendroid_name in self.tendroid_positions:
        del self.tendroid_positions[tendroid_name]
  
  def clear_all_bubbles(self):
    """Remove all bubbles from all tendroids and all particles."""
    for tendroid_name in list(self.bubbles.keys()):
      self.clear_tendroid_bubbles(tendroid_name)
    
    # Clear all pop particles
    self.particle_manager.clear_all()
  
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
  
  def get_particle_count(self) -> int:
    """Get count of active pop particles."""
    return len(self.particle_manager.particles)
  
  def set_pop_time_range(self, min_time: float, max_time: float):
    """
    Update pop time range configuration.
    
    Args:
        min_time: Minimum seconds before pop
        max_time: Maximum seconds before pop
    """
    self.config.min_pop_time = min_time
    self.config.max_pop_time = max_time
