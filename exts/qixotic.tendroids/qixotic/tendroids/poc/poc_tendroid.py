"""
POC Tendroid - Single cylinder mesh with bubble-guided deformation

Creates a USD mesh cylinder and updates vertices based on bubble position.
Height is along Y-axis (Omniverse convention).
"""

import math

import carb
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade


class POCTendroid:
  """
  Single cylinder with bubble-guided deformation.

  Creates a cylindrical mesh and deforms it in real-time based on
  the position of an internal bubble. Height is along Y-axis.
  """

  def __init__(
    self,
    stage: Usd.Stage,
    path: str = "/World/POC_Tendroid",
    radius: float = 10.0,
    length: float = 100.0,
    radial_segments: int = 24,
    height_segments: int = 48
  ):
    """
    Initialize POC tendroid.

    Args:
        stage: USD stage
        path: Prim path for the mesh
        radius: Base cylinder radius
        length: Cylinder height (along Y-axis)
        radial_segments: Vertices around circumference
        height_segments: Vertices along height
    """
    self.stage = stage
    self.path = path
    self.radius = radius
    self.length = length
    self.radial_segments = radial_segments
    self.height_segments = height_segments

    # Store base geometry for deformation
    self.base_points = []
    self.base_normals = []
    self.vertex_heights = []  # Y position of each vertex

    # USD references
    self.mesh_prim = None
    self.points_attr = None

    # Create the mesh
    self._create_mesh()
    self._apply_material()

    carb.log_info(
      f"[POCTendroid] Created: r={radius}, L={length}, "
      f"verts={len(self.base_points)}, segments={radial_segments}x{height_segments}"
    )

  def _create_mesh(self):
    """Create the cylinder mesh geometry with Y as height axis."""
    points = []
    normals = []
    heights = []

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

    # Generate face indices (quads as triangles)
    face_vertex_counts = []
    face_vertex_indices = []

    for h in range(self.height_segments):
      for r in range(self.radial_segments):
        v0 = h * self.radial_segments + r
        v1 = h * self.radial_segments + ((r + 1) % self.radial_segments)
        v2 = (h + 1) * self.radial_segments + ((r + 1) % self.radial_segments)
        v3 = (h + 1) * self.radial_segments + r

        # Two triangles per quad - counter-clockwise winding for outward normals
        face_vertex_counts.extend([3, 3])
        face_vertex_indices.extend([v0, v2, v1, v0, v3, v2])

    # Create USD mesh
    self.mesh_prim = UsdGeom.Mesh.Define(self.stage, self.path)
    self.mesh_prim.CreatePointsAttr(points)
    self.mesh_prim.CreateNormalsAttr(normals)
    self.mesh_prim.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
    self.mesh_prim.CreateFaceVertexCountsAttr(face_vertex_counts)
    self.mesh_prim.CreateFaceVertexIndicesAttr(face_vertex_indices)
    self.mesh_prim.CreateSubdivisionSchemeAttr("none")
    self.mesh_prim.CreateDoubleSidedAttr(True)  # Render both sides

    # Compute and set extent
    extent = UsdGeom.PointBased(self.mesh_prim).ComputeExtent(points)
    self.mesh_prim.CreateExtentAttr(extent)

    self.points_attr = self.mesh_prim.GetPointsAttr()

    carb.log_info(f"[POCTendroid] Mesh created: {len(points)} verts, Y-axis height")

  def _apply_material(self):
    """Apply or create a material for the tendroid."""
    # Try to use existing Carpaint material
    carpaint_path = "/World/Looks/Carpaint_02"
    material_prim = self.stage.GetPrimAtPath(carpaint_path)

    if material_prim.IsValid():
      material = UsdShade.Material(material_prim)
      carb.log_info(f"[POCTendroid] Using existing material: {carpaint_path}")
    else:
      # Create a simple material
      material = self._create_fallback_material()

    # Bind material to mesh
    UsdShade.MaterialBindingAPI(self.mesh_prim).Bind(material)

  def _create_fallback_material(self) -> UsdShade.Material:
    """Create a fallback material if Carpaint doesn't exist."""
    # Ensure /World/Looks exists
    looks_path = "/World/Looks"
    if not self.stage.GetPrimAtPath(looks_path).IsValid():
      UsdGeom.Scope.Define(self.stage, looks_path)

    # Create material
    mat_path = "/World/Looks/POC_Tendroid_Mat"
    material = UsdShade.Material.Define(self.stage, mat_path)

    # Create shader
    shader_path = f"{mat_path}/Shader"
    shader = UsdShade.Shader.Define(self.stage, shader_path)
    shader.CreateIdAttr("UsdPreviewSurface")

    # Coral/pink color like existing tendroids
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
      Gf.Vec3f(0.9, 0.4, 0.5)
    )
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.4)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.1)

    # Connect shader to material
    material.CreateSurfaceOutput().ConnectToSource(
      shader.ConnectableAPI(), "surface"
    )

    carb.log_info(f"[POCTendroid] Created fallback material: {mat_path}")
    return material

  def apply_deformation(self, deformer, bubble_y: float, bubble_radius: float):
    """
    Apply bubble-guided deformation to the mesh.

    Args:
        deformer: POCDeformer instance
        bubble_y: Current Y position of bubble center
        bubble_radius: Radius of the bubble
    """
    new_points = []
    max_disp = 0.0
    max_disp_y = 0.0

    for i, (base_pt, normal, y) in enumerate(
      zip(self.base_points, self.base_normals, self.vertex_heights)
    ):
      # Get displacement fraction for this vertex based on bubble position
      displacement = deformer.calculate_displacement(y, bubble_y, bubble_radius)

      # Track max displacement for debugging
      if displacement > max_disp:
        max_disp = displacement
        max_disp_y = y

      # Scale the vertex radially outward from center axis
      scale = 1.0 + displacement

      new_x = base_pt[0] * scale
      new_y = base_pt[1]  # Y stays constant (height)
      new_z = base_pt[2] * scale

      new_points.append(Gf.Vec3f(new_x, new_y, new_z))

    # Debug: log occasionally
    if int(bubble_y) % 25 == 0:
      carb.log_info(
        f"[Deform] bubble_y={bubble_y:.1f}, max_disp_y={max_disp_y:.1f}"
      )

    # Update mesh
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
      carb.log_info(f"[POCTendroid] Destroyed {self.path}")
