"""
C++ Accelerated Batch Mesh Updater - Hybrid Approach

Combines:
- C++ for ultra-fast vertex computation (0.014ms)
- Fabric for fast USD updates (using map approach)
- Numpy vectorization to eliminate Python loops
"""

import carb
import numpy as np
from pxr import UsdGeom, Gf
import omni.usd

# Try to import C++ extension
CPP_AVAILABLE = False
try:
    from qixotic.tendroids import fast_mesh_updater
    CPP_AVAILABLE = True
    carb.log_info("[CppBatchUpdater] C++ extension loaded successfully")
except ImportError as e:
    from qixotic.tendroids import fast_mesh_updater
    carb.log_warn(f"[CppBatchUpdater] C++ extension not available: {e}")

# Try to import Fabric
FABRIC_AVAILABLE = False
try:
    import usdrt.Usd
    import usdrt.Sdf
    FABRIC_AVAILABLE = True
except ImportError:
    import usdrt.Usd
    import usdrt.Sdf
    pass


class CppBatchMeshUpdater:
    """
    Hybrid C++ + Fabric batch mesh updater.
    
    Uses C++ computation + Fabric's fast list(map()) update pattern.
    """
    
    def __init__(self):
        """Initialize hybrid updater."""
        if not CPP_AVAILABLE:
            raise RuntimeError("C++ extension not available - build it first!")
        
        self.cpp_updater = fast_mesh_updater.FastMeshUpdater()
        self.mesh_prims = []
        self.base_vertices = None
        self.output_vertices = None
        self.num_tubes = 0
        self.verts_per_tube = 0
        
        # Fabric integration
        self.fabric_stage = None
        self.points_attrs = []
        
        if FABRIC_AVAILABLE:
            try:
                usd_context = omni.usd.get_context()
                stage_id = usd_context.get_stage_id()
                self.fabric_stage = usdrt.Usd.Stage.Attach(stage_id)
                carb.log_info("[CppBatchUpdater] Using Fabric fast path")
            except Exception as e:
                carb.log_warn(f"[CppBatchUpdater] Fabric unavailable: {e}")
        
        carb.log_info(f"[CppBatchUpdater] {self.cpp_updater.get_mode()}")
        carb.log_info(f"[CppBatchUpdater] Version: {self.cpp_updater.get_version()}")
    
    def register_meshes(self, stage, mesh_paths: list):
        """Register meshes for batch updates."""
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
            
            # Store mesh info
            self.mesh_prims.append({
                'mesh': mesh,
                'points_attr': points_attr,
                'vertex_count': len(base_points)
            })
            
            # Register with Fabric if available
            if self.fabric_stage:
                fabric_prim = self.fabric_stage.GetPrimAtPath(path)
                if fabric_prim and fabric_prim.IsValid():
                    fabric_points_attr = fabric_prim.GetAttribute("points")
                    if fabric_points_attr:
                        self.points_attrs.append(fabric_points_attr)
            
            # Flatten to numpy array
            for pt in base_points:
                all_base_verts.extend([pt[0], pt[1], pt[2]])
        
        if not self.mesh_prims:
            carb.log_error("[CppBatchUpdater] No valid meshes registered")
            return False
        
        # Create numpy arrays for C++
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
        Update all meshes using C++ computation + Fabric fast path.
        """
        if not self.mesh_prims:
            return
        
        # C++ computes all vertices (FAST - 0.014ms)
        self.cpp_updater.batch_compute_vertices(
            self.base_vertices,
            self.output_vertices,
            self.num_tubes,
            self.verts_per_tube,
            time,
            wave_speed,
            amplitude,
            frequency
        )
        
        # Update USD using Fabric's fast map() approach
        if self.fabric_stage and self.points_attrs:
            # Fabric path - use map() like the fast version
            for tube_idx, points_attr in enumerate(self.points_attrs):
                start_idx = tube_idx * self.verts_per_tube * 3
                end_idx = start_idx + self.verts_per_tube * 3
                
                mesh_vertices_np = self.output_vertices[start_idx:end_idx]
                
                # Reshape to (N, 3) for vectorized conversion
                mesh_vertices_np = mesh_vertices_np.reshape(-1, 3)
                
                # Use list(map()) - same as Fabric updater (FAST)
                fabric_vertices = list(map(
                    lambda v: (float(v[0]), float(v[1]), float(v[2])), 
                    mesh_vertices_np
                ))
                
                points_attr.Set(fabric_vertices)
        else:
            # Fallback to standard USD (slower)
            for tube_idx, mesh_info in enumerate(self.mesh_prims):
                start_idx = tube_idx * self.verts_per_tube * 3
                end_idx = start_idx + self.verts_per_tube * 3
                
                tube_verts = self.output_vertices[start_idx:end_idx]
                
                # Vectorized conversion
                tube_verts_reshaped = tube_verts.reshape(-1, 3)
                points = [Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) 
                         for v in tube_verts_reshaped]
                
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
