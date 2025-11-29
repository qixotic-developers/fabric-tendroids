"""
Sphere geometry helper with vertex-down rotation option.

Generates UV sphere mesh with configurable orientation to eliminate
the "snap" artifact when bubbles exit the cylinder. Standard UV spheres
have pole topology at top/bottom; rotating 90 degrees around X-axis
puts smooth quad geometry at the bottom instead.
"""

import math
from pxr import Gf, UsdGeom


def _rotate_around_x_axis(x: float, y: float, z: float, angle: float) -> tuple:
    """Rotate a point around the X-axis by given angle in radians."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    new_y = y * cos_a - z * sin_a
    new_z = y * sin_a + z * cos_a
    return x, new_y, new_z


def create_uv_sphere_points(
    radius: float,
    horizontal_segments: int = 16,
    vertical_segments: int = 10,
    vertex_down: bool = True
) -> tuple:
    """
    Generate UV sphere vertices with optional vertex-down rotation.
    
    Args:
        radius: Sphere radius
        horizontal_segments: Longitude divisions (around equator)
        vertical_segments: Latitude divisions (pole to pole)
        vertex_down: If True, rotate 90° so equator vertex points down
    
    Returns:
        Tuple of (points, normals) as lists of Gf.Vec3f
    """
    points = []
    normals = []
    
    # Rotation angle: 90 degrees around X-axis puts equator at bottom
    rotation_angle = (math.pi / 2.0) if vertex_down else 0.0
    
    for v in range(vertical_segments + 1):
        # Latitude angle from top pole (0) to bottom pole (pi)
        phi = (v / vertical_segments) * math.pi
        
        sin_phi = math.sin(phi)
        cos_phi = math.cos(phi)
        
        for h in range(horizontal_segments):
            # Longitude angle around the sphere
            theta = (h / horizontal_segments) * 2.0 * math.pi
            
            sin_theta = math.sin(theta)
            cos_theta = math.cos(theta)
            
            # Unit sphere coordinates (Y-up, poles on Y-axis)
            nx = sin_phi * cos_theta
            ny = cos_phi
            nz = sin_phi * sin_theta
            
            # Apply rotation if vertex-down mode
            if vertex_down:
                nx, ny, nz = _rotate_around_x_axis(nx, ny, nz, rotation_angle)
            
            # Scale by radius for position
            x = radius * nx
            y = radius * ny
            z = radius * nz
            
            points.append(Gf.Vec3f(x, y, z))
            normals.append(Gf.Vec3f(nx, ny, nz))
    
    return points, normals


def create_sphere_face_indices(
    horizontal_segments: int,
    vertical_segments: int
) -> tuple:
    """
    Generate face indices for UV sphere mesh.
    
    Args:
        horizontal_segments: Longitude divisions
        vertical_segments: Latitude divisions
    
    Returns:
        Tuple of (face_vertex_counts, face_vertex_indices)
    """
    face_vertex_counts = []
    face_vertex_indices = []
    
    for v in range(vertical_segments):
        for h in range(horizontal_segments):
            # Current ring vertex indices
            v0 = v * horizontal_segments + h
            v1 = v * horizontal_segments + ((h + 1) % horizontal_segments)
            # Next ring vertex indices
            v2 = (v + 1) * horizontal_segments + ((h + 1) % horizontal_segments)
            v3 = (v + 1) * horizontal_segments + h
            
            # Two triangles per quad
            face_vertex_counts.extend([3, 3])
            face_vertex_indices.extend([v0, v2, v1, v0, v3, v2])
    
    return face_vertex_counts, face_vertex_indices


def create_sphere_mesh(
    stage,
    path: str,
    radius: float,
    horizontal_segments: int = 16,
    vertical_segments: int = 10,
    vertex_down: bool = True
) -> UsdGeom.Mesh:
    """
    Create complete USD mesh sphere with optional vertex-down orientation.
    
    Args:
        stage: USD stage
        path: Prim path for mesh
        radius: Sphere radius
        horizontal_segments: Longitude resolution
        vertical_segments: Latitude resolution
        vertex_down: If True, rotate so equator vertex points down
    
    Returns:
        UsdGeom.Mesh prim
    """
    points, normals = create_uv_sphere_points(
        radius=radius,
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments,
        vertex_down=vertex_down
    )
    
    face_counts, face_indices = create_sphere_face_indices(
        horizontal_segments=horizontal_segments,
        vertical_segments=vertical_segments
    )
    
    mesh_prim = UsdGeom.Mesh.Define(stage, path)
    mesh_prim.CreatePointsAttr(points)
    mesh_prim.CreateNormalsAttr(normals)
    mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
    mesh_prim.CreateFaceVertexCountsAttr(face_counts)
    mesh_prim.CreateFaceVertexIndicesAttr(face_indices)
    mesh_prim.CreateSubdivisionSchemeAttr("none")
    mesh_prim.CreateDoubleSidedAttr(True)
    
    extent = UsdGeom.PointBased(mesh_prim).ComputeExtent(points)
    mesh_prim.CreateExtentAttr(extent)
    
    return mesh_prim
