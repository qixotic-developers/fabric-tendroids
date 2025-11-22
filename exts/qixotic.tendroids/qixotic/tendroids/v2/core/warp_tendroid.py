"""
V2 Warp Tendroid - GPU-powered cylinder deformation
"""

import math

import carb
from pxr import Gf, Usd, UsdGeom, Vt

from ..utils import apply_material
from .warp_deformer import V2WarpDeformer


class V2WarpTendroid:
  """
  Cylinder mesh with Warp GPU-accelerated deformation.
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
    self.radial_segments = radial_segments
    self.height_segments = height_segments

    self.base_points = []
    self.mesh_prim = None
    self.points_attr = None
    self.warp_deformer = None

    self._create_mesh()
    apply_material(stage, self.mesh_prim)

    self.warp_deformer = V2WarpDeformer(
      base_points_list=self.base_points,
      cylinder_radius=radius,
      max_amplitude=max_amplitude,
      bulge_width=bulge_width
    )

    carb.log_info(f"[V2WarpTendroid] Created with {len(self.base_points)} verts on GPU")

  def _create_mesh(self):
    """Create the cylinder mesh geometry."""
    points = []
    normals = []

    for h in range(self.height_segments + 1):
      y = (h / self.height_segments) * self.length
      for r in range(self.radial_segments):
        angle = (r / self.radial_segments) * 2.0 * math.pi
        x = self.radius * math.cos(angle)
        z = self.radius * math.sin(angle)
        points.append(Gf.Vec3f(x, y, z))
        normals.append(Gf.Vec3f(math.cos(angle), 0.0, math.sin(angle)))

    self.base_points = points

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

  def apply_deformation(self, bubble_y: float, bubble_radius: float):
    """Apply GPU-accelerated deformation."""
    if not self.warp_deformer:
      return

    new_points_np = self.warp_deformer.deform(bubble_y, bubble_radius)

    if self.points_attr:
      self.points_attr.Set(new_points_np)

  def destroy(self):
    """Clean up GPU and USD resources."""
    if self.warp_deformer:
      self.warp_deformer.destroy()
      self.warp_deformer = None
    if self.stage and self.path:
      self.stage.RemovePrim(self.path)
