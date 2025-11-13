"""
Tube Deformation Helper

Handles warp-based deformation of swept torus tube geometry.
"""

import numpy as np
from typing import List
from pxr import UsdGeom
from .warp_kernels import WarpKernelManager


def apply_tube_deformation(
    mesh_prims: List[UsdGeom.Mesh],
    base_positions: List[np.ndarray],
    warp_manager: WarpKernelManager,
    frame: int,
    wave_amplitude: float = 2.0,
    wave_speed: float = 0.05
):
    """
    Apply warp deformation to tube geometry.
    
    Deforms tube while maintaining topology integrity.
    Uses radial wave pattern to preserve tube structure.
    """
    if not mesh_prims or not base_positions:
        return
        
    for idx, (mesh, base_pos) in enumerate(zip(mesh_prims, base_positions)):
        deformed = compute_tube_wave_deformation(
            base_pos,
            frame,
            wave_speed,
            wave_amplitude
        )
        
        warp_manager.update_mesh_positions(mesh, deformed)


def compute_tube_wave_deformation(
    base_positions: np.ndarray,
    frame: int,
    wave_speed: float,
    wave_amplitude: float
) -> np.ndarray:
    """
    Compute wave deformation for entire tube mesh.
    
    Applies traveling wave along tube height while
    maintaining radial symmetry and topology.
    """
    deformed = base_positions.copy()
    
    for i in range(len(base_positions)):
        pos = base_positions[i]
        y = pos[1]
        
        # Traveling wave along height
        wave_phase = y * 0.1 + frame * wave_speed
        wave_offset = np.sin(wave_phase) * wave_amplitude
        
        # Apply radially to maintain tube structure
        angle = np.arctan2(pos[2], pos[0])
        offset_x = wave_offset * np.cos(angle)
        offset_z = wave_offset * np.sin(angle)
        
        deformed[i][0] += offset_x
        deformed[i][2] += offset_z
        
    return deformed


def setup_tube_buffers(
    mesh_prims: List[UsdGeom.Mesh]
) -> List[np.ndarray]:
    """
    Extract base positions from tube meshes.
    
    Returns:
        List of numpy arrays with base vertex positions
    """
    base_positions = []
    
    for mesh in mesh_prims:
        points_attr = mesh.GetPointsAttr()
        if not points_attr:
            continue
            
        base_points = points_attr.Get()
        positions = np.array(
            [[p[0], p[1], p[2]] for p in base_points],
            dtype=np.float32
        )
        base_positions.append(positions)
        
    return base_positions


def validate_tube_topology(
    points: List,
    indices: List[int],
    radial_segments: int,
    height_segments: int
) -> bool:
    """
    Validate tube mesh topology.
    
    Ensures proper manifold structure with no gaps or overlaps.
    """
    expected_verts = (height_segments + 1) * radial_segments * radial_segments
    expected_faces = height_segments * radial_segments * radial_segments
    
    if len(points) != expected_verts:
        return False
        
    if len(indices) != expected_faces * 4:  # Quads
        return False
        
    return True
