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
        
        # Scene bounds (matches 800x800 sea floor)
        self.bounds_min = Gf.Vec3f(-400, 10, -400)
        self.bounds_max = Gf.Vec3f(400, 90, 400)
        
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
        
        # Create creature mesh
        self.creature_prim = self._create_creature_mesh()
        
        carb.log_info(
            f"[CreatureController] Initialized at {start_position}, "
            f"radius={self.creature_radius}, length={self.creature_length}"
        )
    
    def _create_creature_mesh(self):
        """Create simple cylinder placeholder mesh."""
        path = "/World/Creature"
        
        # Remove existing if present
        if self.stage.GetPrimAtPath(path):
            self.stage.RemovePrim(path)
        
        # Create cylinder
        cylinder = UsdGeom.Cylinder.Define(self.stage, path)
        
        # Set dimensions
        cylinder.CreateRadiusAttr().Set(self.creature_radius)
        cylinder.CreateHeightAttr().Set(self.creature_length)
        cylinder.CreateAxisAttr().Set("Z")  # Align length with Z-axis
        
        # Create xformOps for position and rotation
        xformable = UsdGeom.Xformable(cylinder)
        self.translate_op = xformable.AddTranslateOp()
        self.rotate_op = xformable.AddRotateXYZOp()
        
        # Set initial position
        self.translate_op.Set(Gf.Vec3d(*self.position))
        
        # Rotate to horizontal (swimming orientation)
        # Cylinder axis is Z, rotate 90° around Y to align with X-axis
        self.rotate_op.Set(Gf.Vec3f(0, 90, 0))
        
        # Create simple material (bright color for visibility)
        material_path = "/World/Materials/Creature"
        material = UsdShade.Material.Define(self.stage, material_path)
        
        # Simple preview surface shader
        shader = UsdShade.Shader.Define(
            self.stage,
            f"{material_path}/PreviewSurface"
        )
        shader.CreateIdAttr("UsdPreviewSurface")
        
        # Import Sdf for type names
        from pxr import Sdf
        
        # Create shader inputs with proper type specification
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(0.2, 0.8, 0.9)  # Cyan
        )
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.3)
        
        material.CreateSurfaceOutput().ConnectToSource(
            shader.ConnectableAPI(), "surface"
        )
        
        # Bind material
        UsdShade.MaterialBindingAPI(cylinder).Bind(material)
        
        return cylinder.GetPrim()
    
    def update(self, dt: float):
        """
        Update creature physics and position.
        
        Args:
            dt: Delta time in seconds
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
        
        # Apply acceleration to velocity
        self.velocity += acceleration
        
        # Clamp speed
        speed = self.velocity.GetLength()
        if speed > self.max_speed:
            self.velocity = self.velocity.GetNormalized() * self.max_speed
        
        # Apply drag
        self.velocity *= self.drag_coefficient
        
        # Update position
        self.position += self.velocity * dt
        
        # Clamp to bounds
        self.position = Gf.Vec3f(
            max(self.bounds_min[0], min(self.bounds_max[0], self.position[0])),
            max(self.bounds_min[1], min(self.bounds_max[1], self.position[1])),
            max(self.bounds_min[2], min(self.bounds_max[2], self.position[2]))
        )
        
        # Update mesh transform
        if self.translate_op:
            self.translate_op.Set(Gf.Vec3d(*self.position))
        
        # Debug: Log position changes (remove after testing)
        if self.velocity.GetLength() > 0.1:
            carb.log_info(
                f"[Creature] Pos: ({self.position[0]:.1f}, {self.position[1]:.1f}, {self.position[2]:.1f}) "
                f"Vel: {self.velocity.GetLength():.1f}"
            )
    
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
        if self.creature_prim and self.stage:
            prim_path = str(self.creature_prim.GetPath())
            if self.stage.GetPrimAtPath(prim_path):
                self.stage.RemovePrim(prim_path)
        
        carb.log_info("[CreatureController] Destroyed")
