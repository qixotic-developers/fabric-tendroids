"""
Terrain conforming helper for V2 Tendroid base vertices

Adjusts base flare vertices to follow sea floor terrain contours.
"""

import math
from pxr import Gf


def conform_base_to_terrain(
    vertices: list,
    base_position: tuple,
    flare_height: float,
    radial_segments: int,
    height_segments: int,
    get_height_fn
) -> list:
    """
    Adjust base vertices to conform to terrain height.
    
    Args:
        vertices: List of Gf.Vec3f vertices
        base_position: (x, y, z) world position of tendroid base
        flare_height: Height of flare section
        radial_segments: Number of vertices per ring
        height_segments: Total vertical segments
        get_height_fn: Function(x, z) -> height to query terrain
    
    Returns:
        Modified vertex list with terrain-conforming base
    """
    if not vertices or radial_segments <= 0:
        return vertices
    
    # Calculate segment height
    total_height = vertices[-1][1] if vertices else 0
    segment_height = total_height / height_segments if height_segments > 0 else 1.0
    
    # Calculate which segments are in the flare zone
    flare_segments = int(math.ceil(flare_height / segment_height)) if segment_height > 0 else 0
    flare_segments = min(flare_segments, height_segments)
    
    # Convert to mutable list
    modified_vertices = [Gf.Vec3f(v) for v in vertices]
    
    # Process each ring in the flare zone
    for seg_idx in range(flare_segments + 1):
        ring_start = seg_idx * radial_segments
        
        # Blend factor: bottom = full conform, top of flare = no conform
        if flare_segments > 0:
            blend = 1.0 - (seg_idx / flare_segments)
            blend = blend * blend  # Quadratic falloff for smooth transition
        else:
            blend = 0.0
        
        # For each vertex in the ring
        for i in range(radial_segments):
            vert_idx = ring_start + i
            if vert_idx >= len(vertices):
                break
                
            local_vert = vertices[vert_idx]
            
            # Convert to world coordinates
            world_x = base_position[0] + local_vert[0]
            world_z = base_position[2] + local_vert[2]
            
            # Query terrain height at this position
            terrain_height = get_height_fn(world_x, world_z)
            
            # Calculate terrain offset relative to base
            original_y = local_vert[1]
            terrain_offset = terrain_height - base_position[1]
            
            # Apply terrain height with blend
            final_y = original_y + (terrain_offset * blend)
            
            modified_vertices[vert_idx] = Gf.Vec3f(
                local_vert[0],
                final_y,
                local_vert[2]
            )
    
    return modified_vertices
