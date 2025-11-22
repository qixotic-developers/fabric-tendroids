"""
V2 Tendroid - Single cylinder mesh with bubble-guided deformation (CPU version)
"""

import math
import carb
from pxr import Gf, Usd, UsdGeom

from .v2_material_helper import apply_material


class V2Tendroid:
    """
    Cylinder mesh that deforms based on bubble position.
    Height is along Y-axis (Omniverse convention).
    """

    def __init__(
        self, stage: Usd.Stage, path: str = "/World/V2_Tendroid",
        radius: float = 10.0, length: float = 100.0,
        radial_segments: int = 24, height_segments: int = 48
    ):
        self.stage = stage
        self.path = path
        self.radius = radius
        self.length = length
        self.radial_segments = radial_segments
        self.height_segments = height_segments

        self.base_points = []
        self.base_normals = []
        self.vertex_heights = []
        self.mesh_prim = None
        self.points_attr = None

        self._create_mesh()
        apply_material(stage, self.mesh_prim)

    def _create_mesh(self):
        """Create the cylinder mesh geometry."""
        points, normals, heights = [], [], []

        for h in range(self.height_segments + 1):
            y = (h / self.height_segments) * self.length
            for r in range(self.radial_segments):
                angle = (r / self.radial_segments) * 2.0 * math.pi
                x = self.radius * math.cos(angle)
                z = self.radius * math.sin(angle)
                points.append(Gf.Vec3f(x, y, z))
                normals.append(Gf.Vec3f(math.cos(angle), 0.0, math.sin(angle)))
                heights.append(y)

        self.base_points = points
        self.base_normals = normals
        self.vertex_heights = heights

        face_vertex_counts, face_vertex_indices = [], []
        for h in range(self.height_segments):
            for r in range(self.radial_segments):
                v0 = h * self.radial_segments + r
                v1 = h * self.radial_segments + ((r + 1) % self.radial_segments)
                v2 = (h + 1) * self.radial_segments + ((r + 1) % self.radial_segments)
                v3 = (h + 1) * self.radial_segments + r
                face_vertex_counts.extend([3, 3])
                face_vertex_indices.extend([v0, v2, v1, v0, v3, v2])

        self.mesh_prim = UsdGeom.Mesh.Define(self.stage, self.path)
        self.mesh_prim.CreatePointsAttr(points)
        self.mesh_prim.CreateNormalsAttr(normals)
        self.mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        self.mesh_prim.CreateFaceVertexCountsAttr(face_vertex_counts)
        self.mesh_prim.CreateFaceVertexIndicesAttr(face_vertex_indices)
        self.mesh_prim.CreateSubdivisionSchemeAttr("none")
        self.mesh_prim.CreateDoubleSidedAttr(True)

        extent = UsdGeom.PointBased(self.mesh_prim).ComputeExtent(points)
        self.mesh_prim.CreateExtentAttr(extent)
        self.points_attr = self.mesh_prim.GetPointsAttr()

    def apply_deformation(self, deformer, bubble_y: float, bubble_radius: float):
        """Apply bubble-guided deformation to the mesh."""
        new_points = []

        for base_pt, y in zip(self.base_points, self.vertex_heights):
            displacement = deformer.calculate_displacement(y, bubble_y, bubble_radius)
            scale = 1.0 + displacement
            new_points.append(Gf.Vec3f(base_pt[0] * scale, base_pt[1], base_pt[2] * scale))

        if self.points_attr:
            self.points_attr.Set(new_points)

    def reset_to_base(self):
        """Reset mesh to undeformed base shape."""
        if self.points_attr:
            self.points_attr.Set(self.base_points)

    def destroy(self):
        """Remove the mesh from the stage."""
        if self.stage and self.path:
            self.stage.RemovePrim(self.path)
