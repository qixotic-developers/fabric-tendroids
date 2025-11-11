"""
Geometry Builder

Creates simple test geometry for Warp deformation testing.
Focuses on clean, minimal meshes to isolate performance issues.
"""

from pxr import Usd, UsdGeom, UsdShade, Gf, Sdf
from typing import Tuple, List
import numpy as np
import carb


class GeometryBuilder:
    """Builds test geometry primitives"""
    
    def __init__(self, stage: Usd.Stage):
        self.stage = stage
        
    def create_test_cylinder(
        self,
        path: str,
        height: float = 5.0,
        radius: float = 0.5,
        segments: int = 16,
        radial_segments: int = 12
    ) -> Tuple[UsdGeom.Mesh, np.ndarray]:
        """
        Create a simple cylindrical mesh for testing.
        
        Returns:
            Tuple of (mesh_prim, vertex_positions_array)
        """
        mesh = UsdGeom.Mesh.Define(self.stage, path)
        
        # Generate cylinder vertices
        positions, face_indices, face_counts = self._generate_cylinder_geometry(
            height, radius, segments, radial_segments
        )
        
        # Set mesh attributes
        mesh.CreatePointsAttr(positions)
        mesh.CreateFaceVertexIndicesAttr(face_indices)
        mesh.CreateFaceVertexCountsAttr(face_counts)
        
        # Set subdivision scheme
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        
        return mesh, np.array(positions)
        
    def create_double_wall_cylinder(
        self,
        path: str,
        height: float = 5.0,
        outer_radius: float = 0.5,
        inner_radius: float = 0.45,
        segments: int = 16,
        radial_segments: int = 12
    ) -> Tuple[UsdGeom.Mesh, np.ndarray, int]:
        """
        Create double-walled cylinder with proper thickness for refraction.
        
        Creates a mesh with both outer and inner surfaces, providing proper
        volume geometry for path-traced refraction calculations.
        
        Returns:
            Tuple of (mesh_prim, all_vertex_positions_array, outer_vertex_count)
        """
        mesh = UsdGeom.Mesh.Define(self.stage, path)
        
        positions = []
        face_indices = []
        face_counts = []
        
        # Generate outer cylinder vertices
        for seg in range(segments + 1):
            y = (seg / segments) * height
            
            for rad in range(radial_segments):
                angle = (rad / radial_segments) * 2.0 * np.pi
                x = outer_radius * np.cos(angle)
                z = outer_radius * np.sin(angle)
                positions.append(Gf.Vec3f(x, y, z))
        
        outer_vertex_count = len(positions)
        
        # Generate inner cylinder vertices (reversed winding)
        for seg in range(segments + 1):
            y = (seg / segments) * height
            
            for rad in range(radial_segments):
                angle = (rad / radial_segments) * 2.0 * np.pi
                x = inner_radius * np.cos(angle)
                z = inner_radius * np.sin(angle)
                positions.append(Gf.Vec3f(x, y, z))
        
        # Generate outer cylinder faces
        for seg in range(segments):
            for rad in range(radial_segments):
                i0 = seg * radial_segments + rad
                i1 = seg * radial_segments + ((rad + 1) % radial_segments)
                i2 = (seg + 1) * radial_segments + ((rad + 1) % radial_segments)
                i3 = (seg + 1) * radial_segments + rad
                
                face_indices.extend([i0, i1, i2, i3])
                face_counts.append(4)
        
        # Generate inner cylinder faces (reversed winding for inward normals)
        for seg in range(segments):
            for rad in range(radial_segments):
                i0 = outer_vertex_count + seg * radial_segments + rad
                i1 = outer_vertex_count + (seg + 1) * radial_segments + rad
                i2 = outer_vertex_count + (seg + 1) * radial_segments + ((rad + 1) % radial_segments)
                i3 = outer_vertex_count + seg * radial_segments + ((rad + 1) % radial_segments)
                
                face_indices.extend([i0, i1, i2, i3])
                face_counts.append(4)
        
        # Set mesh attributes
        mesh.CreatePointsAttr(positions)
        mesh.CreateFaceVertexIndicesAttr(face_indices)
        mesh.CreateFaceVertexCountsAttr(face_counts)
        mesh.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        
        carb.log_info(f"[GeometryBuilder] Created double-wall cylinder: {outer_vertex_count} outer + {outer_vertex_count} inner = {len(positions)} total vertices")
        
        # Return ALL vertices and the split point
        return mesh, np.array(positions), outer_vertex_count
        
    def _generate_cylinder_geometry(
        self,
        height: float,
        radius: float,
        segments: int,
        radial_segments: int
    ) -> Tuple[List[Gf.Vec3f], List[int], List[int]]:
        """Generate vertex positions and face topology for cylinder"""
        positions = []
        face_indices = []
        face_counts = []
        
        # Generate vertices
        for seg in range(segments + 1):
            y = (seg / segments) * height
            
            for rad in range(radial_segments):
                angle = (rad / radial_segments) * 2.0 * np.pi
                x = radius * np.cos(angle)
                z = radius * np.sin(angle)
                positions.append(Gf.Vec3f(x, y, z))
        
        # Generate faces (quads)
        for seg in range(segments):
            for rad in range(radial_segments):
                # Current ring
                i0 = seg * radial_segments + rad
                i1 = seg * radial_segments + ((rad + 1) % radial_segments)
                
                # Next ring
                i2 = (seg + 1) * radial_segments + ((rad + 1) % radial_segments)
                i3 = (seg + 1) * radial_segments + rad
                
                # Create quad face
                face_indices.extend([i0, i1, i2, i3])
                face_counts.append(4)
        
        return positions, face_indices, face_counts
        
    def create_multiple_cylinders(
        self,
        parent_path: str,
        count: int,
        spacing: float = 3.0
    ) -> List[Tuple[UsdGeom.Mesh, np.ndarray]]:
        """
        Create multiple test cylinders arranged in a grid.
        Used for Phase 2 testing.
        """
        cylinders = []
        grid_size = int(np.ceil(np.sqrt(count)))
        
        for i in range(count):
            row = i // grid_size
            col = i % grid_size
            
            x = (col - grid_size / 2) * spacing
            z = (row - grid_size / 2) * spacing
            
            path = f"{parent_path}/cylinder_{i}"
            mesh, positions = self.create_test_cylinder(path)
            
            # Position the cylinder
            xform = UsdGeom.Xformable(mesh)
            xform.AddTranslateOp().Set(Gf.Vec3d(x, 0, z))
            
            cylinders.append((mesh, positions))
        
        return cylinders
        
    def apply_simple_material(self, mesh: UsdGeom.Mesh, color: Gf.Vec3f = Gf.Vec3f(0.2, 0.6, 0.8)):
        """
        Apply a simple opaque material to mesh.
        For Phase 3 testing with materials.
        """
        # Create material
        material_path = f"{mesh.GetPath()}_material"
        material = UsdShade.Material.Define(self.stage, material_path)
        
        # Bind material to mesh
        UsdShade.MaterialBindingAPI(mesh).Bind(material)
        
        return material
        
    def apply_glass_material(self, mesh: UsdGeom.Mesh, ior: float = 1.5):
        """
        Apply glass/transparent material with refraction.
        For Phase 4 & 5 testing.
        
        Phase 4: Single-surface (will crash)
        Phase 5: Double-wall (should work properly)
        """
        # Create material
        material_path = f"{mesh.GetPath()}_glass_material"
        material = UsdShade.Material.Define(self.stage, material_path)
        
        # Create shader
        shader = UsdShade.Shader.Define(self.stage, f"{material_path}/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")
        
        # Set glass-like properties
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(0.9, 0.9, 1.0))
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.0)
        shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.3)
        shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(ior)
        
        # Enable transmission for refraction
        shader.CreateInput("useSpecularWorkflow", Sdf.ValueTypeNames.Int).Set(1)
        
        # Connect shader to material output
        material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
        
        # Bind material to mesh
        UsdShade.MaterialBindingAPI(mesh).Bind(material)
        
        carb.log_info(f"[GeometryBuilder] Applied glass material with IOR {ior}")
        
        return material
