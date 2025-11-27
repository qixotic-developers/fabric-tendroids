"""
Batch Warp Deformer Manager

Manages GPU arrays for batch processing ALL tendroid vertices
in a single kernel launch. Eliminates per-tendroid kernel overhead.
"""

import numpy as np
import warp as wp

from .batch_deform_kernel import batch_deform_kernel

wp.init()


class BatchWarpDeformer:
    """
    Batch processor for multi-tendroid deformation.
    
    Concatenates all vertex data into contiguous GPU arrays,
    enabling single-kernel processing of entire scene.
    """
    
    def __init__(self, device: str = "cuda:0"):
        self.device = device
        self.tendroids = []
        self.tendroid_names = []
        self.name_to_index = {}
        self.vertex_offsets = []
        self.vertex_counts = []
        self.total_vertices = 0
        
        # GPU arrays
        self.base_points_gpu = None
        self.out_points_gpu = None
        self.height_factors_gpu = None
        self.vertex_tendroid_ids_gpu = None
        self.bubble_y_gpu = None
        self.bubble_radius_gpu = None
        self.wave_dx_gpu = None
        self.wave_dz_gpu = None
        self.cylinder_radius_gpu = None
        self.cylinder_length_gpu = None
        self.max_amplitude_gpu = None
        self.bulge_width_gpu = None
        
        # CPU staging (reused)
        self._bubble_y_cpu = None
        self._bubble_radius_cpu = None
        self._wave_dx_cpu = None
        self._wave_dz_cpu = None
        self._built = False
    
    def register_tendroid(self, tendroid, base_points: list):
        """Register a tendroid for batch processing."""
        if self._built:
            raise RuntimeError("Cannot register after build()")
        name = tendroid.name
        if name in self.name_to_index:
            return
        index = len(self.tendroids)
        self.name_to_index[name] = index
        self.tendroids.append(tendroid)
        self.tendroid_names.append(name)
        self.vertex_offsets.append(self.total_vertices)
        self.vertex_counts.append(len(base_points))
        self.total_vertices += len(base_points)
    
    def build(self):
        """Build GPU arrays after all tendroids registered."""
        if self._built or not self.tendroids:
            return
        n_tendroids = len(self.tendroids)
        
        all_base_points = []
        all_height_factors = []
        all_tendroid_ids = []
        
        for i, tendroid in enumerate(self.tendroids):
            deformer = tendroid.deformer
            base_pts = deformer.base_points_gpu.numpy()
            height_facs = deformer.height_factors_gpu.numpy()
            for j in range(len(base_pts)):
                all_base_points.append(tuple(base_pts[j]))
                all_height_factors.append(float(height_facs[j]))
                all_tendroid_ids.append(i)
        
        self.base_points_gpu = wp.array(all_base_points, dtype=wp.vec3, device=self.device)
        self.out_points_gpu = wp.zeros(self.total_vertices, dtype=wp.vec3, device=self.device)
        self.height_factors_gpu = wp.array(all_height_factors, dtype=float, device=self.device)
        self.vertex_tendroid_ids_gpu = wp.array(all_tendroid_ids, dtype=int, device=self.device)
        
        cyl_radii = [t.radius for t in self.tendroids]
        self.cylinder_radius_gpu = wp.array(cyl_radii, dtype=float, device=self.device)
        self.cylinder_length_gpu = wp.array([t.length for t in self.tendroids], dtype=float, device=self.device)
        self.max_amplitude_gpu = wp.array([t.deformer.max_amplitude for t in self.tendroids], dtype=float, device=self.device)
        self.bulge_width_gpu = wp.array([t.deformer.bulge_width for t in self.tendroids], dtype=float, device=self.device)
        
        self.bubble_y_gpu = wp.zeros(n_tendroids, dtype=float, device=self.device)
        self.bubble_radius_gpu = wp.array(cyl_radii, dtype=float, device=self.device)
        self.wave_dx_gpu = wp.zeros(n_tendroids, dtype=float, device=self.device)
        self.wave_dz_gpu = wp.zeros(n_tendroids, dtype=float, device=self.device)
        
        self._bubble_y_cpu = np.zeros(n_tendroids, dtype=np.float32)
        self._bubble_radius_cpu = np.array(cyl_radii, dtype=np.float32)
        self._wave_dx_cpu = np.zeros(n_tendroids, dtype=np.float32)
        self._wave_dz_cpu = np.zeros(n_tendroids, dtype=np.float32)
        self._built = True
    
    def update_states(self, bubble_data: dict, wave_state: dict, default_config):
        """Update tendroid states from bubble data."""
        if not self._built:
            return
        
        wave_enabled = wave_state.get('enabled', False)
        wave_disp = wave_state.get('displacement', 0.0)
        wave_amp = wave_state.get('amplitude', 0.0)
        wave_dx = wave_state.get('dir_x', 0.0)
        wave_dz = wave_state.get('dir_z', 0.0)
        
        for i, tendroid in enumerate(self.tendroids):
            name = tendroid.name
            bubble_y = 0.0
            bubble_radius = tendroid.radius
            
            if name in bubble_data:
                data = bubble_data[name]
                if data['phase'] in (1, 2):
                    bubble_y = data['position'][1] - tendroid.position[1]
                    bubble_radius = data['radius'] * default_config.diameter_multiplier
            
            self._bubble_y_cpu[i] = bubble_y
            self._bubble_radius_cpu[i] = bubble_radius
            
            if wave_enabled:
                t_x, t_z = tendroid.position[0], tendroid.position[2]
                spatial = 1.0 + np.sin(t_x * 0.003 + t_z * 0.002) * 0.15
                d = wave_disp * spatial
                self._wave_dx_cpu[i] = d * wave_amp * wave_dx
                self._wave_dz_cpu[i] = d * wave_amp * wave_dz
            else:
                self._wave_dx_cpu[i] = 0.0
                self._wave_dz_cpu[i] = 0.0
        
        # Direct array assignment (Warp handles this efficiently)
        self.bubble_y_gpu = wp.array(self._bubble_y_cpu, dtype=float, device=self.device)
        self.bubble_radius_gpu = wp.array(self._bubble_radius_cpu, dtype=float, device=self.device)
        self.wave_dx_gpu = wp.array(self._wave_dx_cpu, dtype=float, device=self.device)
        self.wave_dz_gpu = wp.array(self._wave_dz_cpu, dtype=float, device=self.device)
    
    def deform_all(self):
        """Launch single kernel to deform ALL vertices."""
        if not self._built:
            return None
        wp.launch(
            kernel=batch_deform_kernel,
            dim=self.total_vertices,
            inputs=[
                self.base_points_gpu, self.out_points_gpu, self.height_factors_gpu,
                self.vertex_tendroid_ids_gpu,
                self.bubble_y_gpu, self.bubble_radius_gpu,
                self.wave_dx_gpu, self.wave_dz_gpu,
                self.cylinder_radius_gpu, self.cylinder_length_gpu,
                self.max_amplitude_gpu, self.bulge_width_gpu,
            ],
            device=self.device
        )
        return self.out_points_gpu.numpy()
    
    def apply_to_meshes(self, all_points: np.ndarray):
        """Apply deformed points to USD meshes - CPU PATH."""
        if all_points is None:
            return
        from pxr import Vt, UsdGeom
        
        for i, tendroid in enumerate(self.tendroids):
            offset = self.vertex_offsets[i]
            count = self.vertex_counts[i]
            # numpy tolist() is C-optimized, much faster than per-element conversion
            points_tuples = all_points[offset:offset + count].tolist()
            
            if hasattr(tendroid, 'mesh_prim') and tendroid.mesh_prim:
                mesh = UsdGeom.Mesh(tendroid.mesh_prim)
                mesh.GetPointsAttr().Set(Vt.Vec3fArray(points_tuples))
    
    def apply_to_meshes_fabric(self, stage_id):
        """Apply deformed points via Fabric - GPU PATH (FAST)."""
        if not self._built:
            return
        
        from usdrt import Vt
        from ..utils import FabricHelper
        
        # Get USDRT stage (cached)
        usdrt_stage = FabricHelper.get_usdrt_stage(stage_id)
        
        # CRITICAL: Do ONE GPU→CPU transfer for all vertices
        # Multiple numpy() calls create GPU sync points causing stuttering
        all_points_cpu = self.out_points_gpu.numpy()
        
        # Apply to each tendroid mesh
        for i, tendroid in enumerate(self.tendroids):
            offset = self.vertex_offsets[i]
            count = self.vertex_counts[i]
            
            # Get mesh path
            if hasattr(tendroid, 'mesh_path'):
                mesh_path = tendroid.mesh_path
            elif hasattr(tendroid, 'mesh_prim') and tendroid.mesh_prim:
                mesh_path = str(tendroid.mesh_prim.GetPath())
            else:
                continue
            
            # Get Fabric points attribute
            points_attr = FabricHelper.get_fabric_points_attribute(
                usdrt_stage, mesh_path
            )
            if not points_attr:
                continue
            
            # Extract slice from CPU numpy array (no GPU sync!)
            tendroid_points = all_points_cpu[offset:offset + count]
            
            # Write to Fabric - VtArray constructor accepts numpy directly
            # No tolist() needed - numpy is passed as-is
            points_attr.Set(Vt.Vec3fArray(tendroid_points))
    
    def reset(self):
        """Reset to pre-build state."""
        self.destroy()
        self.tendroids.clear()
        self.tendroid_names.clear()
        self.name_to_index.clear()
        self.vertex_offsets.clear()
        self.vertex_counts.clear()
        self.total_vertices = 0
        self._built = False
    
    def destroy(self):
        """Free all GPU resources."""
        for attr in ['base_points_gpu', 'out_points_gpu', 'height_factors_gpu',
                     'vertex_tendroid_ids_gpu', 'bubble_y_gpu', 'bubble_radius_gpu',
                     'wave_dx_gpu', 'wave_dz_gpu', 'cylinder_radius_gpu',
                     'cylinder_length_gpu', 'max_amplitude_gpu', 'bulge_width_gpu']:
            setattr(self, attr, None)
        self._bubble_y_cpu = self._bubble_radius_cpu = None
        self._wave_dx_cpu = self._wave_dz_cpu = None
    
    @property
    def is_built(self) -> bool:
        return self._built
    
    @property
    def tendroid_count(self) -> int:
        return len(self.tendroids)
