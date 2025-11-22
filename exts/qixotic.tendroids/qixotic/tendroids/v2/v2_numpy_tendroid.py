"""
V2 NumPy Tendroid - Vectorized CPU deformation
"""

import math
import carb
import numpy as np
from pxr import Gf, Usd, UsdGeom, Vt

from .v2_material_helper import apply_material


class V2NumpyTendroid:
    """
    Cylinder mesh with NumPy-vectorized deformation.
    """

    def __init__(
        self, stage: Usd.Stage, path: str = "/World/V2_Tendroid",
        radius: float = 10.0, length: float = 100.0,
        radial_segments: int = 24, height_segments: int = 48,
        max_amplitude: float = 0.8, bulge_width: float = 0.9
    ):
        self.stage = stage
        self.path = path
        self.radius = radius
        self.length = length
        self.max_amplitude = max_amplitude
        self.bulge_width = bulge_width

        self.mesh_prim = None
        self.points_attr = None
        
        self.base_points_np = None
        self.vertex_heights = None
        self.out_points = None
        
        self._create_mesh(radial_segments, height_segments)
        apply_material(stage, self.mesh_prim)

    def _create_mesh(self, radial_segments: int, height_segments: int):
        """Create cylinder mesh."""
        num_verts = (height_segments + 1) * radial_segments
        
        points = np.zeros((num_verts, 3), dtype=np.float64)
        normals = np.zeros((num_verts, 3), dtype=np.float64)
        
        idx = 0
        for h in range(height_segments + 1):
            y = (h / height_segments) * self.length
            for r in range(radial_segments):
                angle = (r / radial_segments) * 2.0 * math.pi
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                points[idx] = [self.radius * cos_a, y, self.radius * sin_a]
                normals[idx] = [cos_a, 0.0, sin_a]
                idx += 1
        
        self.base_points_np = points.copy()
        self.vertex_heights = points[:, 1].copy()
        self.out_points = points.copy()
        
        points_list = [Gf.Vec3f(float(p[0]), float(p[1]), float(p[2])) for p in points]
        normals_list = [Gf.Vec3f(float(n[0]), float(n[1]), float(n[2])) for n in normals]

        face_vertex_counts, face_vertex_indices = [], []
        for h in range(height_segments):
            for r in range(radial_segments):
                v0 = h * radial_segments + r
                v1 = h * radial_segments + ((r + 1) % radial_segments)
                v2 = (h + 1) * radial_segments + ((r + 1) % radial_segments)
                v3 = (h + 1) * radial_segments + r
                face_vertex_counts.extend([3, 3])
                face_vertex_indices.extend([v0, v2, v1, v0, v3, v2])

        self.mesh_prim = UsdGeom.Mesh.Define(self.stage, self.path)
        self.mesh_prim.CreatePointsAttr(points_list)
        self.mesh_prim.CreateNormalsAttr(normals_list)
        self.mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        self.mesh_prim.CreateFaceVertexCountsAttr(face_vertex_counts)
        self.mesh_prim.CreateFaceVertexIndicesAttr(face_vertex_indices)
        self.mesh_prim.CreateSubdivisionSchemeAttr("none")
        self.mesh_prim.CreateDoubleSidedAttr(True)

        extent = UsdGeom.PointBased(self.mesh_prim).ComputeExtent(points_list)
        self.mesh_prim.CreateExtentAttr(extent)
        self.points_attr = self.mesh_prim.GetPointsAttr()
        
        carb.log_info(f"[V2NumpyTendroid] Created: {num_verts} verts")

    def apply_deformation(self, bubble_y: float, bubble_radius: float):
        """Vectorized deformation."""
        max_radius = self.radius * (1.0 + self.max_amplitude)
        radius_range = max_radius - self.radius
        
        growth = 0.0
        if radius_range > 0:
            growth = np.clip((bubble_radius - self.radius) / radius_range, 0.0, 1.0)
        
        current_amp = self.max_amplitude * growth
        
        sigma = bubble_radius * self.bulge_width
        dist = self.vertex_heights - bubble_y
        gaussian = np.exp(-(dist * dist) / (2.0 * sigma * sigma))
        
        scale = 1.0 + current_amp * gaussian
        
        self.out_points[:, 0] = self.base_points_np[:, 0] * scale
        self.out_points[:, 1] = self.base_points_np[:, 1]
        self.out_points[:, 2] = self.base_points_np[:, 2] * scale
        
        points_list = [Gf.Vec3f(*p) for p in self.out_points.tolist()]
        
        if self.points_attr:
            self.points_attr.Set(points_list)

    def destroy(self):
        if self.stage and self.path:
            self.stage.RemovePrim(self.path)
