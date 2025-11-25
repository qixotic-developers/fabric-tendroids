"""
V2 Bubbles - Bubble-driven deformation system

Bubbles rise inside tendroids, driving the bulge deformation.
Sphere geometry uses vertex-down orientation for smooth exit transitions.

GPU-accelerated physics available via bubble_physics module.
"""

from .bubble import V2Bubble
from .bubble_visual import V2BubbleVisual
from .bubble_config import V2BubbleConfig, DEFAULT_V2_BUBBLE_CONFIG
from .bubble_manager import V2BubbleManager
from .sphere_geometry_helper import (
    create_uv_sphere_points,
    create_sphere_face_indices,
    create_sphere_mesh,
)
from .pop_particle import PopParticle, PopParticleManager

# GPU-accelerated bubble physics
from .bubble_gpu_manager import BubbleGPUManager
from .bubble_physics_adapter import BubblePhysicsAdapter, create_gpu_bubble_system

__all__ = [
    "V2Bubble",
    "V2BubbleVisual",
    "V2BubbleConfig",
    "DEFAULT_V2_BUBBLE_CONFIG",
    "V2BubbleManager",
    "create_uv_sphere_points",
    "create_sphere_face_indices",
    "create_sphere_mesh",
    "PopParticle",
    "PopParticleManager",
    # GPU acceleration
    "BubbleGPUManager",
    "BubblePhysicsAdapter",
    "create_gpu_bubble_system",
]
