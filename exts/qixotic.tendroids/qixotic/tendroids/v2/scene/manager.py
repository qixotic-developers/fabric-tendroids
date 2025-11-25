"""
V2 Scene Manager - High-level coordinator for tendroids and bubbles

Orchestrates scene creation, animation, and cleanup.
GPU-accelerated bubble physics integrated for maximum performance.
"""

import carb
import omni.usd
from pxr import UsdGeom

from .animation_controller import V2AnimationController
from .tendroid_factory import V2TendroidFactory
from .tendroid_wrapper import V2TendroidWrapper
from ..core import V2WarpDeformer
from ..environment import SeaFloorController, get_height_at
from ..bubbles import V2BubbleManager
from ..bubbles import create_gpu_bubble_system, BubblePhysicsAdapter


class V2SceneManager:
    """
    High-level scene coordinator for V2 Tendroids.

    Manages tendroid creation, bubble system, and animation.
    Now supports GPU-accelerated bubble physics for 10x+ performance.
    """

    def __init__(self):
        """Initialize scene manager."""
        self.tendroids = []
        self.tendroid_data = []
        self.bubble_manager = None
        self.animation_controller = V2AnimationController()
        self._sea_floor_created = False
        
        # GPU bubble physics
        self.use_gpu_bubbles = True  # Feature flag
        self.gpu_bubble_adapter = None

    def _ensure_sea_floor(self, stage):
        """Create sea floor if not present."""
        if not self._sea_floor_created and stage:
            try:
                SeaFloorController.create_sea_floor(stage)
                self._sea_floor_created = True
            except Exception as e:
                carb.log_error(f"[V2SceneManager] Sea floor failed: {e}")

    def _ensure_parent_prim(self, stage, path: str):
        """Ensure parent prim exists."""
        if not stage.GetPrimAtPath(path):
            UsdGeom.Xform.Define(stage, path)
    
    def _initialize_gpu_bubbles(self):
        """Initialize GPU bubble system after tendroids are created."""
        if not self.use_gpu_bubbles or not self.tendroids:
            return
        
        try:
            from ..bubbles import V2BubbleConfig, DEFAULT_V2_BUBBLE_CONFIG
            config = DEFAULT_V2_BUBBLE_CONFIG
            
            self.gpu_bubble_adapter = create_gpu_bubble_system(
                self.tendroids,
                config
            )
            
            # Pass GPU adapter to animation controller
            self.animation_controller.set_gpu_bubble_adapter(self.gpu_bubble_adapter)
            
            carb.log_info(
                f"[GPU] Bubble physics initialized for {len(self.tendroids)} tendroids"
            )
        except Exception as e:
            carb.log_error(f"[GPU] Failed to initialize bubbles: {e}")
            self.use_gpu_bubbles = False

    def create_tendroids(
        self,
        count: int = None,
        spawn_area: tuple = None,
        radius_range: tuple = None,
        radial_segments: int = 24,
        height_segments: int = 48
    ) -> bool:
        """Create multiple tendroids in the scene."""
        try:
            ctx = omni.usd.get_context()
            if not ctx:
                carb.log_error("[V2SceneManager] No USD context")
                return False

            stage = ctx.get_stage()
            if not stage:
                carb.log_error("[V2SceneManager] No USD stage")
                return False

            self._ensure_sea_floor(stage)
            self._ensure_parent_prim(stage, "/World/Tendroids")
            self.clear_tendroids(stage)

            self.tendroid_data = V2TendroidFactory.create_batch(
                stage=stage,
                count=count,
                spawn_area=spawn_area,
                radius_range=radius_range,
                radial_segments=radial_segments,
                height_segments=height_segments,
                get_height_fn=get_height_at
            )

            self.tendroids = []
            for data in self.tendroid_data:
                tendroid = self._create_warp_tendroid(stage, data)
                if tendroid:
                    self.tendroids.append(tendroid)

            self.animation_controller.set_tendroids(
                self.tendroids,
                self.tendroid_data
            )

            self.bubble_manager = V2BubbleManager(stage)
            for tendroid in self.tendroids:
                self.bubble_manager.register_tendroid(tendroid)
            self.animation_controller.set_bubble_manager(self.bubble_manager)
            
            # Initialize GPU bubbles after everything is set up
            if self.use_gpu_bubbles:
                self._initialize_gpu_bubbles()

            carb.log_info(
                f"[V2SceneManager] Created {len(self.tendroids)} tendroids"
            )
            return True

        except Exception as e:
            carb.log_error(f"[V2SceneManager] Create failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_warp_tendroid(self, stage, data: dict):
        """Create V2WarpTendroid from builder data."""
        try:
            deformer = V2WarpDeformer(
                base_points_list=data['base_points'],
                cylinder_radius=data['radius'],
                cylinder_length=data['length'],
                max_amplitude=data.get('max_amplitude', 0.8),
                bulge_width=data.get('bulge_width', 0.9)
            )

            tendroid = V2TendroidWrapper(
                name=data['name'],
                position=data['position'],
                radius=data['radius'],
                length=data['length'],
                mesh_prim=data['mesh_prim'],
                deformer=deformer,
                deform_start_height=data['deform_start_height'],
                flare_height=data.get('flare_height', 0.0)
            )

            return tendroid

        except Exception as e:
            carb.log_error(
                f"[V2SceneManager] Warp tendroid failed for {data['name']}: {e}"
            )
            return None

    def create_single_tendroid(
        self,
        position: tuple = (0, 0, 0),
        radius: float = 10.0,
        length: float = 100.0,
        radial_segments: int = 24,
        height_segments: int = 48
    ) -> bool:
        """Create a single tendroid at specified position."""
        try:
            ctx = omni.usd.get_context()
            if not ctx:
                return False

            stage = ctx.get_stage()
            if not stage:
                return False

            self._ensure_sea_floor(stage)
            self._ensure_parent_prim(stage, "/World/Tendroids")
            self.clear_tendroids(stage)

            from ..builders import V2TendroidBuilder
            data = V2TendroidBuilder.create_tendroid(
                stage=stage,
                name="Tendroid_Single",
                position=position,
                radius=radius,
                length=length,
                radial_segments=radial_segments,
                height_segments=height_segments,
                get_height_fn=get_height_at
            )

            if data:
                self.tendroid_data = [data]
                tendroid = self._create_warp_tendroid(stage, data)
                if tendroid:
                    self.tendroids = [tendroid]
                    self.animation_controller.set_tendroids(
                        self.tendroids,
                        self.tendroid_data
                    )
                    return True

            return False

        except Exception as e:
            carb.log_error(f"[V2SceneManager] Single create failed: {e}")
            return False

    def start_animation(self, enable_profiling: bool = False):
        """Start animation loop."""
        self.animation_controller.start(enable_profiling=enable_profiling)

    def stop_animation(self):
        """Stop animation loop."""
        self.animation_controller.stop()

    def clear_tendroids(self, stage=None):
        """Remove all tendroids from scene."""
        if not stage:
            ctx = omni.usd.get_context()
            if ctx:
                stage = ctx.get_stage()

        if stage:
            for data in self.tendroid_data:
                base_path = data.get('base_path')
                if base_path:
                    prim = stage.GetPrimAtPath(base_path)
                    if prim.IsValid():
                        stage.RemovePrim(base_path)

        for tendroid in self.tendroids:
            if hasattr(tendroid, 'deformer') and tendroid.deformer:
                tendroid.deformer.destroy()

        if self.bubble_manager:
            self.bubble_manager.clear_all()
            self.bubble_manager = None
        
        # Clean up GPU resources
        if self.gpu_bubble_adapter:
            self.gpu_bubble_adapter.destroy()
            self.gpu_bubble_adapter = None

        self.tendroids.clear()
        self.tendroid_data.clear()
        self.animation_controller.set_tendroids([], [])

    def get_tendroid_count(self) -> int:
        """Get active tendroid count."""
        return len(self.tendroids)

    def get_profile_data(self):
        """Get profiling data from animation controller."""
        return self.animation_controller.get_profile_data()

    def shutdown(self):
        """Cleanup on shutdown."""
        self.animation_controller.shutdown()
        
        # Clean up GPU resources
        if self.gpu_bubble_adapter:
            self.gpu_bubble_adapter.destroy()
            self.gpu_bubble_adapter = None
        
        ctx = omni.usd.get_context()
        if ctx:
            stage = ctx.get_stage()
            if stage:
                self.clear_tendroids(stage)
