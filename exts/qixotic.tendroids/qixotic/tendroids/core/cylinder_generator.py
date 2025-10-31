"""
Procedural cylinder mesh generator for Tendroids

Creates cylinder geometry optimized for transform-based segment animation.
Adapted from previous implementation with simplifications.
"""

from pxr import UsdGeom, Gf, Vt, Sdf
import math
import carb


class CylinderGenerator:
    """
    Generates procedural cylinder meshes as Tendroid base geometry.
    
    Creates segment-based cylinder topology where each ring of vertices
    represents a segment that can be scaled independently for animation.
    """

    @staticmethod
    def create_cylinder(
        stage,
        path: str,
        radius: float = 10.0,
        length: float = 100.0,
        num_segments: int = 16,
        radial_resolution: int = 16,
        flare_radius_multiplier: float = 1.5,
        flare_height_percent: float = 10.0
    ):
        """
        Create a procedural cylinder mesh with optional flared base.

        Args:
            stage: USD stage to create mesh in
            path: USD path for the mesh prim
            radius: Cylinder radius (default 10)
            length: Cylinder length along Y-axis (up) (default 100)
            num_segments: Number of segments along length (default 16)
            radial_resolution: Number of vertices around circumference (default 16)
            flare_radius_multiplier: Radius multiplier at base (default 1.5 = 50% larger)
            flare_height_percent: Percentage of length for flare (default 10)

        Returns:
            Tuple of (mesh_prim, num_segments, radial_resolution)
        """
        carb.log_info(
            f"[CylinderGenerator] Creating cylinder at {path}: "
            f"radius={radius}, length={length}, segments={num_segments}, "
            f"radial_res={radial_resolution}"
        )

        # Calculate flare parameters
        flare_height = length * (flare_height_percent / 100.0)
        max_flare_radius = radius * flare_radius_multiplier

        # Define mesh prim
        mesh = UsdGeom.Mesh.Define(stage, path)

        # Generate vertex positions
        vertices = []
        normals = []
        segment_height = length / num_segments

        # Create vertices ring by ring from bottom (y=0) to top (y=length)
        for seg_idx in range(num_segments + 1):
            y = seg_idx * segment_height

            # Calculate radius at this height (flare at base)
            if y <= flare_height and flare_height > 0:
                # Ease-out quartic for mechanical flange profile
                t = y / flare_height
                blend = 1.0 - pow(1.0 - t, 4)
                current_radius = max_flare_radius + (radius - max_flare_radius) * blend
            else:
                current_radius = radius

            # Create ring of vertices
            for i in range(radial_resolution):
                angle = 2 * math.pi * i / radial_resolution
                x = current_radius * math.cos(angle)
                z = current_radius * math.sin(angle)

                vertices.append(Gf.Vec3f(x, y, z))

                # Calculate normal
                if y <= flare_height and flare_height > 0:
                    # For flared section, normal points outward and slightly upward
                    t = y / flare_height
                    # Derivative of ease-out quartic blend
                    dt_radius = (radius - max_flare_radius) * 4 * pow(1.0 - t, 3) / flare_height

                    nx = math.cos(angle)
                    nz = math.sin(angle)
                    ny = -dt_radius / current_radius if current_radius > 0 else 0

                    # Normalize
                    normal_length = math.sqrt(nx * nx + ny * ny + nz * nz)
                    if normal_length > 0:
                        normals.append(Gf.Vec3f(nx / normal_length, ny / normal_length, nz / normal_length))
                    else:
                        normals.append(Gf.Vec3f(1.0, 0.0, 0.0))
                else:
                    # Normal points radially outward
                    normal_length = math.sqrt(x * x + z * z)
                    if normal_length > 0:
                        normals.append(Gf.Vec3f(x / normal_length, 0.0, z / normal_length))
                    else:
                        normals.append(Gf.Vec3f(1.0, 0.0, 0.0))

        # Set mesh points
        mesh.CreatePointsAttr(Vt.Vec3fArray(vertices))

        # Set vertex normals for smooth shading
        mesh.CreateNormalsAttr(Vt.Vec3fArray(normals))
        mesh.SetNormalsInterpolation(UsdGeom.Tokens.vertex)

        # Generate quad face topology
        face_vertex_counts = []
        face_vertex_indices = []

        for seg_idx in range(num_segments):
            for i in range(radial_resolution):
                # Wrap around for last radial segment
                next_i = (i + 1) % radial_resolution

                # Define quad vertices (counter-clockwise)
                v0 = seg_idx * radial_resolution + i
                v1 = seg_idx * radial_resolution + next_i
                v2 = (seg_idx + 1) * radial_resolution + next_i
                v3 = (seg_idx + 1) * radial_resolution + i

                face_vertex_counts.append(4)
                face_vertex_indices.extend([v0, v1, v2, v3])

        mesh.CreateFaceVertexCountsAttr(Vt.IntArray(face_vertex_counts))
        mesh.CreateFaceVertexIndicesAttr(Vt.IntArray(face_vertex_indices))

        # Compute and set bounding box
        extent = UsdGeom.PointBased(mesh).ComputeExtent(mesh.GetPointsAttr().Get())
        mesh.CreateExtentAttr(extent)

        # Set subdivision scheme
        mesh.CreateSubdivisionSchemeAttr("none")

        # Add default display color (light blue-green for sea creature)
        primvar_api = UsdGeom.PrimvarsAPI(mesh)
        color_primvar = primvar_api.CreatePrimvar(
            "displayColor",
            Sdf.ValueTypeNames.Color3f,
            "constant"
        )
        color_primvar.Set([Gf.Vec3f(0.3, 0.6, 0.7)])

        carb.log_info(
            f"[CylinderGenerator] Created mesh with {len(vertices)} vertices, "
            f"{len(face_vertex_counts)} faces"
        )

        return mesh.GetPrim(), num_segments, radial_resolution

    @staticmethod
    def get_segment_paths(base_path: str, num_segments: int) -> list:
        """
        Generate USD paths for segment Xforms that will control scaling.
        
        Args:
            base_path: Base USD path for the Tendroid
            num_segments: Number of segments
            
        Returns:
            List of USD paths for segment Xforms
        """
        return [f"{base_path}/segment_{i:02d}" for i in range(num_segments)]
