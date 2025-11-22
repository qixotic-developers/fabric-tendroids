"""
Cylinder mesh generator with flared base support for V2 tendroids

Creates cylinder geometry with configurable flare at the base
for realistic sea floor attachment.
"""

import math
from pxr import Gf, UsdGeom


class CylinderGenerator:
    """
    Generates cylinder mesh geometry with optional flared base.
    
    The flare creates a wider base that can conform to terrain,
    giving tendroids a more organic, rooted appearance.
    """
    
    @staticmethod
    def create_cylinder_points(
        radius: float,
        length: float,
        radial_segments: int = 24,
        height_segments: int = 48,
        flare_height_percent: float = 15.0,
        flare_radius_multiplier: float = 2.0
    ) -> tuple:
        """
        Generate cylinder vertices with flared base.
        
        Args:
            radius: Base cylinder radius (at non-flared sections)
            length: Total cylinder height
            radial_segments: Vertices around circumference
            height_segments: Vertical divisions
            flare_height_percent: Height of flare as % of total length
            flare_radius_multiplier: Max radius at base (multiplier of radius)
        
        Returns:
            Tuple of (points, normals, heights, deform_start_height)
            - points: List of Gf.Vec3f vertices
            - normals: List of Gf.Vec3f normals
            - heights: List of Y values per vertex
            - deform_start_height: Y where flare ends (deformation can begin)
        """
        points = []
        normals = []
        heights = []
        
        flare_height = length * (flare_height_percent / 100.0)
        max_flare_radius = radius * flare_radius_multiplier
        
        for h in range(height_segments + 1):
            y = (h / height_segments) * length
            
            # Calculate radius at this height (flared at base)
            if y < flare_height:
                # Smooth flare using cosine interpolation
                t = y / flare_height
                flare_factor = 0.5 * (1.0 - math.cos(t * math.pi))
                current_radius = max_flare_radius + (radius - max_flare_radius) * flare_factor
            else:
                current_radius = radius
            
            for r in range(radial_segments):
                angle = (r / radial_segments) * 2.0 * math.pi
                cos_a = math.cos(angle)
                sin_a = math.sin(angle)
                
                x = current_radius * cos_a
                z = current_radius * sin_a
                
                points.append(Gf.Vec3f(x, y, z))
                normals.append(Gf.Vec3f(cos_a, 0.0, sin_a))
                heights.append(y)
        
        deform_start_height = flare_height
        
        return points, normals, heights, deform_start_height
    
    @staticmethod
    def create_face_indices(
        radial_segments: int,
        height_segments: int
    ) -> tuple:
        """
        Generate face vertex counts and indices for cylinder mesh.
        
        Args:
            radial_segments: Vertices around circumference
            height_segments: Vertical divisions
        
        Returns:
            Tuple of (face_vertex_counts, face_vertex_indices)
        """
        face_vertex_counts = []
        face_vertex_indices = []
        
        for h in range(height_segments):
            for r in range(radial_segments):
                v0 = h * radial_segments + r
                v1 = h * radial_segments + ((r + 1) % radial_segments)
                v2 = (h + 1) * radial_segments + ((r + 1) % radial_segments)
                v3 = (h + 1) * radial_segments + r
                
                # Two triangles per quad
                face_vertex_counts.extend([3, 3])
                face_vertex_indices.extend([v0, v2, v1, v0, v3, v2])
        
        return face_vertex_counts, face_vertex_indices
    
    @staticmethod
    def create_mesh(
        stage,
        path: str,
        radius: float,
        length: float,
        radial_segments: int = 24,
        height_segments: int = 48,
        flare_height_percent: float = 15.0,
        flare_radius_multiplier: float = 2.0
    ) -> tuple:
        """
        Create complete USD mesh with flared cylinder geometry.
        
        Args:
            stage: USD stage
            path: Prim path for mesh
            radius: Base cylinder radius
            length: Total height
            radial_segments: Circumference resolution
            height_segments: Vertical resolution
            flare_height_percent: Flare height as % of length
            flare_radius_multiplier: Base radius multiplier
        
        Returns:
            Tuple of (mesh_prim, points, deform_start_height)
        """
        # Generate geometry
        points, normals, heights, deform_start = CylinderGenerator.create_cylinder_points(
            radius=radius,
            length=length,
            radial_segments=radial_segments,
            height_segments=height_segments,
            flare_height_percent=flare_height_percent,
            flare_radius_multiplier=flare_radius_multiplier
        )
        
        face_counts, face_indices = CylinderGenerator.create_face_indices(
            radial_segments=radial_segments,
            height_segments=height_segments
        )
        
        # Create USD mesh
        mesh_prim = UsdGeom.Mesh.Define(stage, path)
        mesh_prim.CreatePointsAttr(points)
        mesh_prim.CreateNormalsAttr(normals)
        mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        mesh_prim.CreateFaceVertexCountsAttr(face_counts)
        mesh_prim.CreateFaceVertexIndicesAttr(face_indices)
        mesh_prim.CreateSubdivisionSchemeAttr("none")
        mesh_prim.CreateDoubleSidedAttr(True)
        
        # Compute and set extent
        extent = UsdGeom.PointBased(mesh_prim).ComputeExtent(points)
        mesh_prim.CreateExtentAttr(extent)
        
        return mesh_prim, points, deform_start
