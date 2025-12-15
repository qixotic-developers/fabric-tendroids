"""
Creature Controller - Keyboard-controlled player creature

Handles keyboard input, simulation physics, and creature visualization.
Phase 1: Basic movement with momentum and drift.
LTEND-28: Disables keyboard during repel, re-enables on recovery.

Controls:
- W/S or Up/Down: Forward/Backward (Z-axis)
- A/D or Left/Right: Left/Right (X-axis)
- Space: Move up (Y+)
- Left Shift: Move down (Y-)
"""

import carb
import omni.appwindow
from pxr import Gf
from carb.input import KeyboardInput

from .creature_collider_helper import create_creature_collider, destroy_creature_collider
from .creature_mesh_helpers import create_creature_mesh
from .creature_input_helpers import (
    filter_keyboard_by_lock,
    get_null_keyboard_state,
    get_movement_from_filtered_keys,
)
from ..contact.input_lock_helpers import (
    InputLockStatus,
    InputLockReason,
    sync_lock_from_color_state,
    is_input_locked,
)
from ..contact.color_effect_helpers import ColorEffectStatus


class CreatureController:
    """
    Player-controlled creature with simulation physics.
    
    Supports input locking during repel state (LTEND-28).
    When input is locked, keyboard has no effect and creature
    moves only via repulsion forces. Input unlocks on recovery.
    """
    
    def __init__(self, stage, start_position=(0, 50, 0)):
        """Initialize creature controller."""
        self.stage = stage
        
        # Physics state
        self.position = Gf.Vec3f(*start_position)
        self.velocity = Gf.Vec3f(0, 0, 0)
        
        # Physics parameters
        self.creature_radius = 6.0
        self.creature_length = 12.0
        self.max_speed = 50.0
        self.acceleration_rate = 120.0
        self.drag_coefficient = 0.98
        
        # Scene bounds
        self.bounds_min = Gf.Vec3f(-400, 10, -400)
        self.bounds_max = Gf.Vec3f(400, 400, 400)
        
        # Keyboard input
        self.input_interface = carb.input.acquire_input_interface()
        self.keyboard = None
        if self.input_interface:
            app_window = omni.appwindow.get_default_app_window()
            if app_window:
                self.keyboard = app_window.get_keyboard()
        
        # Orientation tracking
        self.intended_velocity = Gf.Vec3f(0, 0, 0)
        
        # Input lock state (LTEND-28)
        self._input_lock_status = InputLockStatus()
        
        # Create mesh and get transform ops
        result = create_creature_mesh(
            self.stage, self.creature_radius, self.creature_length
        )
        self.creature_prim, self.translate_op, self.rotate_op, self.current_rotation = result
        self.translate_op.Set(Gf.Vec3d(*self.position))
        
        # Create collider
        self.creature_prim_path = "/World/Creature"
        self.has_collider = create_creature_collider(self.stage, self.creature_prim_path)
        
        carb.log_info(f"[CreatureController] Initialized at {start_position}")
    
    @property
    def is_input_locked(self) -> bool:
        """Check if keyboard input is currently locked."""
        return is_input_locked(self._input_lock_status)
    
    @property
    def input_lock_reason(self) -> InputLockReason:
        """Get current input lock reason."""
        return self._input_lock_status.reason
    
    def sync_input_lock(self, color_status: ColorEffectStatus) -> None:
        """Synchronize input lock state from color effect state."""
        old_locked = self._input_lock_status.is_locked
        self._input_lock_status = sync_lock_from_color_state(
            self._input_lock_status, color_status
        )
        if old_locked != self._input_lock_status.is_locked:
            state_msg = "LOCKED - repel active" if self._input_lock_status.is_locked else "UNLOCKED"
            carb.log_info(f"[CreatureController] Input {state_msg}")
    
    def apply_repulsion_force(self, force_vector: tuple) -> None:
        """Apply external repulsion force (bypasses keyboard lock)."""
        fx, fy, fz = force_vector
        self.velocity += Gf.Vec3f(fx, fy, fz)
        if self.velocity.GetLength() > self.max_speed:
            self.velocity = self.velocity.GetNormalized() * self.max_speed
    
    def _get_keyboard_state(self):
        """Get raw keyboard input state."""
        if not self.input_interface or self.keyboard is None:
            return get_null_keyboard_state()
        
        return {
            'forward': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.W) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.UP) != 0),
            'backward': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.S) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.DOWN) != 0),
            'left': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.A) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.LEFT) != 0),
            'right': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.D) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.RIGHT) != 0),
            'up': self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.SPACE) != 0,
            'down': self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.LEFT_SHIFT) != 0,
        }
    
    def get_position(self):
        """Get current creature position."""
        return tuple(self.position)
    
    def get_radius(self):
        """Get creature collision radius."""
        return self.creature_radius
    
    def destroy(self):
        """Cleanup creature resources."""
        if hasattr(self, 'creature_prim_path') and self.stage:
            destroy_creature_collider(self.stage, self.creature_prim_path)
        if self.creature_prim and self.stage:
            prim_path = str(self.creature_prim.GetPath())
            if self.stage.GetPrimAtPath(prim_path):
                self.stage.RemovePrim(prim_path)
        carb.log_info("[CreatureController] Destroyed")
    
    def update(self, dt: float, bubble_positions: dict = None, bubble_radii: dict = None,
               wave_state: dict = None, tendroids: list = None):
        """
        Update creature physics and position.
        
        LTEND-28: Keyboard input filtered based on lock state.
        """
        from .creature_update_helpers import (
            apply_wave_drift, clamp_to_bounds, check_bubble_collisions,
            check_tendroid_interactions, calculate_rotation,
        )
        
        # Get and filter keyboard (LTEND-28)
        raw_keys = self._get_keyboard_state()
        keys = filter_keyboard_by_lock(raw_keys, self._input_lock_status)
        
        # Calculate accelerations
        ax, ay, az = get_movement_from_filtered_keys(keys, self.acceleration_rate, dt)
        raw_ax, raw_ay, raw_az = get_movement_from_filtered_keys(raw_keys, self.acceleration_rate, dt)
        
        # Update velocities
        self.velocity += Gf.Vec3f(ax, ay, az)
        self.velocity *= self.drag_coefficient
        self.intended_velocity += Gf.Vec3f(raw_ax, raw_ay, raw_az)
        self.intended_velocity *= self.drag_coefficient
        
        # Clamp speeds
        if self.velocity.GetLength() > self.max_speed:
            self.velocity = self.velocity.GetNormalized() * self.max_speed
        if self.intended_velocity.GetLength() > self.max_speed:
            self.intended_velocity = self.intended_velocity.GetNormalized() * self.max_speed
        
        # Update position
        self.position += self.velocity * dt
        self.position = apply_wave_drift(self.position, wave_state, dt)
        self.position = clamp_to_bounds(self.position, self.bounds_min, self.bounds_max)
        
        # Update transforms
        if self.translate_op:
            self.translate_op.Set(Gf.Vec3d(*self.position))
        if self.rotate_op:
            self.current_rotation = calculate_rotation(self.intended_velocity, self.current_rotation)
            self.rotate_op.Set(self.current_rotation)
        
        # Check collisions
        self.velocity, popped = check_bubble_collisions(
            self.position, self.creature_radius, bubble_positions, bubble_radii, self.velocity)
        self.velocity, interactions = check_tendroid_interactions(
            self.position, self.velocity, self.creature_radius, tendroids)
        
        return popped, interactions
