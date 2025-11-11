"""
Tube Geometry Helper

Mathematical functions for creating swept torus tube geometry.
Provides proper tube topology with consistent wall thickness.
"""

import math
import numpy as np
from pxr import Gf
from typing import Tuple, List


def generate_tube_geometry(
    height: float,
    major_radius: float,
    minor_radius: float,
    height_segments: int,
    radial_segments: int,
    wall_segments: int
) -> Tuple[List[Gf.Vec3f], List[int], List[int], List[Gf.Vec3f]]:
    """
    Generate swept torus tube with proper manifold topology.
    
    Creates a tube by sweeping a circular cross-section along height,
    with the cross-section itself rotating around a major radius.
    
    Returns:
        Tuple of (positions, face_indices, face_counts, centerline_positions)
    """
    positions = []
    face_indices = []
    face_counts = []
    centerline = []
    
    # Generate vertices
    for h in range(height_segments + 1):
        y = (h / height_segments) * height
        
        # Store centerline for deformation reference
        centerline.append(Gf.Vec3f(0, y, 0))
        
        for r in range(radial_segments):
            theta = (r / radial_segments) * 2.0 * math.pi
            
            # Center of tube wall at this angle
            cx = major_radius * math.cos(theta)
            cz = major_radius * math.sin(theta)
            
            for w in range(wall_segments):
                phi = (w / wall_segments) * 2.0 * math.pi
                
                # Offset from wall center (perpendicular to tube surface)
                offset_r = minor_radius * math.cos(phi)
                offset_y = minor_radius * math.sin(phi)
                
                x = cx + offset_r * math.cos(theta)
                z = cz + offset_r * math.sin(theta)
                y_final = y + offset_y
                
                positions.append(Gf.Vec3f(x, y_final, z))
    
    # Generate face indices
    # Need to connect both:
    # 1. Around wall cross-section (w dimension)
    # 2. Around tube circumference (r dimension)
    # 3. Along height (h dimension)
    
    verts_per_ring = radial_segments * wall_segments
    
    for h in range(height_segments):
        for r in range(radial_segments):
            next_r = (r + 1) % radial_segments
            
            for w in range(wall_segments):
                next_w = (w + 1) % wall_segments
                
                # Quad connecting this wall segment to next along height
                i0 = h * verts_per_ring + r * wall_segments + w
                i1 = h * verts_per_ring + r * wall_segments + next_w
                i2 = (h + 1) * verts_per_ring + r * wall_segments + next_w
                i3 = (h + 1) * verts_per_ring + r * wall_segments + w
                
                face_indices.extend([i0, i1, i2, i3])
                face_counts.append(4)
                
                # Quad connecting this radial segment to next around circumference
                i0 = h * verts_per_ring + r * wall_segments + w
                i1 = (h + 1) * verts_per_ring + r * wall_segments + w
                i2 = (h + 1) * verts_per_ring + next_r * wall_segments + w
                i3 = h * verts_per_ring + next_r * wall_segments + w
                
                face_indices.extend([i0, i1, i2, i3])
                face_counts.append(4)
    
    return positions, face_indices, face_counts, centerline


def compute_tube_deformation_offset(
    base_position: np.ndarray,
    frame: int,
    wave_speed: float,
    wave_amplitude: float
) -> np.ndarray:
    """
    Compute deformation offset for tube vertex.
    
    Applies wave along height while maintaining tube structure.
    """
    y = base_position[1]
    wave = math.sin(y * 0.1 + frame * wave_speed) * wave_amplitude
    
    # Offset radially, not just in X
    angle = math.atan2(base_position[2], base_position[0])
    offset_x = wave * math.cos(angle)
    offset_z = wave * math.sin(angle)
    
    return np.array([offset_x, 0.0, offset_z], dtype=np.float32)
