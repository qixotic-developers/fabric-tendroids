"""
Core Tendroid class - manages a single Tendroid creature

Coordinates geometry, animation, and Fabric updates for one Tendroid.
"""

import carb
import omni.usd
from pxr import Gf, UsdGeom, Sdf
from .cylinder_generator import CylinderGenerator
from ..animation.breathing import BreathingAnimator
from ..animation.idle_motion import IdleMotionAnimator

try:
    from usdrt import Usd as RtUsd, UsdGeom as RtUsdGeom
    FABRIC_AVAILABLE = True
except ImportError:
    FABRIC_AVAILABLE = False
    RtUsd = None  # Add this
    RtUsdGeom = None  # Add this
carb.log_warn("[Tendroid] Fabric/USDRT not available, using standard USD")


class Tendroid:
    """
    A single Tendroid creature with geometry and animation.
    
    Manages the full lifecycle of a Tendroid including creation,
    animation updates, and cleanup.
    """

    def __init__(
        self,
        name: str,
        position: tuple = (0, 0, 0),
        radius: float = 10.0,
        length: float = 100.0,
        num_segments: int = 16,
        radial_resolution: int = 16
    ):
        """
        Initialize Tendroid (does not create geometry yet).
        
        Args:
            name: Unique name for this Tendroid
            position: (x, y, z) position in world space
            radius: Cylinder radius
            length: Total length
            num_segments: Number of segments for animation
            radial_resolution: Number of vertices around circumference
        """
        self.name = name
        self.position = position
        self.radius = radius
        self.length = length
        self.num_segments = num_segments
        self.radial_resolution = radial_resolution
        
        # USD paths and references
        self.base_path = None
        self.segment_xforms = []  # List of UsdGeom.Xform prims
        self.segment_paths = []
        
        # Fabric references
        self._rt_stage = None
        self._rt_xforms = []
        
        # Animation
        self.flare_height = length * 0.1  # 10% flare
        self.breathing_animator = BreathingAnimator(
            length=length,
            num_segments=num_segments,
            flare_height=self.flare_height
        )
        self.idle_animator = IdleMotionAnimator()
        
        # State
        self.is_created = False
        self.is_active = True
        
        carb.log_info(f"[Tendroid] Initialized '{name}' at {position}")

    def create(self, stage, parent_path: str = "/World/Tendroids") -> bool:
        """
        Create Tendroid geometry and setup in the USD stage.
        
        Creates a segmented cylinder where each segment is a separate mesh
        with its own Xform parent for transform-based animation.
        
        Args:
            stage: USD stage to create in
            parent_path: Parent path for this Tendroid
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create base Xform for the Tendroid
            self.base_path = f"{parent_path}/{self.name}"
            base_xform = UsdGeom.Xform.Define(stage, self.base_path)
            
            # Set world position
            base_xform.AddTranslateOp().Set(Gf.Vec3d(*self.position))
            
            # Calculate segment dimensions
            segment_length = self.length / self.num_segments
            
            # Create segments from bottom to top
            for i in range(self.num_segments):
                segment_name = f"segment_{i:02d}"
                segment_xform_path = f"{self.base_path}/{segment_name}"
                segment_mesh_path = f"{segment_xform_path}/mesh"
                
                # Create Xform for this segment
                segment_xform = UsdGeom.Xform.Define(stage, segment_xform_path)
                
                # Position segment vertically
                segment_y_position = i * segment_length
                segment_xform.AddTranslateOp().Set(Gf.Vec3d(0, segment_y_position, 0))
                
                # Add scale operation (we'll modify this during animation)
                scale_op = segment_xform.AddScaleOp()
                scale_op.Set(Gf.Vec3f(1.0, 1.0, 1.0))
                
                # Calculate flare for this segment (only bottom segments)
                segment_center_y = segment_y_position + segment_length / 2
                if segment_center_y <= self.flare_height:
                    # This segment is in the flare region
                    flare_amount = 1.5  # 50% wider at base
                else:
                    flare_amount = 1.0
                
                # Create cylinder mesh for this segment
                mesh_prim, _, _ = CylinderGenerator.create_cylinder(
                    stage=stage,
                    path=segment_mesh_path,
                    radius=self.radius * flare_amount,
                    length=segment_length,
                    num_segments=1,  # Single segment (no subdivision needed)
                    radial_resolution=self.radial_resolution,
                    flare_radius_multiplier=1.0,  # No flare per-segment (handled by positioning)
                    flare_height_percent=0.0
                )
                
                # Store references
                self.segment_xforms.append(segment_xform)
                self.segment_paths.append(segment_xform_path)
            
            # Setup Fabric if available
            if FABRIC_AVAILABLE:
                self._setup_fabric()
            
            self.is_created = True
            carb.log_info(
                f"[Tendroid] Created '{self.name}' with {self.num_segments} segments "
                f"at {self.base_path}"
            )
            return True
            
        except Exception as e:
            carb.log_error(f"[Tendroid] Failed to create '{self.name}': {e}")
            import traceback
            traceback.print_exc()
            return False

    def _setup_fabric(self):
        """Setup Fabric/USDRT references for fast updates."""
        try:
            ctx = omni.usd.get_context()
            if not ctx:
                return
                
            stage_id = ctx.get_stage_id()
            self._rt_stage = RtUsd.Stage.Attach(stage_id)
            
            # Get Fabric references to segment Xforms for fast transform updates
            for segment_path in self.segment_paths:
                try:
                    rt_xform = RtUsdGeom.Xform(self._rt_stage.GetPrimAtPath(segment_path))
                    self._rt_xforms.append(rt_xform)
                except Exception as e:
                    carb.log_warn(f"[Tendroid] Could not get Fabric reference for {segment_path}: {e}")
                    self._rt_xforms.append(None)
            
            carb.log_info(f"[Tendroid] Fabric setup complete for '{self.name}'")
            
        except Exception as e:
            carb.log_warn(f"[Tendroid] Fabric setup failed for '{self.name}': {e}")

    def update(self, dt: float):
        """
        Update Tendroid animation for current frame.
        
        Applies breathing animation (radial scaling) and idle motion (swaying)
        to the Tendroid's segments.
        
        Args:
            dt: Delta time since last update (seconds)
        """
        if not self.is_created or not self.is_active:
            return
        
        try:
            # Update breathing animation - get scale factors for each segment
            segment_scales = self.breathing_animator.update(dt)

            # Update idle motion - get sway rotation and offset for base
            idle_motion = self.idle_animator.update(dt)

            # Apply segment scales (radial expansion/contraction)
            self._apply_segment_scales(segment_scales)

            # Apply idle motion to base (subtle swaying)
            self._apply_idle_motion(idle_motion['rotation'])

            # Check for bubble emission
            if self.breathing_animator.should_emit_bubble():
                self._emit_bubble()
                
        except Exception as e:
            carb.log_error(f"[Tendroid] Update failed for '{self.name}': {e}")

    def _apply_segment_scales(self, segment_scales: list):
        """
        Apply radial scale factors to each segment.
        
        Args:
            segment_scales: List of scale factors (one per segment)
        """
        if len(segment_scales) != len(self.segment_xforms):
            carb.log_error(
                f"[Tendroid] Scale count mismatch: "
                f"{len(segment_scales)} scales for {len(self.segment_xforms)} segments"
            )
            return
        
        # Use Fabric if available for performance, otherwise use standard USD
        if FABRIC_AVAILABLE and len(self._rt_xforms) == len(segment_scales):
            self._apply_scales_fabric(segment_scales)
        else:
            self._apply_scales_usd(segment_scales)

    def _apply_scales_fabric(self, segment_scales: list):
        """Apply scales using Fabric/USDRT (fast path)."""
        for i, (rt_xform, scale) in enumerate(zip(self._rt_xforms, segment_scales)):
            if rt_xform is None:
                continue
            try:
                # Apply radial scale (X and Z only, preserve Y height)
                # Apply radial scale (X and Z only, preserve Y height)
                scale_vec = Gf.Vec3f(scale, 1.0, scale)
                # Get scale attribute and set
                xformable = RtUsdGeom.Xformable(rt_xform)
                ops = xformable.GetOrderedXformOps()
                
                # Find the scale op (should be last one we created)
                for op in ops:
                    if op.GetOpType() == UsdGeom.XformOp.TypeScale:
                      op.Set(tuple(scale_vec))
                      break
                        
            except Exception as e:
                if i == 0:  # Only log first error to avoid spam
                    carb.log_warn(f"[Tendroid] Fabric scale update failed: {e}")

    def _apply_scales_usd(self, segment_scales: list):
        """Apply scales using standard USD (fallback path)."""
        for i, (segment_xform, scale) in enumerate(zip(self.segment_xforms, segment_scales)):
            try:
                # Apply radial scale (X and Z only, preserve Y height)
                scale_vec = Gf.Vec3f(scale, 1.0, scale)
                
                # Find the scale operation
                ops = segment_xform.GetOrderedXformOps()
                for op in ops:
                    if op.GetOpType() == UsdGeom.XformOp.TypeScale:
                        op.Set(scale_vec)
                        break
                        
            except Exception as e:
                if i == 0:  # Only log first error to avoid spam
                    carb.log_warn(f"[Tendroid] USD scale update failed: {e}")

    def _apply_idle_motion(self, rotation: tuple):
        """
        Apply idle motion (swaying) to the base Xform.
        
        Args:
            rotation: (x, y, z) rotation angles in degrees
        """
        if not self.base_path:
            return
        
        try:
            # Get base Xform
            ctx = omni.usd.get_context()
            stage = ctx.get_stage()
            base_prim = stage.GetPrimAtPath(self.base_path)
            base_xform = UsdGeom.Xform(base_prim)
            
            # Find or create rotation operation
            ops = base_xform.GetOrderedXformOps()
            rotate_op = None
            
            for op in ops:
                if op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ:
                    rotate_op = op
                    break
            
            if not rotate_op:
                # Create rotation operation if it doesn't exist
                rotate_op = base_xform.AddRotateXYZOp()
            
            # Apply rotation
            rotate_op.Set(Gf.Vec3f(*rotation))
            
        except Exception as e:
            carb.log_warn(f"[Tendroid] Idle motion update failed: {e}")

    def _emit_bubble(self):
        """Emit a bubble from the top of the Tendroid."""
        # TODO: Implement bubble creation in Phase 2
        carb.log_info(f"[Tendroid] '{self.name}' emitting bubble!")

    def set_active(self, active: bool):
        """Enable or disable this Tendroid's animation."""
        self.is_active = active
        self.idle_animator.set_enabled(active)

    def set_breathing_parameters(
        self,
        wave_speed: float = None,
        wave_length: float = None,
        amplitude: float = None,
        cycle_delay: float = None
    ):
        """
        Update breathing animation parameters at runtime.
        
        Args:
            wave_speed: Wave travel speed (units/second)
            wave_length: Length of the breathing wave
            amplitude: Maximum expansion factor (e.g., 0.3 = 30%)
            cycle_delay: Delay between cycles (seconds)
        """
        self.breathing_animator.set_parameters(
            wave_speed=wave_speed,
            wave_length=wave_length,
            amplitude=amplitude,
            cycle_delay=cycle_delay
        )

    def destroy(self, stage):
        """
        Remove this Tendroid from the stage.
        
        Args:
            stage: USD stage to remove from
        """
        if self.base_path:
            try:
                stage.RemovePrim(self.base_path)
                carb.log_info(f"[Tendroid] Destroyed '{self.name}'")
            except Exception as e:
                carb.log_error(f"[Tendroid] Failed to destroy '{self.name}': {e}")
        
        self.is_created = False
        self.segment_xforms = []
        self.segment_paths = []
        self._rt_stage = None
        self._rt_xforms = []

    def get_top_position(self) -> tuple:
        """
        Get world position of the Tendroid's top (for bubble emission).
        
        Returns:
            (x, y, z) position of the top
        """
        return (
            self.position[0],
            self.position[1] + self.length,
            self.position[2]
        )
