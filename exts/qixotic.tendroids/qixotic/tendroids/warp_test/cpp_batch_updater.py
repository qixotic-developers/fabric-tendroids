"""
C++ Accelerated Batch Mesh Updater

Uses C++ for vertex computation, Python for USD updates.
Expected 5-10x speedup over pure Python/Warp.
"""

import carb
import numpy as np
from pxr import UsdGeom, Gf

# Try to import C++ extension
CPP_AVAILABLE = False
try:
    from qixotic.tendroids import fast_mesh_updater
    CPP_AVAILABLE = True
    carb.log_info("[CppBatchUpdater] C++ extension loaded successfully")
except ImportError as e:
    carb.log_warn(f"[CppBatchUpdater] C++ extension not available: {e}")


class CppBatchMeshUpdater:
    """
    C++ accelerated batch mesh updater.
    
    Architecture:
    - C++ computes all vertex positions (fast math)
    - Python updates USD (necessary, no C++ USD libs available)
    - Zero-copy numpy arrays between Python/C++
    """
    
    def __init__(self):
        """Initialize C++ updater."""
        if not CPP_AVAILABLE:
            raise RuntimeError("C++ extension not available - build it first!")
        
        self.cpp_updater = fast_mesh_updater.FastMeshUpdater()
        self.mesh_prims = []
        self.base_vertices = None
        self.output_vertices = None
        self.num_tubes = 0
        self.verts_per_tube = 0
        
        carb.log_info(f"[CppBatchUpdater] {self.cpp_updater.get_mode()}")
        carb.log_info(f"[CppBatchUpdater] Version: {self.cpp_updater.get_version()}")
    
    def register_meshes(self, stage, mesh_paths: list):
        """
        Register meshes for batch updates.
        
        Args:
            stage: USD stage
            mesh_paths: List of mesh prim paths
        """
        self.mesh_prims = []
        all_base_verts = []
        
        for path in mesh_paths:
            prim = stage.GetPrimAtPath(path)
            if not prim.IsValid():
                carb.log_warn(f"[CppBatchUpdater] Invalid prim: {path}")
                continue
            
            mesh = UsdGeom.Mesh(prim)
            points_attr = mesh.GetPointsAttr()
            base_points = points_attr.Get()
            
            if not base_points:
                carb.log_warn(f"[CppBatchUpdater] No points for: {path}")
                continue
            
            # Store USD mesh reference
            self.mesh_prims.append({
                'mesh': mesh,
                'points_attr': points_attr,
                'base_points': base_points,
                'vertex_count': len(base_points)
            })
            
            # Flatten to numpy array
            verts_flat = []
            for pt in base_points:
                verts_flat.extend([pt[0], pt[1], pt[2]])
            all_base_verts.extend(verts_flat)
        
        if not self.mesh_prims:
            carb.log_error("[CppBatchUpdater] No valid meshes registered")
            return False
        
        # Create numpy arrays for C++ (zero-copy)
        self.num_tubes = len(self.mesh_prims)
        self.verts_per_tube = self.mesh_prims[0]['vertex_count']
        
        self.base_vertices = np.array(all_base_verts, dtype=np.float32)
        self.output_vertices = np.zeros_like(self.base_vertices)
        
        carb.log_info(f"[CppBatchUpdater] Registered {self.num_tubes} tubes, "
                     f"{self.verts_per_tube} verts/tube, "
                     f"{len(self.base_vertices)} total floats")
        
        return True
    
    def update(self, time: float, wave_speed: float = 2.0, 
              amplitude: float = 0.1, frequency: float = 1.0):
        """
        Update all meshes using C++ computation.
        
        Args:
            time: Animation time
            wave_speed: Wave propagation speed
            amplitude: Wave amplitude
            frequency: Wave frequency
        """
        if not self.mesh_prims:
            return
        
        # C++ computes all vertices (FAST)
        verts_processed = self.cpp_updater.batch_compute_vertices(
            self.base_vertices,
            self.output_vertices,
            self.num_tubes,
            self.verts_per_tube,
            time,
            wave_speed,
            amplitude,
            frequency
        )
        
        # Python updates USD (necessary)
        for tube_idx, mesh_info in enumerate(self.mesh_prims):
            start_idx = tube_idx * self.verts_per_tube * 3
            end_idx = start_idx + self.verts_per_tube * 3
            
            tube_verts = self.output_vertices[start_idx:end_idx]
            
            # Reshape to (N, 3) and convert to Gf.Vec3f
            points = []
            for i in range(0, len(tube_verts), 3):
                points.append(Gf.Vec3f(
                    tube_verts[i],
                    tube_verts[i + 1],
                    tube_verts[i + 2]
                ))
            
            # Update USD
            mesh_info['points_attr'].Set(points)
    
    def get_stats(self):
        """Get C++ performance stats."""
        if CPP_AVAILABLE:
            stats = self.cpp_updater.get_stats()
            return {
                'total_calls': stats.total_calls,
                'total_vertices': stats.total_vertices,
                'total_time_ms': stats.total_time_ms,
                'avg_time_ms': stats.avg_time_ms,
                'vertices_per_call': stats.total_vertices / stats.total_calls if stats.total_calls > 0 else 0
            }
        return None
    
    def reset_stats(self):
        """Reset performance counters."""
        if CPP_AVAILABLE:
            self.cpp_updater.reset_stats()
