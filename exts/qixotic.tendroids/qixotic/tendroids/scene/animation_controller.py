"""
V2 Animation Controller - Update loop for tendroids and bubbles

Manages per-frame updates with wave effects and bubble system integration.
GPU bubble physics fully supported with proper state synchronization.
"""

import time

import carb

from ..animation import WaveConfig, WaveController
from ..bubbles import DEFAULT_V2_BUBBLE_CONFIG
from ..debug import EnvelopeVisualizer
from ..deflection import DeflectionIntegration


class V2AnimationController:
  """
  Controls animation lifecycle for V2 tendroids and bubbles.

  Manages update subscription and coordinates deformation updates.
  Supports both CPU and GPU bubble physics paths.
  """

  def __init__(self):
    """Initialize animation controller."""
    self.tendroids = []
    self.tendroid_data = []
    self.bubble_manager = None
    self.gpu_bubble_adapter = None
    self.batch_deformer = None
    self.creature_controller = None  # Interactive creature
    self.envelope_visualizer = None  # Debug visualization
    self.deflection_integration = None  # Tendroid bending system
    self.update_subscription = None
    self.is_running = False

    self._frame_count = 0
    self._absolute_time = 0.0

    self.wave_controller = WaveController(WaveConfig())

    # Fabric GPU path (zero-copy mesh updates)
    self._use_fabric_write = True  # Enable Fabric by default
    self._stage_id = None

    # Profiling
    self._profiling_enabled = False
    self._profile_samples = []
    self._last_profile_time = 0
    self._profile_interval = 1.0
    self._profile_frame_start = 0

  def set_tendroids(self, tendroids: list, tendroid_data: list = None):
    """Set tendroids to animate."""
    self.tendroids = tendroids
    self.tendroid_data = tendroid_data or []

  def set_bubble_manager(self, bubble_manager):
    """Set bubble manager for animation updates."""
    self.bubble_manager = bubble_manager

  def set_gpu_bubble_adapter(self, gpu_adapter):
    """Set GPU bubble physics adapter."""
    self.gpu_bubble_adapter = gpu_adapter
    if gpu_adapter:
      carb.log_info("[GPU] Bubble physics enabled - full lifecycle on GPU")

  def set_batch_deformer(self, batch_deformer):
    """Set batch deformation manager."""
    self.batch_deformer = batch_deformer
    if batch_deformer:
      carb.log_info("[GPU] Batch deformation enabled")

  def set_creature_controller(self, creature_controller):
    """Set creature controller for interactive gameplay."""
    self.creature_controller = creature_controller
    if creature_controller:
      carb.log_info("[Creature] Interactive creature enabled")

  def set_envelope_visualizer(self, visualizer: EnvelopeVisualizer):
    """Set envelope debug visualizer."""
    self.envelope_visualizer = visualizer
    if visualizer:
      carb.log_info("[Debug] Envelope visualizer enabled")

  def set_deflection_integration(self, deflection: DeflectionIntegration):
    """Set deflection system for creature-tendroid interaction."""
    self.deflection_integration = deflection
    if deflection:
      carb.log_info("[Deflection] System connected to animation controller")

  def toggle_envelope_debug(self) -> bool:
    """Toggle envelope visualization. Returns new state."""
    if self.envelope_visualizer:
      return self.envelope_visualizer.toggle()
    return False

  def set_fabric_write(self, enabled: bool):
    """Enable/disable Fabric GPU write path."""
    self._use_fabric_write = enabled
    path_name = "Fabric GPU" if enabled else "CPU"
    carb.log_info(f"[AnimationController] Mesh write path: {path_name}")

  def start(self, enable_profiling: bool = False):
    """Start animation loop."""
    if self.is_running:
      return

    # Get stage_id for Fabric operations
    import omni.usd
    usd_context = omni.usd.get_context()
    if usd_context:
      self._stage_id = usd_context.get_stage_id()
      carb.log_info(f"[AnimationController] Stage ID: {self._stage_id}")

    update_stream = omni.kit.app.get_app().get_update_event_stream()
    self.update_subscription = update_stream.create_subscription_to_pop(
      self._on_update,
      name="V2AnimationController.Update"
    )

    self.is_running = True
    self._frame_count = 0
    self._absolute_time = 0.0

    self._profiling_enabled = enable_profiling
    if enable_profiling:
      self._profile_samples = []
      self._last_profile_time = time.perf_counter()
      self._profile_frame_start = 0

    carb.log_info("[V2AnimationController] Started")

  def stop(self):
    """Stop animation loop."""
    if self.update_subscription:
      self.update_subscription.unsubscribe()
      self.update_subscription = None

    self.is_running = False
    self._profiling_enabled = False

    if self._profile_samples:
      self._log_profile_summary()
      self._profile_samples = []

    carb.log_info("[V2AnimationController] Stopped")

  def _on_update(self, event):
    """Per-frame update callback."""
    try:
      self._frame_count += 1

      if self._profiling_enabled:
        self._sample_performance()

      dt = 1.0 / 60.0
      if event and hasattr(event, 'payload'):
        payload = event.payload
        if isinstance(payload, dict):
          dt = payload.get('dt', dt)

      self._absolute_time += dt

      # Update wave motion
      self.wave_controller.update(dt)
      wave_state = self.wave_controller.get_wave_state()

      # Update deflection system (creature-tendroid bending)
      deflection_states = {}
      if self.deflection_integration and self.creature_controller:
        deflection_states = self.deflection_integration.update(
          self.creature_controller, dt
        )

      # GPU path - pass deflection states to deformation
      if self.gpu_bubble_adapter:
        self._update_gpu_path(dt, wave_state, deflection_states)
      # CPU fallback
      elif self.bubble_manager:
        self.bubble_manager.update(dt, self.tendroids, self.wave_controller)
        # Update interactive creature (Phase 1) - CPU path
        if self.creature_controller:
          bubble_positions = self.bubble_manager.get_bubble_positions()
          bubble_radii = self.bubble_manager.get_bubble_radii()
          popped, interactions = self.creature_controller.update(dt, bubble_positions, bubble_radii, wave_state)
          # Handle collisions (extract tendroid name from tuple)
          for tendroid_name, collision_dir in popped:
            self.bubble_manager.pop_bubble(tendroid_name)
      # No bubbles - wave only with deflection
      else:
        self._apply_wave_only_with_deflection(wave_state, deflection_states)
        # Update interactive creature (Phase 1) - no bubbles
        if self.creature_controller:
          self.creature_controller.update(dt, wave_state=wave_state)

      # Update envelope debug visualization
      if self.envelope_visualizer and self.creature_controller:
        creature_pos = self.creature_controller.get_position()
        self.envelope_visualizer.update(creature_pos)

    except Exception as e:
      carb.log_error(f"[V2AnimationController] Update error: {e}")
      import traceback
      traceback.print_exc()

  def _apply_wave_only_with_deflection(self, wave_state: dict, deflection_states: dict):
    """
    Apply wave-only deformation with deflection bending.
    
    Used when no bubble system is active.
    """
    import math
    
    for tendroid in self.tendroids:
      # Get deflection state for this tendroid
      defl_state = deflection_states.get(tendroid.name)
      
      if defl_state and defl_state.is_deflecting and abs(defl_state.current_angle) > 0.001:
        # Calculate wave displacement
        if wave_state.get('enabled', False):
          spatial_phase = tendroid.position[0] * 0.003 + tendroid.position[2] * 0.002
          spatial_factor = 1.0 + math.sin(spatial_phase) * 0.15
          displacement_value = wave_state['displacement'] * spatial_factor
          wave_dx = displacement_value * wave_state['amplitude'] * wave_state['dir_x']
          wave_dz = displacement_value * wave_state['amplitude'] * wave_state['dir_z']
        else:
          wave_dx, wave_dz = 0.0, 0.0
        
        # Apply wave + deflection
        # Note: negate angle to bend AWAY from creature
        tendroid.apply_wave_only_with_deflection(
          wave_dx, wave_dz,
          -defl_state.current_angle,
          (defl_state.deflection_axis[0], defl_state.deflection_axis[2])
        )
      else:
        # No deflection - use standard wave-only
        tendroid.apply_wave_only_with_state(wave_state)

  def _update_gpu_path(self, dt: float, wave_state: dict, deflection_states: dict = None):
    """
    GPU bubble update - single download, GPU is source of truth.

    Flow: GPU physics → Download once → Batch deform → Update visuals → Update particles
    """
    # 1. Update physics on GPU
    self.gpu_bubble_adapter.update_gpu(
      dt=dt,
      config=DEFAULT_V2_BUBBLE_CONFIG,
      wave_state=wave_state
    )

    # 2. Download GPU state ONCE (single memory transfer)
    phases, positions, radii = self.gpu_bubble_adapter.gpu_manager.get_bubble_states()

    # 3. Build name-indexed dicts for easy lookup
    name_to_id = self.gpu_bubble_adapter._name_to_id

    bubble_data = { }
    for name, bubble_id in name_to_id.items():
      bubble_data[name] = {
        'phase': int(phases[bubble_id]),
        'position': tuple(positions[bubble_id]),
        'radius': float(radii[bubble_id])
      }

    # 4. Apply deformations - BATCH or fallback to per-tendroid
    # NOTE: Batch deformer doesn't support deflection yet, so bypass when deflecting
    any_deflecting = any(
      s.is_deflecting and abs(s.current_angle) > 0.001 
      for s in (deflection_states or {}).values()
    )
    
    if self.batch_deformer and self.batch_deformer.is_built and not any_deflecting:
      self._apply_batch_deformation(bubble_data, wave_state)
    else:
      self._apply_deformations_gpu(bubble_data, wave_state, deflection_states)

    # 5. Update interactive creature with bubble collision detection
    if self.creature_controller:
      # Extract positions and radii for active bubbles
      bubble_positions = {}
      bubble_radii = {}
      for name, data in bubble_data.items():
        if data['phase'] > 0:  # Active bubble
          bubble_positions[name] = data['position']
          bubble_radii[name] = data['radius']
      
      # Update creature and get popped bubbles with collision data
      popped, interactions = self.creature_controller.update(dt, bubble_positions, bubble_radii, wave_state)
      
      # Trigger pop for collided bubbles with particle effects
      for tendroid_name, collision_dir in popped:
        # Get bubble data before popping for particle creation
        if tendroid_name in bubble_data:
          bubble_pos = bubble_data[tendroid_name]['position']
          
          # Create pop particle spray (convert numpy types to Python floats)
          if self.bubble_manager and self.bubble_manager.particle_manager:
            self.bubble_manager.particle_manager.create_pop_spray(
              pop_position=(
                float(bubble_pos[0]),
                float(bubble_pos[1]),
                float(bubble_pos[2])
              ),
              bubble_velocity=[0.0, 0.0, 0.0]  # GPU doesn't track velocity yet
            )
          
          # Set bubble to popped state
          self.gpu_bubble_adapter.pop_bubble(tendroid_name)

    # 6. Update visuals using GPU state
    self._update_visuals_gpu(bubble_data)

    # 7. Update particle system
    if self.bubble_manager and self.bubble_manager.particle_manager:
      self.bubble_manager.particle_manager.update(dt)

  def _apply_batch_deformation(self, bubble_data: dict, wave_state: dict):
    """
    Apply deformations using single-kernel batch processing.
    
    MUCH faster than per-tendroid: 1 kernel launch instead of N.
    Supports both CPU and Fabric GPU write paths.
    """
    # Update batch deformer state from GPU bubble data
    self.batch_deformer.update_states(
      bubble_data=bubble_data,
      wave_state=wave_state,
      default_config=DEFAULT_V2_BUBBLE_CONFIG
    )

    # Single kernel launch for ALL vertices
    all_points = self.batch_deformer.deform_all()

    # Apply to meshes - choose write path
    if self._use_fabric_write and self._stage_id is not None:
      # Fabric GPU path (zero-copy)
      self.batch_deformer.apply_to_meshes_fabric(self._stage_id)
    else:
      # CPU path (fallback)
      self.batch_deformer.apply_to_meshes(all_points)

  def _apply_deformations_gpu(self, bubble_data: dict, wave_state: dict, deflection_states: dict = None):
    """
    Apply deformations using GPU bubble state with deflection support.

    Args:
        bubble_data: Dict[name] -> {phase, position, radius}
        wave_state: Wave controller state
        deflection_states: Dict[name] -> TendroidDeflectionState
    """
    import math
    
    if not self.bubble_manager:
      return
    
    deflection_states = deflection_states or {}

    for tendroid in self.tendroids:
      name = tendroid.name
      
      # Get deflection state for this tendroid
      defl_state = deflection_states.get(name)
      has_deflection = (
        defl_state and 
        defl_state.is_deflecting and 
        abs(defl_state.current_angle) > 0.001
      )
      
      # Extract deflection params
      if has_deflection:
        defl_angle = defl_state.current_angle
        defl_axis = (defl_state.deflection_axis[0], defl_state.deflection_axis[2])
      else:
        defl_angle = 0.0
        defl_axis = (1.0, 0.0)

      if name not in bubble_data:
        # No bubble - apply wave + deflection
        if has_deflection:
          self._apply_wave_deflection_single(tendroid, wave_state, defl_angle, defl_axis)
        else:
          tendroid.apply_wave_only_with_state(wave_state)
        continue

      data = bubble_data[name]
      phase = data['phase']

      # Phase 0 = idle (no bubble)
      if phase == 0:
        if has_deflection:
          self._apply_wave_deflection_single(tendroid, wave_state, defl_angle, defl_axis)
        else:
          tendroid.apply_wave_only_with_state(wave_state)
        continue

      # Phase 1 = rising, 2 = exiting -> deform with bubble
      if phase == 1 or phase == 2:
        pos = data['position']
        radius = data['radius']
        bubble_y = pos[1] - tendroid.position[1]
        deform_radius = radius * DEFAULT_V2_BUBBLE_CONFIG.diameter_multiplier
        
        if has_deflection:
          # Calculate wave displacement
          if wave_state.get('enabled', False):
            spatial_phase = tendroid.position[0] * 0.003 + tendroid.position[2] * 0.002
            spatial_factor = 1.0 + math.sin(spatial_phase) * 0.15
            displacement_value = wave_state['displacement'] * spatial_factor
            wave_dx = displacement_value * wave_state['amplitude'] * wave_state['dir_x']
            wave_dz = displacement_value * wave_state['amplitude'] * wave_state['dir_z']
          else:
            wave_dx, wave_dz = 0.0, 0.0
          
          # Apply combined: bend + wave + bubble
          # Note: negate angle to bend AWAY from creature
          tendroid.apply_deformation_with_deflection(
            bubble_y, deform_radius,
            wave_dx, wave_dz,
            -defl_angle, defl_axis
          )
        else:
          tendroid.apply_deformation_with_wave_state(
            bubble_y, deform_radius, wave_state
          )
      else:
        # Phase 3 = released, 4 = popped -> wave only
        if has_deflection:
          self._apply_wave_deflection_single(tendroid, wave_state, defl_angle, defl_axis)
        else:
          tendroid.apply_wave_only_with_state(wave_state)
  
  def _apply_wave_deflection_single(
    self, tendroid, wave_state: dict, defl_angle: float, defl_axis: tuple
  ):
    """Apply wave + deflection to a single tendroid."""
    import math
    
    if wave_state.get('enabled', False):
      spatial_phase = tendroid.position[0] * 0.003 + tendroid.position[2] * 0.002
      spatial_factor = 1.0 + math.sin(spatial_phase) * 0.15
      displacement_value = wave_state['displacement'] * spatial_factor
      wave_dx = displacement_value * wave_state['amplitude'] * wave_state['dir_x']
      wave_dz = displacement_value * wave_state['amplitude'] * wave_state['dir_z']
    else:
      wave_dx, wave_dz = 0.0, 0.0
    
    # Note: negate angle to bend AWAY from creature
    tendroid.apply_wave_only_with_deflection(
      wave_dx, wave_dz, -defl_angle, defl_axis
    )

  def _update_visuals_gpu(self, bubble_data: dict):
    """
    Update bubble visuals from GPU state.

    Args:
        bubble_data: Dict[name] -> {phase, position, radius}
    """
    if not self.bubble_manager:
      return

    from pxr import Gf, UsdGeom

    for name in self.bubble_manager._bubbles:
      state = self.bubble_manager._bubbles[name]

      if name not in bubble_data:
        continue

      data = bubble_data[name]
      phase = data['phase']
      pos = data['position']
      radius = data['radius']

      # Detect phase transitions for particle effects
      phase_names = ['idle', 'rising', 'exiting', 'released', 'popped']
      old_phase = state.phase
      new_phase = phase_names[phase] if 0 <= phase < len(phase_names) else 'idle'

      # Trigger pop particle effect on transition to popped
      if old_phase != 'popped' and new_phase == 'popped':
        # Create particle spray at pop position
        if state.particle_manager:
          # Convert GPU position to Python float for USD
          pop_pos = data['position']
          pop_pos_float = (float(pop_pos[0]), float(pop_pos[1]), float(pop_pos[2]))

          # Calculate velocity from last known position
          velocity = [0.0, DEFAULT_V2_BUBBLE_CONFIG.released_rise_speed, 0.0]
          state.particle_manager.create_pop_spray(
            pop_position=pop_pos_float,
            bubble_velocity=velocity
          )

      state.phase = new_phase

      # Convert numpy types to Python float for USD
      x, y, z = float(pos[0]), float(pos[1]), float(pos[2])
      radius = float(radius)

      state.y = y - state.tendroid.position[1]
      state.current_radius = radius
      state.world_pos = [x, y, z]

      # Phase 0 or 4 = invisible
      if phase == 0 or phase == 4:
        if state.sphere_prim:
          UsdGeom.Imageable(state.sphere_prim).MakeInvisible()
        continue

      # Update visual transform
      if state.translate_op:
        state.translate_op.Set(Gf.Vec3d(x, y, z))

      # Update scale using GPU radius
      if state.scale_op:
        r = radius * 0.92  # Match CPU bubble manager
        sx = r * state.horizontal_scale
        sy = r * state.vertical_stretch
        sz = r * state.horizontal_scale
        state.scale_op.Set(Gf.Vec3f(sx, sy, sz))

      # Visibility
      if state.sphere_prim:
        if phase == 1 and DEFAULT_V2_BUBBLE_CONFIG.hide_until_clear:
          UsdGeom.Imageable(state.sphere_prim).MakeInvisible()
        else:
          UsdGeom.Imageable(state.sphere_prim).MakeVisible()

  def _sample_performance(self):
    """Sample FPS for profiling."""
    current_time = time.perf_counter()
    elapsed = current_time - self._last_profile_time

    if elapsed >= self._profile_interval:
      frames = self._frame_count - self._profile_frame_start
      fps = frames / elapsed if elapsed > 0 else 0

      sample = {
        'frame': self._frame_count,
        'fps': fps,
        'frame_time_ms': (elapsed / frames * 1000) if frames > 0 else 0
      }
      self._profile_samples.append(sample)

      bubble_info = ""
      if self.bubble_manager:
        bubble_info = f", {self.bubble_manager.get_bubble_count()} bubbles"

      carb.log_info(
        f"[PROFILE] Frame {self._frame_count}: "
        f"{fps:.1f} fps ({sample['frame_time_ms']:.2f} ms){bubble_info}"
      )

      self._last_profile_time = current_time
      self._profile_frame_start = self._frame_count

  def _log_profile_summary(self):
    """Log profiling summary."""
    if not self._profile_samples:
      return

    fps_values = [s['fps'] for s in self._profile_samples]
    avg_fps = sum(fps_values) / len(fps_values)
    min_fps = min(fps_values)
    max_fps = max(fps_values)

    carb.log_info("=" * 50)
    carb.log_info(f"[PROFILE] Avg: {avg_fps:.1f}, Min: {min_fps:.1f}, Max: {max_fps:.1f}")
    carb.log_info("=" * 50)

  def get_profile_data(self) -> dict | None:
    """Get profiling data."""
    if not self._profile_samples:
      return None

    fps_values = [s['fps'] for s in self._profile_samples]
    return {
      'samples': self._profile_samples,
      'avg_fps': sum(fps_values) / len(fps_values),
      'min_fps': min(fps_values),
      'max_fps': max(fps_values)
    }

  def shutdown(self):
    """Cleanup on shutdown."""
    self.stop()
    self.tendroids.clear()
    self.tendroid_data.clear()
