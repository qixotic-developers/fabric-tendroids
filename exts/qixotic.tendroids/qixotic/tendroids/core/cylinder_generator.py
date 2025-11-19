"""
Procedural cylinder mesh generator with flared base for Tendroids

Creates a single unified mesh optimized for Warp-based vertex deformation.
"""

from pxr import UsdGeom, Gf, Vt, Sdf
import math
from ..utils.math_helpers import calculate_flare_radius


class CylinderGenerator:
    """
    Generates procedural cylinder meshes for Tendroid base geometry.
    
    Creates a single unified mesh with:
    - Flared base (static during animation)
    - Smooth transition zone
    - Cylindrical body (deformable region)
    """

    @staticmethod
    def create_tendroid_cylinder(
        stage,
        path: str,
        radius: float = 10.0,
        length: float = 100.0,
        num_segments: int = 32,
        radial_resolution: int = 16,
        flare_height_percent: float = 15.0,
        flare_radius_multiplier: float = 2.0
    ):
        """
        Create a Tendroid cylinder mesh with flared base.

        Args:
            stage: USD stage to create mesh in
            path: USD path for the mesh prim
            radius: Cylinder radius
            length: Total length along Y-axis (up)
            num_segments: Number of vertical segments (higher = smoother deformation)
            radial_resolution: Number of vertices around circumference
            flare_height_percent: Percentage of length for flared base
            flare_radius_multiplier: Base radius multiplier (2.0 = 2x wider at base)

        Returns:
            Tuple of (mesh_prim, vertices, num_segments, radial_resolution, deform_start_height)
        """
        # Calculate dimensions
        flare_height = length * (flare_height_percent / 100.0)
        max_radius = radius * flare_radius_multiplier
        segment_height = length / num_segments
        
        # Deformation starts above flare + transition zone
        transition_zone = flare_height * 0.2
        deform_start_height = flare_height + transition_zone

        # Define mesh
        mesh = UsdGeom.Mesh.Define(stage, path)

        # Generate vertices
        vertices = []
        normals = []

        for seg_idx in range(num_segments + 1):
            y = seg_idx * segment_height
            current_radius = calculate_flare_radius(y, radius, max_radius, flare_height)

            # Create ring of vertices
            for i in range(radial_resolution):
                angle = 2.0 * math.pi * i / radial_resolution
                x = current_radius * math.cos(angle)
                z = current_radius * math.sin(angle)
                vertices.append(Gf.Vec3f(x, y, z))

                # Calculate normal
                if y <= flare_height:
                    # Flared section - outward and slightly upward normal
                    nx = math.cos(angle)
                    nz = math.sin(angle)
                    ny = 0.1  # Slight upward component
                    length_n = math.sqrt(nx * nx + ny * ny + nz * nz)
                    normals.append(Gf.Vec3f(nx / length_n, ny / length_n, nz / length_n))
                else:
                    # Cylindrical section - purely radial normal
                    normals.append(Gf.Vec3f(math.cos(angle), 0.0, math.sin(angle)))

        # Set geometry
        mesh.CreatePointsAttr(Vt.Vec3fArray(vertices))
        mesh.CreateNormalsAttr(Vt.Vec3fArray(normals))
        mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)

        # Generate quad faces
        face_vertex_counts = []
        face_vertex_indices = []

        for seg_idx in range(num_segments):
            for i in range(radial_resolution):
                next_i = (i + 1) % radial_resolution
                
                v0 = seg_idx * radial_resolution + i
                v1 = seg_idx * radial_resolution + next_i
                v2 = (seg_idx + 1) * radial_resolution + next_i
                v3 = (seg_idx + 1) * radial_resolution + i

                face_vertex_counts.append(4)
                face_vertex_indices.extend([v0, v1, v2, v3])

        mesh.CreateFaceVertexCountsAttr(Vt.IntArray(face_vertex_counts))
        mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(face_vertex_indices))

        # Compute extent
        extent = UsdGeom.PointBased(mesh).ComputeExtent(vertices)
        mesh.CreateExtentAttr(extent)

        # Set subdivision
        mesh.CreateSubdivisionSchemeAttr("none")

        # Set default color (sea creature blue-green)
        primvar_api = UsdGeom.PrimvarsAPI(mesh)
        color_primvar = primvar_api.CreatePrimvar(
            "displayColor",
            Sdf.ValueTypeNames.Color3f,
            "constant"
        )
        color_primvar.Set([Gf.Vec3f(0.2, 0.5, 0.6)])

        return mesh.GetPrim(), vertices, num_segments, radial_resolution, deform_start_height
