"""
V2 Bubble Manager - Lifecycle management for bubble-driven deformation

Manages bubble spawning, rising, release, pop, and respawn for all tendroids.
Includes v1-style physics: elongation, wave throw, shape transition.

Key fix: Wave displacement and bubble deformation are now composed together
in a single GPU pass - no more fighting between the two systems.

New in this version:
- Particle burst effect on pop
- Wave drift for rising bubbles
- Extended mouth deformation during exit
"""

import carb
import random
from pxr import UsdGeom, Gf

from .bubble_config import V2BubbleConfig, DEFAULT_V2_BUBBLE_CONFIG

# Import particle manager from v1 (up two levels from v2/bubbles, then into v1/bubbles)
from ...v1.bubbles.bubble_particle import PopParticleManager


class V2BubbleManager:
    """
    Manages bubbles across all tendroids.
    
    Each tendroid can have one active bubble that drives its deformation.
    Bubbles rise, exit, pop, and respawn automatically.
    """
    
    def __init__(self, stage, config: V2BubbleConfig = None):
        self.stage = stage
        self.config = config or DEFAULT_V2_BUBBLE_CONFIG
        self._bubbles = {}
        self._bubble_counter = 0
        self._bubble_parent = "/World/Bubbles"
        self._ensure_parent()
        
        # Particle system for pop effects (use resolved config)
        self.particle_manager = PopParticleManager(stage, self.config)
    
    def _ensure_parent(self):
        if self.stage and not self.stage.GetPrimAtPath(self._bubble_parent):
            UsdGeom.Scope.Define(self.stage, self._bubble_parent)
    
    def register_tendroid(self, tendroid):
        name = tendroid.name
        if name not in self._bubbles:
            self._bubbles[name] = _BubbleState(
                tendroid=tendroid,
                config=self.config,
                stage=self.stage,
                parent_path=self._bubble_parent,
                bubble_id=self._bubble_counter,
                particle_manager=self.particle_manager
            )
            self._bubble_counter += 1
    
    def update(self, dt: float, tendroids: list, wave_controller=None):
        for t in tendroids:
            if t.name not in self._bubbles:
                self.register_tendroid(t)
        for name, state in self._bubbles.items():
            state.update(dt, wave_controller)
        
        # Update particle system
        if self.particle_manager:
            self.particle_manager.update(dt)
    
    def get_bubble_count(self) -> int:
        return sum(1 for s in self._bubbles.values() if s.phase != "idle")
    
    def clear_all(self):
        for state in self._bubbles.values():
            state.destroy()
        self._bubbles.clear()
        
        # Clear particles
        if self.particle_manager:
            self.particle_manager.clear_all()


class _BubbleState:
    """
    State machine for bubble with v1-style physics.
    
    Phases: idle -> rising -> exiting -> released -> popped -> idle
    
    Key: Wave displacement is now passed to deformation for composition.
    """
    
    def __init__(self, tendroid, config: V2BubbleConfig, stage, parent_path: str, bubble_id: int, particle_manager):
        self.tendroid = tendroid
        self.config = config
        self.stage = stage
        self.parent_path = parent_path
        self.bubble_id = bubble_id
        self.particle_manager = particle_manager
        
        self.prim_path = f"{parent_path}/bubble_{tendroid.name}_{bubble_id}"
        self.sphere_prim = None
        self.translate_op = None
        self.scale_op = None
        
        self.y = 0.0
        self.world_pos = [0.0, 0.0, 0.0]
        self.velocity = [0.0, 0.0, 0.0]
        
        # Track release position for upward movement
        self.release_position = None
        
        self.current_radius = tendroid.radius
        self.final_radius = tendroid.radius
        
        self.vertical_stretch = 1.5
        self.horizontal_scale = 1.0
        
        self.phase = "idle"
        self.age = 0.0
        self.release_timer = 0.0
        self.respawn_timer = 0.0
        self.pop_height = 0.0
        
        # Growth zone - use tendroid's spawn height calculation
        self.spawn_y = tendroid.get_spawn_height(config.spawn_height_pct)
        self.max_diameter_y = tendroid.length * config.max_diameter_pct
        self.max_radius = tendroid.radius * (1.0 + tendroid.deformer.max_amplitude)
        
        # Physics tuning
        self.shape_transition_time = 0.3
        self.throw_duration = 0.5
        self.throw_strength = 2.0
        
        # Cache last wave displacement for smooth transitions
        self._last_wave_dx = 0.0
        self._last_wave_dz = 0.0
        
        self._spawn()
    
    def _get_wave_displacement(self, wave_controller) -> tuple:
        """Get wave displacement at tendroid position."""
        if wave_controller and wave_controller.enabled:
            wave_dx, _, wave_dz = wave_controller.get_displacement(self.tendroid.position)
            self._last_wave_dx = wave_dx
            self._last_wave_dz = wave_dz
            return wave_dx, wave_dz
        return self._last_wave_dx, self._last_wave_dz
    
    def _spawn(self):
        """Spawn bubble at correct position above flared base."""
        self.phase = "rising"
        self.age = 0.0
        self.y = self.spawn_y
        
        # Start bubble SMALLER than cylinder, then grow - SPHERICAL shape
        self.current_radius = self.tendroid.radius * 0.5  # Start at half cylinder radius
        self.vertical_stretch = 1.0  # SPHERICAL - not elongated
        self.horizontal_scale = 1.0
        self.velocity = [0.0, 0.0, 0.0]
        self.release_timer = 0.0
        
        tx, ty, tz = self.tendroid.position
        self.world_pos = [tx, ty + self.y, tz]
        
        self.pop_height = self.tendroid.length + random.uniform(
            self.config.min_pop_height, self.config.max_pop_height
        )
        
        self._create_visual()
        
        if self.config.debug_logging:
            carb.log_info(
                f"[Bubble] Spawned {self.tendroid.name} at y={self.spawn_y:.1f}, "
                f"r={self.current_radius:.1f} (spherical)"
            )

    
    def _create_visual(self):
        if self.stage.GetPrimAtPath(self.prim_path).IsValid():
            self.stage.RemovePrim(self.prim_path)
        
        sphere = UsdGeom.Sphere.Define(self.stage, self.prim_path)
        sphere.CreateRadiusAttr(1.0)
        sphere.CreateDisplayColorAttr([self.config.color])
        sphere.CreateDisplayOpacityAttr([self.config.opacity])
        
        xform = UsdGeom.Xformable(sphere.GetPrim())
        xform.ClearXformOpOrder()
        self.translate_op = xform.AddTranslateOp()
        self.scale_op = xform.AddScaleOp()
        
        self.translate_op.Set(Gf.Vec3d(*self.world_pos))
        self._update_scale()
        
        self.sphere_prim = sphere.GetPrim()
        
        if self.config.hide_until_clear:
            UsdGeom.Imageable(self.sphere_prim).MakeInvisible()
    
    def _get_bubble_bottom_y(self) -> float:
        """Get Y position of bubble bottom (center - stretched radius)."""
        return self.y - (self.current_radius * self.vertical_stretch)
    
    def _get_bubble_top_y(self) -> float:
        """Get Y position of bubble top (center + stretched radius)."""
        return self.y + (self.current_radius * self.vertical_stretch)

    def update(self, dt: float, wave_controller=None):
        if self.phase == "idle":
            self._update_idle(dt, wave_controller)
        elif self.phase == "rising":
            self._update_rising(dt, wave_controller)
        elif self.phase == "exiting":
            self._update_exiting(dt, wave_controller)
        elif self.phase == "released":
            self._update_released(dt, wave_controller)
        elif self.phase == "popped":
            self._update_popped(dt, wave_controller)
    
    def _update_idle(self, dt: float, wave_controller=None):
        """Idle state - tendroid sways with wave, waiting for respawn."""
        # Apply wave-only deformation while waiting
        wave_dx, wave_dz = self._get_wave_displacement(wave_controller)
        self.tendroid.apply_wave_only(wave_dx, wave_dz)
        
        self.respawn_timer -= dt
        if self.respawn_timer <= 0 and self.config.auto_respawn:
            self._spawn()

    
    def _update_rising(self, dt: float, wave_controller=None):
        """Bubble rising inside tendroid, driving deformation with wave."""
        self.age += dt
        self.y += self.config.rise_speed * dt
        
        # Calculate radius growth: starts at 50% of cylinder, grows to max
        # Growth happens from spawn_y to max_diameter_y
        min_radius = self.tendroid.radius * 0.5  # Match spawn size
        
        if self.y <= self.spawn_y:
            self.current_radius = min_radius
        elif self.y >= self.max_diameter_y:
            self.current_radius = self.max_radius
        else:
            # Smooth growth curve from min_radius to max_radius
            t = (self.y - self.spawn_y) / (self.max_diameter_y - self.spawn_y)
            # Use ease-out curve for more natural growth
            t_smooth = 1.0 - (1.0 - t) * (1.0 - t)
            self.current_radius = min_radius + t_smooth * (self.max_radius - min_radius)
        
        effective_radius = self.current_radius * self.config.diameter_multiplier
        
        # Get wave displacement and pass to deformation
        wave_dx, wave_dz = self._get_wave_displacement(wave_controller)
        
        # Drive deformation at bubble position WITH wave displacement
        self.tendroid.apply_deformation(self.y, effective_radius, wave_dx, wave_dz)
        
        # Update world position with wave tracking (should match deformation)
        self._update_world_pos_with_wave(wave_controller)
        
        # Debug: verify bubble position matches expected wave-displaced centerline
        if self.config.debug_logging and self.age < 0.1:  # Log once at start
            height_ratio = min(1.0, self.y / self.tendroid.length)
            factor = height_ratio * height_ratio * (3.0 - 2.0 * height_ratio)
            expected_x = self.tendroid.position[0] + wave_dx * factor
            carb.log_info(
                f"[Bubble Debug] y={self.y:.1f}, wave_dx={wave_dx:.2f}, factor={factor:.2f}, "
                f"expected_x={expected_x:.1f}, actual_x={self.world_pos[0]:.1f}"
            )
        
        self._update_visual()
        
        # Transition to exiting when bubble CENTER reaches mouth
        if self.y >= self.tendroid.length:
            self._start_exiting(wave_controller)
    
    def _start_exiting(self, wave_controller=None):
        """Begin exit transition - bubble still drives deformation."""
        self.phase = "exiting"
        self.final_radius = self.current_radius
        
        # Capture initial throw velocity
        self.velocity = [0.0, self.config.rise_speed, 0.0]
        if wave_controller and wave_controller.enabled:
            wave_dx, _, wave_dz = wave_controller.get_displacement(tuple(self.world_pos))
            wave_period = 1.0 / wave_controller.config.frequency
            self.velocity[0] = (wave_dx * self.throw_strength) / wave_period
            self.velocity[2] = (wave_dz * self.throw_strength) / wave_period
        
        if self.config.debug_logging:
            carb.log_info(f"[Bubble] Exiting {self.tendroid.name}")

    
    def _update_exiting(self, dt: float, wave_controller=None):
        """Bubble exiting mouth - deformation continues following bubble exactly as during rising."""
        self.age += dt
        self.y += self.config.rise_speed * dt
        
        # Get wave displacement
        wave_dx, wave_dz = self._get_wave_displacement(wave_controller)
        
        # Check if bubble bottom has cleared mouth
        bubble_bottom = self._get_bubble_bottom_y()
        mouth_y = self.tendroid.length
        
        if bubble_bottom < mouth_y:
            # Bubble still partially inside - apply deformation EXACTLY like rising phase
            effective_radius = self.current_radius * self.config.diameter_multiplier
            self.tendroid.apply_deformation(self.y, effective_radius, wave_dx, wave_dz)
        else:
            # Bubble fully cleared - stop deformation and release
            self.tendroid.reset_deformation(wave_dx, wave_dz)
            self._release(wave_controller)
            return
        
        # Update position with throw momentum
        self.world_pos[0] += self.velocity[0] * dt * 0.5
        self.world_pos[2] += self.velocity[2] * dt * 0.5
        
        tx, ty, tz = self.tendroid.position
        self.world_pos[1] = ty + self.y
        
        # Ensure bubble is visible during exit
        if self.sphere_prim:
            UsdGeom.Imageable(self.sphere_prim).MakeVisible()
        
        self._update_visual()

    def _release(self, wave_controller=None):
        """Bubble fully exited - transition to free float from release position."""
        self.phase = "released"
        self.release_timer = 0.0
        
        # Capture release position for upward movement
        self.release_position = tuple(self.world_pos)
        
        if self.sphere_prim:
            UsdGeom.Imageable(self.sphere_prim).MakeVisible()
        
        if self.config.debug_logging:
            carb.log_info(
                f"[Bubble] Released {self.tendroid.name} at "
                f"({self.world_pos[0]:.1f}, {self.world_pos[1]:.1f}, {self.world_pos[2]:.1f})"
            )

    
    def _update_released(self, dt: float, wave_controller=None):
        """
        Bubble floating free with wave drift.
        
        Starts upward motion from release position, affected by waves.
        """
        self.age += dt
        self.release_timer += dt
        
        # Tendroid continues wave-only motion
        wave_dx, wave_dz = self._get_wave_displacement(wave_controller)
        self.tendroid.apply_wave_only(wave_dx, wave_dz)
        
        # Bubble stays spherical (no shape transition needed)
        self.vertical_stretch = 1.0
        
        # Vertical velocity transition
        if self.release_timer < 0.2:
            t = self.release_timer / 0.2
            accel_factor = 1.0 - (1.0 - t) ** 2
            self.velocity[1] = self.config.rise_speed + \
                (self.config.released_rise_speed - self.config.rise_speed) * accel_factor
        else:
            self.velocity[1] = self.config.released_rise_speed
        
        # Wave drift - bubble sways with current
        if wave_controller and wave_controller.enabled:
            # Get wave displacement at current bubble position
            bubble_wave_dx, _, bubble_wave_dz = wave_controller.get_displacement(
                tuple(self.world_pos)
            )
            
            # Apply wave drift directly to horizontal velocity
            wave_drift_strength = 0.15  # How much wave affects bubble drift
            self.velocity[0] = self.velocity[0] * 0.92 + bubble_wave_dx * wave_drift_strength
            self.velocity[2] = self.velocity[2] * 0.92 + bubble_wave_dz * wave_drift_strength
        else:
            # Damping without waves
            self.velocity[0] *= 0.95
            self.velocity[2] *= 0.95
        
        # Update position from velocity
        self.world_pos[0] += self.velocity[0] * dt
        self.world_pos[1] += self.velocity[1] * dt
        self.world_pos[2] += self.velocity[2] * dt
        
        self.y = self.world_pos[1] - self.tendroid.position[1]
        
        self._update_visual()
        
        if self.y >= self.pop_height:
            self._pop()
    
    def _pop(self):
        """Bubble pops - create particle spray effect."""
        self.phase = "popped"
        self.respawn_timer = self.config.respawn_delay
        
        # Create particle spray at pop position
        if self.particle_manager:
            self.particle_manager.create_pop_spray(
                pop_position=tuple(self.world_pos),
                bubble_velocity=self.velocity
            )
        
        # Hide bubble visual
        if self.sphere_prim:
            UsdGeom.Imageable(self.sphere_prim).MakeInvisible()
        
        if self.config.debug_logging:
            carb.log_info(f"[Bubble] Popped {self.tendroid.name} with particle spray")
    
    def _update_popped(self, dt: float, wave_controller=None):
        """Popped state - tendroid continues wave motion."""
        wave_dx, wave_dz = self._get_wave_displacement(wave_controller)
        self.tendroid.apply_wave_only(wave_dx, wave_dz)
        
        self.phase = "idle"
        self.respawn_timer = self.config.respawn_delay

    
    def _update_world_pos_with_wave(self, wave_controller):
        """
        Position bubble at the wave-displaced centerline.
        
        The bubble follows the deformed cylinder centerline exactly.
        Uses same wave displacement calculation as GPU kernel.
        """
        tx, ty, tz = self.tendroid.position
        self.world_pos[1] = ty + self.y
        
        if wave_controller and wave_controller.enabled:
            # Get wave displacement at tendroid base
            wave_dx, _, wave_dz = wave_controller.get_displacement((tx, ty, tz))
            
            # Apply height scaling (matches GPU kernel exactly)
            height_ratio = min(1.0, self.y / self.tendroid.length) if self.tendroid.length > 0 else 0.0
            factor = height_ratio * height_ratio * (3.0 - 2.0 * height_ratio)
            
            # Position bubble at wave-displaced centerline
            self.world_pos[0] = tx + wave_dx * factor
            self.world_pos[2] = tz + wave_dz * factor
        else:
            self.world_pos[0] = tx
            self.world_pos[2] = tz
    
    def _update_scale(self):
        if self.scale_op:
            r = self.current_radius * 0.95
            sx = r * self.horizontal_scale
            sy = r * self.vertical_stretch
            sz = r * self.horizontal_scale
            self.scale_op.Set(Gf.Vec3f(sx, sy, sz))
    
    def _update_visual(self):
        """Update bubble visual position and scale."""
        if self.translate_op:
            self.translate_op.Set(Gf.Vec3d(*self.world_pos))
        self._update_scale()
        
        # Make bubble visible (config can override to hide until clear)
        if self.sphere_prim and self.phase == "rising":
            if self.config.hide_until_clear:
                UsdGeom.Imageable(self.sphere_prim).MakeInvisible()
            else:
                UsdGeom.Imageable(self.sphere_prim).MakeVisible()
    
    def destroy(self):
        if self.stage and self.prim_path:
            prim = self.stage.GetPrimAtPath(self.prim_path)
            if prim.IsValid():
                self.stage.RemovePrim(self.prim_path)
        self.sphere_prim = None
        self.translate_op = None
        self.scale_op = None
