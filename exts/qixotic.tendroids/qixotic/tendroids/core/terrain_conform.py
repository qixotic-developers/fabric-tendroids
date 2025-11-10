"""
Terrain conforming helper for Tendroid base vertices

Adjusts base flare vertices to follow terrain contours.
"""

import carb
import math
from pxr import Gf
from ..sea_floor import get_height_at


def conform_base_to_terrain(
    vertices: list,
    base_position: tuple,
    flare_height: float,
    num_segments: int,
    radial_resolution: int
) -> list:
    """
    Adjust base vertices to conform to terrain height.
    
    Args:
        vertices: List of Vec3f vertices
        base_position: (x, y, z) world position of tendroid base
        flare_height: Height of flare section
        num_segments: Number of vertical segments
        radial_resolution: Number of vertices per ring
    
    Returns:
        Modified vertex list with terrain-conforming base
    """
    # Calculate which segments are in the flare zone
    segment_height = vertices[radial_resolution][1] - vertices[0][1]
    flare_segments = int(math.ceil(flare_height / segment_height))
    
    carb.log_info(
        f"[TerrainConform] Conforming {flare_segments} base segments "
        f"to terrain at ({base_position[0]:.1f}, {base_position[2]:.1f})"
    )
    
    # Convert to mutable list
    modified_vertices = [Gf.Vec3f(v) for v in vertices]
    
    heights_sampled = []
    
    # Process each ring in the flare zone
    for seg_idx in range(flare_segments + 1):
        ring_start = seg_idx * radial_resolution
        
        # For each vertex in the ring
        for i in range(radial_resolution):
            vert_idx = ring_start + i
            local_vert = vertices[vert_idx]
            
            # Convert to world coordinates
            world_x = base_position[0] + local_vert[0]
            world_z = base_position[2] + local_vert[2]
            
            # Query terrain height at this position
            terrain_height = get_height_at(world_x, world_z)
            
            # Calculate blend factor (bottom = full conform, top = no conform)
            blend = 1.0 - (seg_idx / flare_segments)
            blend = blend * blend  # Quadratic falloff for smooth transition
            
            # Apply terrain height with blend
            original_y = local_vert[1]
            conformed_y = terrain_height - base_position[1]  # Convert to local
            final_y = original_y + (conformed_y * blend)
            
            modified_vertices[vert_idx] = Gf.Vec3f(
                local_vert[0],
                final_y,
                local_vert[2]
            )
            
            if i == 0:  # Track one sample per ring for logging
                heights_sampled.append(terrain_height)
    
    # Log height range for verification
    if heights_sampled:
        min_h = min(heights_sampled)
        max_h = max(heights_sampled)
        carb.log_info(
            f"[TerrainConform] Base height range: "
            f"[{min_h:.2f}, {max_h:.2f}]"
        )
    
    return modified_vertices
