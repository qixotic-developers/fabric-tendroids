"""
V2 Animation Controller - Update loop for tendroids and bubbles

Manages per-frame updates with wave effects and bubble system integration.
"""

import carb
import time
import omni.kit.app

from ..animation import WaveController, WaveConfig


class V2AnimationController:
    """
    Controls animation lifecycle for V2 tendroids and bubbles.
    
    Manages update subscription and coordinates deformation updates.
    """
    
    def __init__(self):
        """Initialize animation controller."""
        self.tendroids = []  # List of V2Tendroid instances
        self.tendroid_data = []  # List of tendroid data dicts
        self.bubble_manager = None
        self.gpu_bubble_adapter = None  # GPU bubble physics
        self.update_subscription = None
        self.is_running = False
        
        self._frame_count = 0
        self._absolute_time = 0.0
        
        # Wave controller
        self.wave_controller = WaveController(WaveConfig())
        
        # Profiling
        self._profiling_enabled = False
        self._profile_samples = []
        self._last_profile_time = 0
        self._profile_interval = 1.0
        self._profile_frame_start = 0
    
    def set_tendroids(self, tendroids: list, tendroid_data: list = None):
        """
        Set tendroids to animate.
        
        Args:
            tendroids: List of V2WarpTendroid instances
            tendroid_data: List of tendroid data dicts (from builder)
        """
        self.tendroids = tendroids
        self.tendroid_data = tendroid_data or []
    
    def set_bubble_manager(self, bubble_manager):
        """Set bubble manager for animation updates."""
        self.bubble_manager = bubble_manager
    
    def set_gpu_bubble_adapter(self, gpu_adapter):
        """
        Set GPU bubble physics adapter.
        
        NOTE: GPU bubbles temporarily disabled - needs lifecycle management.
        Falling back to CPU for full bubble system functionality.
        """
        # TEMPORARY: Disable GPU bubbles until lifecycle management is complete
        carb.log_warn("[GPU] Bubble physics temporarily disabled - using CPU fallback")
        self.gpu_bubble_adapter = None  # Force CPU path
        # self.gpu_bubble_adapter = gpu_adapter  # Will re-enable after fixes
    
    def start(self, enable_profiling: bool = False):
        """
        Start animation loop.
        
        Args:
            enable_profiling: Enable FPS logging
        """
        if self.is_running:
            return
        
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
            
            # Get delta time
            dt = 1.0 / 60.0
            if event and hasattr(event, 'payload'):
                payload = event.payload
                if isinstance(payload, dict):
                    dt = payload.get('dt', dt)
            
            self._absolute_time += dt
            
            # Update wave controller
            self.wave_controller.update(dt)
            
            # Get wave state for GPU path
            wave_state = self.wave_controller.get_wave_state()
            
            # === GPU BUBBLE PATH (if available) ===
            if self.gpu_bubble_adapter:
                # Update all bubble physics on GPU in one batch
                from ..bubbles import DEFAULT_V2_BUBBLE_CONFIG
                self.gpu_bubble_adapter.update_gpu(
                    dt=dt,
                    config=DEFAULT_V2_BUBBLE_CONFIG,
                    wave_state=wave_state
                )
                
                # Get results from GPU
                bubble_positions = self.gpu_bubble_adapter.get_bubble_positions()
                bubble_phases = self.gpu_bubble_adapter.get_bubble_phases()
                
                # Apply deformation to each tendroid based on GPU bubble state
                self._apply_gpu_bubble_deformations(
                    bubble_positions, 
                    bubble_phases, 
                    wave_state
                )
                
                # Update visuals
                self._update_bubble_visuals_from_gpu(bubble_positions)
                
            # === CPU BUBBLE PATH (fallback) ===
            elif self.bubble_manager:
                self.bubble_manager.update(
                    dt, 
                    self.tendroids,
                    self.wave_controller
                )
            else:
                # No bubble system - apply wave-only to all tendroids
                for tendroid in self.tendroids:
                    tendroid.apply_wave_only_with_state(wave_state)
            
        except Exception as e:
            carb.log_error(f"[V2AnimationController] Update error: {e}")
            import traceback
            traceback.print_exc()
    
    def _apply_gpu_bubble_deformations(
        self, 
        bubble_positions: dict, 
        bubble_phases: dict,
        wave_state: dict
    ):
        """
        Apply deformation to tendroids based on GPU bubble state.
        
        Syncs GPU state to CPU bubble manager, then applies deformations.
        
        Args:
            bubble_positions: Dict[tendroid_name] -> (x, y, z)
            bubble_phases: Dict[tendroid_name] -> phase_int
            wave_state: Wave controller state
        """
        if not self.bubble_manager:
            return
        
        # Sync GPU state to CPU bubble manager
        self._sync_gpu_to_cpu_bubbles(bubble_positions, bubble_phases)
        
        for tendroid in self.tendroids:
            name = tendroid.name
            phase = bubble_phases.get(name, 0)
            
            # Phase 0 = idle, no bubble
            if phase == 0:
                # Wave-only motion
                if wave_state:
                    tendroid.apply_wave_only_with_state(wave_state)
                continue
            
            # Get bubble state from CPU manager for radius info
            if name not in self.bubble_manager._bubbles:
                continue
            
            bubble_state = self.bubble_manager._bubbles[name]
            
            # Phase 1 = rising, Phase 2 = exiting
            if phase == 1 or phase == 2:
                # Apply deformation at bubble position
                bubble_y = bubble_state.y
                bubble_radius = bubble_state.current_radius
                
                if wave_state:
                    tendroid.apply_deformation_with_wave_state(
                        bubble_y,
                        bubble_radius,
                        wave_state
                    )
                else:
                    tendroid.apply_deformation(bubble_y, bubble_radius, 0.0, 0.0)
            
            # Phase 3 = released, Phase 4 = popped
            else:
                # Wave-only motion (bubble is free or gone)
                if wave_state:
                    tendroid.apply_wave_only_with_state(wave_state)
                else:
                    tendroid.apply_wave_only(0.0, 0.0)
    
    def _sync_gpu_to_cpu_bubbles(self, positions: dict, phases: dict):
        """
        Sync GPU bubble state back to CPU bubble manager.
        
        Updates y position, phase, and handles pop/respawn logic.
        """
        if not self.bubble_manager:
            return
        
        for name, pos in positions.items():
            if name in self.bubble_manager._bubbles:
                state = self.bubble_manager._bubbles[name]
                
                # Update Y position (relative to tendroid base)
                tendroid_y = state.tendroid.position[1]
                state.y = float(pos[1]) - tendroid_y
                
                # Update phase from GPU
                phase = phases.get(name, 0)
                phase_names = ['idle', 'rising', 'exiting', 'released', 'popped']
                if 0 <= phase < len(phase_names):
                    state.phase = phase_names[phase]
                
                # Recalculate current radius based on new Y position
                if state.y <= state.spawn_y:
                    state.current_radius = state.tendroid.radius
                elif state.y >= state.max_diameter_y:
                    state.current_radius = state.max_radius
                else:
                    zone_length = state.max_diameter_y - state.spawn_y
                    if zone_length > 0:
                        progress = (state.y - state.spawn_y) / zone_length
                        state.current_radius = state.tendroid.radius + progress * (
                            state.max_radius - state.tendroid.radius
                        )
                
                # Handle pop detection (GPU doesn't do this yet)
                if phase == 3:  # Released
                    if state.y >= state.pop_height:
                        # Trigger pop
                        state._pop()
                        # Will respawn after delay in next section
                
                # Handle respawn (GPU doesn't do this yet)
                if phase == 4 or state.phase == 'popped':
                    state.respawn_timer -= 0.016  # Approximate dt
                    if state.respawn_timer <= 0:
                        # Respawn bubble
                        state._spawn()
                        # Tell GPU to reset this bubble (hacky for now)
                        # Will be fixed when GPU handles full lifecycle
    
    def _update_bubble_visuals_from_gpu(self, positions: dict):
        """
        Update bubble sphere visuals from GPU physics results.
        
        Args:
            positions: Dict[tendroid_name] -> (x, y, z)
        """
        if not self.bubble_manager:
            return
        
        from pxr import Gf, UsdGeom
        
        for name, pos in positions.items():
            if name in self.bubble_manager._bubbles:
                state = self.bubble_manager._bubbles[name]
                
                # Convert numpy.float32 to Python float for USD
                x, y, z = float(pos[0]), float(pos[1]), float(pos[2])
                
                # Update world position
                state.world_pos = [x, y, z]
                
                # Update visual transform
                if state.translate_op:
                    state.translate_op.Set(Gf.Vec3d(x, y, z))
                
                # Make bubble visible
                if state.sphere_prim:
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
