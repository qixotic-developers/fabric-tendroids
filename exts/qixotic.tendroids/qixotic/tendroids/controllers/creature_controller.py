"""
Creature Controller - Keyboard-controlled player creature

Handles keyboard input, simulation physics, and creature visualization.
Phase 1: Basic movement with momentum and drift.

Controls:
- W/S or Up/Down: Forward/Backward (Z-axis)
- A/D or Left/Right: Left/Right (X-axis)
- Space: Move up (Y+)
- Left Shift: Move down (Y-)
"""

import carb
import omni.appwindow
from pxr import Gf, UsdGeom, UsdShade
from carb.input import KeyboardInput

from .creature_collider_helper import create_creature_collider, destroy_creature_collider


class CreatureController:
    """
    Player-controlled creature with simulation physics.
    
    Controls:
    - W/S or Up/Down arrows: Forward/Backward (Z-axis)
    - A/D or Left/Right arrows: Left/Right (X-axis)
    - Space: Move up (Y+)
    - Left Shift: Move down (Y-)
    """
    
    def __init__(self, stage, start_position=(0, 50, 0)):
        """
        Initialize creature controller.
        
        Args:
            stage: USD stage for mesh creation
            start_position: Starting (x, y, z) position
        """
        self.stage = stage
        
        # Physics state
        self.position = Gf.Vec3f(*start_position)
        self.velocity = Gf.Vec3f(0, 0, 0)
        
        # Physics parameters
        self.creature_radius = 6.0
        self.creature_length = 12.0
        self.max_speed = 50.0  # units/sec
        self.acceleration_rate = 120.0  # units/sec²
        self.drag_coefficient = 0.98  # Per-frame damping
        
        # Scene bounds (matches 800x800 sea floor, extended Y for bubble testing)
        self.bounds_min = Gf.Vec3f(-400, 10, -400)
        self.bounds_max = Gf.Vec3f(400, 400, 400)  # Y raised to 400 for bubble collision testing
        
        # Keyboard input interface
        self.input_interface = carb.input.acquire_input_interface()
        
        if not self.input_interface:
            carb.log_error("[CreatureController] Failed to acquire input interface!")
            self.keyboard = None
        else:
            # Get keyboard device from app window
            app_window = omni.appwindow.get_default_app_window()
            if app_window:
                self.keyboard = app_window.get_keyboard()
            else:
                carb.log_error("[CreatureController] Failed to get app window!")
                self.keyboard = None
        
        # Current orientation
        self.current_rotation = Gf.Vec3f(0, 90, 0)  # Start horizontal
        
        # Track intended direction from keyboard (for orientation only)
        self.intended_velocity = Gf.Vec3f(0, 0, 0)
        
        # Create creature mesh
        self.creature_prim = self._create_creature_mesh()
        
        # Create PhysX capsule collider (TEND-12)
        self.creature_prim_path = "/World/Creature"
        self.has_collider = create_creature_collider(self.stage, self.creature_prim_path)
        
        carb.log_info(
            f"[CreatureController] Initialized at {start_position}, "
            f"radius={self.creature_radius}, length={self.creature_length}, "
            f"collider={'enabled' if self.has_collider else 'disabled'}"
        )
    
    def _create_creature_mesh(self):
        """Create creature mesh with body and directional nose cone."""
        from pxr import Sdf
        
        # Create parent xform for the creature
        parent_path = "/World/Creature"
        
        # Remove existing if present
        if self.stage.GetPrimAtPath(parent_path):
            self.stage.RemovePrim(parent_path)
        
        # Create parent xform
        parent_xform = UsdGeom.Xform.Define(self.stage, parent_path)
        xformable = UsdGeom.Xformable(parent_xform)
        self.translate_op = xformable.AddTranslateOp()
        self.rotate_op = xformable.AddRotateXYZOp()
        
        # Set initial transform
        self.translate_op.Set(Gf.Vec3d(*self.position))
        self.rotate_op.Set(self.current_rotation)
        
        # === BODY: Main cylinder ===
        body_path = f"{parent_path}/Body"
        body = UsdGeom.Cylinder.Define(self.stage, body_path)
        body.CreateRadiusAttr().Set(self.creature_radius)
        body.CreateHeightAttr().Set(self.creature_length)
        body.CreateAxisAttr().Set("Z")  # Cylinder along Z
        
        # === NOSE: Cone at front (+Z direction when horizontal) ===
        nose_path = f"{parent_path}/Nose"
        nose = UsdGeom.Cone.Define(self.stage, nose_path)
        nose.CreateRadiusAttr().Set(self.creature_radius)
        nose.CreateHeightAttr().Set(self.creature_radius * 2.0)  # Pointy nose
        nose.CreateAxisAttr().Set("Z")  # Point in +Z direction
        
        # Position nose at front of body
        nose_xform = UsdGeom.Xformable(nose)
        nose_translate = nose_xform.AddTranslateOp()
        # Offset to front: half body length + half nose height
        nose_offset = (self.creature_length / 2.0) + (self.creature_radius * 1.0)
        nose_translate.Set(Gf.Vec3d(0, 0, nose_offset))
        
        # === MATERIALS ===
        # Body material (cyan)
        body_mat_path = "/World/Materials/CreatureBody"
        body_material = UsdShade.Material.Define(self.stage, body_mat_path)
        body_shader = UsdShade.Shader.Define(self.stage, f"{body_mat_path}/Surface")
        body_shader.CreateIdAttr("UsdPreviewSurface")
        body_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0.2, 0.8, 0.9)  # Cyan
        )
        body_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)
        body_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.3)
        body_material.CreateSurfaceOutput().ConnectToSource(body_shader.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI(body).Bind(body_material)
        
        # Nose material (orange for visibility)
        nose_mat_path = "/World/Materials/CreatureNose"
        nose_material = UsdShade.Material.Define(self.stage, nose_mat_path)
        nose_shader = UsdShade.Shader.Define(self.stage, f"{nose_mat_path}/Surface")
        nose_shader.CreateIdAttr("UsdPreviewSurface")
        nose_shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(1.0, 0.5, 0.1)  # Orange
        )
        nose_shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.2)
        nose_shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
        nose_material.CreateSurfaceOutput().ConnectToSource(nose_shader.ConnectableAPI(), "surface")
        UsdShade.MaterialBindingAPI(nose).Bind(nose_material)
        
        return parent_xform.GetPrim()
    
    def update(self, dt: float, bubble_positions: dict = None, bubble_radii: dict = None, 
               wave_state: dict = None, tendroids: list = None):
        """
        Update creature physics and position.
        
        Args:
            dt: Time delta in seconds
            bubble_positions: Dict of {tendroid_name: (x, y, z)} bubble positions
            bubble_radii: Dict of {tendroid_name: radius} bubble radii
            wave_state: Optional wave controller state for drift effects
            tendroids: Optional list of tendroid objects for avoidance/shock detection
        
        Returns:
            Tuple of (popped_bubbles, tendroid_interactions) where:
                popped_bubbles: List of (tendroid_name, collision_direction) tuples
                tendroid_interactions: Dict of {tendroid_name: interaction_data}
        """
        # Get keyboard input state
        keys = self._get_keyboard_state()
        
        # Calculate acceleration from keyboard input
        acceleration = Gf.Vec3f(0, 0, 0)
        
        # Horizontal movement (X-axis: A/D or Left/Right)
        if keys['left']:
            acceleration[0] -= self.acceleration_rate * dt
        if keys['right']:
            acceleration[0] += self.acceleration_rate * dt
        
        # Forward/backward movement (Z-axis: W/S or Up/Down)
        if keys['forward']:
            acceleration[2] -= self.acceleration_rate * dt
        if keys['backward']:
            acceleration[2] += self.acceleration_rate * dt
        
        # Vertical movement (Y-axis: Space/Shift)
        if keys['up']:
            acceleration[1] += self.acceleration_rate * dt
        if keys['down']:
            acceleration[1] -= self.acceleration_rate * dt
        
        # Update intended velocity (for orientation) - completely separate from physics
        # This only responds to keyboard input and ignores environmental forces
        self.intended_velocity += acceleration
        
        # Apply drag to intended velocity (independent damping)
        self.intended_velocity *= self.drag_coefficient
        
        # Clamp intended velocity
        intended_speed = self.intended_velocity.GetLength()
        if intended_speed > self.max_speed:
            self.intended_velocity = self.intended_velocity.GetNormalized() * self.max_speed
        
        # Apply keyboard acceleration to actual velocity (for movement)
        self.velocity += acceleration
        
        # Clamp speed
        speed = self.velocity.GetLength()
        if speed > self.max_speed:
            self.velocity = self.velocity.GetNormalized() * self.max_speed
        
        # Apply drag to keyboard-driven velocity
        self.velocity *= self.drag_coefficient
        
        # Update position from keyboard-driven velocity
        self.position += self.velocity * dt
        
        # Apply wave drift as direct position offset (constant current, no fade)
        # This is NOT added to velocity, so it doesn't get dampened by drag
        if wave_state and wave_state.get('enabled', False):
            import math
            
            # Calculate spatial variation based on creature position
            x, y, z = self.position
            spatial_phase = x * 0.003 + z * 0.002
            spatial_factor = 1.0 + math.sin(spatial_phase) * 0.15
            
            # Get wave parameters
            wave_disp = wave_state.get('displacement', 0.0)
            wave_amp = wave_state.get('amplitude', 0.0)
            wave_dir_x = wave_state.get('dir_x', 0.0)
            wave_dir_z = wave_state.get('dir_z', 0.0)
            
            # Calculate wave drift as position offset (not velocity!)
            disp = wave_disp * spatial_factor
            wave_drift_x = disp * wave_amp * wave_dir_x
            wave_drift_z = disp * wave_amp * wave_dir_z
            
            # Apply drift directly to position (constant current effect)
            drift_speed = 8.0  # Units/sec drift speed
            self.position[0] += wave_drift_x * drift_speed * dt
            self.position[2] += wave_drift_z * drift_speed * dt
        
        # Clamp to bounds
        self.position = Gf.Vec3f(
            max(self.bounds_min[0], min(self.bounds_max[0], self.position[0])),
            max(self.bounds_min[1], min(self.bounds_max[1], self.position[1])),
            max(self.bounds_min[2], min(self.bounds_max[2], self.position[2]))
        )
        
        # Update mesh transform
        if self.translate_op:
            self.translate_op.Set(Gf.Vec3d(*self.position))
        
        # Update rotation based on intended velocity (player input only, ignores external forces)
        if self.rotate_op and self.intended_velocity.GetLength() > 1.0:  # Only rotate when moving
            import math
            
            # Calculate target rotation from intended velocity (keyboard input)
            # Use intended_velocity instead of actual velocity to ignore bubble collisions
            vx, vy, vz = self.intended_velocity[0], self.intended_velocity[1], self.intended_velocity[2]
            
            # Yaw (rotation around Y axis) - determines horizontal direction
            # In world space: +X is right, +Z is forward (away from camera default view)
            # atan2 gives angle from -Z axis (forward), positive = counterclockwise from above
            target_yaw = 90.0 - math.degrees(math.atan2(vz, vx))
            
            # Pitch (rotation around X axis) - determines up/down angle  
            # Positive pitch = nose up
            horizontal_dist = math.sqrt(vx*vx + vz*vz)
            
            # Get current rotation values first
            current_yaw = self.current_rotation[1]
            current_pitch = self.current_rotation[0]
            
            if horizontal_dist > 0.01:
                # Moving horizontally - calculate pitch from slope
                target_pitch = -math.degrees(math.atan2(vy, horizontal_dist))  # Negative to match axis orientation
            elif abs(vy) > 0.01:
                # Moving purely vertically - point straight up or down
                target_pitch = -90.0 if vy > 0 else 90.0  # Inverted signs to match orientation
            else:
                # Not moving - keep current pitch
                target_pitch = current_pitch
            
            # Smoothly interpolate rotation (damped rotation for smooth turning)
            lerp_factor = 0.2  # Slightly more responsive than 0.15
            
            # Handle yaw wraparound (shortest path)
            yaw_diff = target_yaw - current_yaw
            if yaw_diff > 180:
                yaw_diff -= 360
            elif yaw_diff < -180:
                yaw_diff += 360
            
            new_yaw = current_yaw + yaw_diff * lerp_factor
            new_pitch = current_pitch + (target_pitch - current_pitch) * lerp_factor
            
            self.current_rotation = Gf.Vec3f(new_pitch, new_yaw, 0)
            self.rotate_op.Set(self.current_rotation)
        
        # Check for bubble collisions
        popped_bubbles = []
        if bubble_positions and bubble_radii:
            for tendroid_name, bubble_pos in bubble_positions.items():
                bubble_radius = bubble_radii.get(tendroid_name, 0.0)
                if bubble_radius <= 0.0:
                    continue
                
                # Calculate distance between creature center and bubble center
                # Convert numpy types to Python floats for Gf.Vec3f
                bubble_vec = Gf.Vec3f(
                    float(bubble_pos[0]),
                    float(bubble_pos[1]),
                    float(bubble_pos[2])
                )
                distance_vec = self.position - bubble_vec
                distance = distance_vec.GetLength()
                
                # Collision if distance < sum of radii (with small overlap for true contact)
                # Use 0.9 factor so bubbles need to actually touch/overlap
                collision_distance = (self.creature_radius + bubble_radius) * 0.9
                if distance < collision_distance:
                    # Calculate collision direction (from bubble toward creature)
                    if distance > 0.01:  # Avoid division by zero
                        collision_direction = distance_vec / distance
                    else:
                        collision_direction = Gf.Vec3f(0, 1, 0)  # Default up if overlapping exactly
                    
                    # Apply gentle impulse to creature (bubble reaction)
                    bubble_impulse = 5.0  # Subtle but visible nudge
                    self.velocity += collision_direction * bubble_impulse
                    
                    popped_bubbles.append((tendroid_name, collision_direction))
                    
                    carb.log_info(
                        f"[Creature] Collision! Bubble at {tendroid_name} "
                        f"(distance: {distance:.1f}, threshold: {collision_distance:.1f})"
                    )
        
        # Check for tendroid interactions (avoidance and shock)
        tendroid_interactions = {}
        if tendroids:
            avoidance_epsilon = 30.0  # Distance at which tendroid starts reacting
            shock_impulse = 25.0  # Strength of shock effect
            
            for tendroid in tendroids:
                # Get tendroid center position
                tendroid_pos = Gf.Vec3f(*tendroid.position)
                
                # Calculate distance from creature to tendroid
                distance_vec = self.position - tendroid_pos
                distance = distance_vec.GetLength()
                
                # Skip if too far away
                if distance > avoidance_epsilon:
                    continue
                
                # Calculate approach velocity (creature velocity projected toward tendroid)
                if distance > 0.01:
                    direction_to_tendroid = -distance_vec / distance  # Negative because pointing toward
                    approach_velocity = self.velocity.GetDot(direction_to_tendroid)
                else:
                    approach_velocity = 0.0
                
                # Only react if creature is approaching (positive velocity toward tendroid)
                if approach_velocity > 0.1:
                    # Calculate avoidance factor (0.0 at epsilon, 1.0 at contact)
                    contact_distance = self.creature_radius + tendroid.radius
                    if distance > contact_distance:
                        # Avoidance range: epsilon → contact
                        avoidance_factor = 1.0 - ((distance - contact_distance) / (avoidance_epsilon - contact_distance))
                        avoidance_factor = max(0.0, min(1.0, avoidance_factor))
                        
                        # Direction tendroid should lean (away from creature)
                        avoidance_direction = distance_vec / distance  # Normalized away from creature
                        
                        tendroid_interactions[tendroid.name] = {
                            'type': 'avoidance',
                            'distance': distance,
                            'approach_velocity': approach_velocity,
                            'avoidance_factor': avoidance_factor,
                            'avoidance_direction': (avoidance_direction[0], avoidance_direction[1], avoidance_direction[2])
                        }
                    else:
                        # Contact! Apply shock to creature
                        shock_direction = distance_vec / distance if distance > 0.01 else Gf.Vec3f(0, 1, 0)
                        self.velocity += shock_direction * shock_impulse
                        
                        tendroid_interactions[tendroid.name] = {
                            'type': 'shock',
                            'distance': distance,
                            'shock_direction': (shock_direction[0], shock_direction[1], shock_direction[2])
                        }
                        
                        carb.log_info(
                            f"[Creature] Shocked by {tendroid.name}! "
                            f"(distance: {distance:.1f}, impulse: {shock_impulse})"
                        )
        
        return popped_bubbles, tendroid_interactions
    
    def _get_keyboard_state(self):
        """
        Get current keyboard input state.
        
        Returns:
            dict: Keyboard state with boolean flags for each direction
        """
        if not self.input_interface or self.keyboard is None:
            return {
                'forward': False, 'backward': False,
                'left': False, 'right': False,
                'up': False, 'down': False
            }
        
        # Poll keyboard state (no logging for performance)
        return {
            # Forward/Backward (W/S or Up/Down arrows)
            'forward': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.W) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.UP) != 0
            ),
            'backward': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.S) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.DOWN) != 0
            ),
            # Left/Right (A/D or Left/Right arrows)
            'left': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.A) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.LEFT) != 0
            ),
            'right': (
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.D) != 0 or
                self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.RIGHT) != 0
            ),
            # Up/Down (Space/Left Shift)
            'up': self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.SPACE) != 0,
            'down': self.input_interface.get_keyboard_value(self.keyboard, KeyboardInput.LEFT_SHIFT) != 0
        }
    
    def get_position(self):
        """Get current creature position."""
        return tuple(self.position)
    
    def get_radius(self):
        """Get creature collision radius."""
        return self.creature_radius
    
    def destroy(self):
        """Cleanup creature resources."""
        # Destroy collider first
        if hasattr(self, 'creature_prim_path') and self.stage:
            destroy_creature_collider(self.stage, self.creature_prim_path)
        
        # Destroy mesh
        if self.creature_prim and self.stage:
            prim_path = str(self.creature_prim.GetPath())
            if self.stage.GetPrimAtPath(prim_path):
                self.stage.RemovePrim(prim_path)
        
        carb.log_info("[CreatureController] Destroyed")
