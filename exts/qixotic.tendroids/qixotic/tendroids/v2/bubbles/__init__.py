"""
V2 Bubbles - Bubble-driven deformation system

Bubbles rise inside tendroids, driving the bulge deformation.
Sphere geometry uses vertex-down orientation for smooth exit transitions.
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
]
