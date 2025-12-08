"""
V2 Animation Controller - Update loop for tendroids and bubbles

Manages per-frame updates with wave effects and bubble system integration.
GPU bubble physics fully supported with proper state synchronization.
"""

import time

import carb

from ..animation import WaveConfig, WaveController
from ..bubbles import DEFAULT_V2_BUBBLE_CONFIG


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

      # GPU path
      if self.gpu_bubble_adapter:
        self._update_gpu_path(dt, wave_state)
      # CPU fallback
      elif self.bubble_manager:
        self.bubble_manager.update(dt, self.tendroids, self.wave_controller)
        # Update interactive creature (Phase 1) - CPU path
        if self.creature_controller:
          bubble_positions = self.bubble_manager.get_bubble_positions()
          bubble_radii = self.bubble_manager.get_bubble_radii()
          collision_data = self.creature_controller.update(dt, bubble_positions, bubble_radii, wave_state)
          # Handle collisions (extract tendroid name from tuple)
          for tendroid_name, collision_dir in collision_data:
            self.bubble_manager.pop_bubble(tendroid_name)
      # No bubbles - wave only
      else:
        for tendroid in self.tendroids:
          tendroid.apply_wave_only_with_state(wave_state)
        # Update interactive creature (Phase 1) - no bubbles
        if self.creature_controller:
          self.creature_controller.update(dt, wave_state=wave_state)

    except Exception as e:
      carb.log_error(f"[V2AnimationController] Update error: {e}")
      import traceback
      traceback.print_exc()

  def _update_gpu_path(self, dt: float, wave_state: dict):
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
    if self.batch_deformer and self.batch_deformer.is_built:
      self._apply_batch_deformation(bubble_data, wave_state)
    else:
      self._apply_deformations_gpu(bubble_data, wave_state)

    # 5. Update interactive creature with bubble collision detection
    if self.creature_controller:
      # Extract positions and radii for active bubbles
      bubble_positions = {}
      bubble_radii = {}
      for name, data in bubble_data.items():
        if data['phase'] > 0:  # Active bubble
          bubble_positions[name] = data['position']
          bubble_radii[name] = data['radius']
      
      # Update creature and get list of popped bubbles with collision data
      collision_data = self.creature_controller.update(dt, bubble_positions, bubble_radii, wave_state)
      
      # Trigger pop for collided bubbles with particle effects
      for tendroid_name, collision_dir in collision_data:
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

  def _apply_deformations_gpu(self, bubble_data: dict, wave_state: dict):
    """
    Apply deformations using GPU bubble state.

    Args:
        bubble_data: Dict[name] -> {phase, position, radius}
        wave_state: Wave controller state
    """
    if not self.bubble_manager:
      return

    for tendroid in self.tendroids:
      name = tendroid.name

      if name not in bubble_data:
        tendroid.apply_wave_only_with_state(wave_state)
        continue

      data = bubble_data[name]
      phase = data['phase']

      # Phase 0 = idle (no bubble)
      if phase == 0:
        tendroid.apply_wave_only_with_state(wave_state)
        continue

      # Phase 1 = rising, 2 = exiting -> deform
      if phase == 1 or phase == 2:
        # Use GPU position and radius
        pos = data['position']
        radius = data['radius']

        # Calculate Y relative to tendroid base
        bubble_y = pos[1] - tendroid.position[1]

        # Scale for deformation bulge
        deform_radius = radius * DEFAULT_V2_BUBBLE_CONFIG.diameter_multiplier

        tendroid.apply_deformation_with_wave_state(
          bubble_y,
          deform_radius,
          wave_state
        )
      else:
        # Phase 3 = released, 4 = popped -> wave only
        tendroid.apply_wave_only_with_state(wave_state)

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
