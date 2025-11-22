"""
V2 Warp GPU Kernel for Bubble-Guided Cylinder Deformation

Runs deformation calculations on GPU for maximum performance.
Each vertex is processed in parallel by a separate GPU thread.
"""

import warp as wp

wp.init()


@wp.kernel
def deform_cylinder_kernel(
    base_points: wp.array(dtype=wp.vec3),
    out_points: wp.array(dtype=wp.vec3),
    bubble_y: float,
    bubble_radius: float,
    cylinder_radius: float,
    max_amplitude: float,
    bulge_width: float,
):
    """
    GPU kernel to deform cylinder vertices based on bubble position.
    
    Each thread processes one vertex:
    1. Calculate growth factor (how much bubble exceeds cylinder)
    2. Calculate Gaussian falloff based on distance from bubble
    3. Scale vertex radially by displacement amount
    """
    tid = wp.tid()
    
    pos = base_points[tid]
    vertex_y = pos[1]
    
    max_radius = cylinder_radius * (1.0 + max_amplitude)
    radius_range = max_radius - cylinder_radius
    
    growth_factor = 0.0
    if radius_range > 0.0:
        growth_factor = (bubble_radius - cylinder_radius) / radius_range
        growth_factor = wp.clamp(growth_factor, 0.0, 1.0)
    
    current_amplitude = max_amplitude * growth_factor
    
    sigma = bubble_radius * bulge_width
    dist = vertex_y - bubble_y
    gaussian = wp.exp(-(dist * dist) / (2.0 * sigma * sigma))
    
    displacement = current_amplitude * gaussian
    scale = 1.0 + displacement
    
    out_points[tid] = wp.vec3(pos[0] * scale, pos[1], pos[2] * scale)


class V2WarpDeformer:
    """
    Warp-accelerated cylinder deformer.
    
    Pre-allocates GPU arrays and launches kernel each frame.
    """
    
    def __init__(
        self,
        base_points_list: list,
        cylinder_radius: float = 10.0,
        max_amplitude: float = 0.8,
        bulge_width: float = 0.9,
        device: str = "cuda:0"
    ):
        """
        Args:
            base_points_list: List of Gf.Vec3f base vertex positions
            cylinder_radius: Base cylinder radius
            max_amplitude: Maximum radial expansion fraction
            bulge_width: Gaussian width multiplier
            device: Warp device ("cuda:0" for GPU)
        """
        self.cylinder_radius = cylinder_radius
        self.max_amplitude = max_amplitude
        self.bulge_width = bulge_width
        self.device = device
        self.num_points = len(base_points_list)
        
        points_data = [(p[0], p[1], p[2]) for p in base_points_list]
        
        self.base_points_gpu = wp.array(points_data, dtype=wp.vec3, device=device)
        self.out_points_gpu = wp.zeros(self.num_points, dtype=wp.vec3, device=device)
        self._out_cpu = None
    
    def deform(self, bubble_y: float, bubble_radius: float) -> list:
        """
        Run deformation kernel and return new points.
        """
        wp.launch(
            kernel=deform_cylinder_kernel,
            dim=self.num_points,
            inputs=[
                self.base_points_gpu,
                self.out_points_gpu,
                bubble_y,
                bubble_radius,
                self.cylinder_radius,
                self.max_amplitude,
                self.bulge_width,
            ],
            device=self.device
        )
        
        return self.out_points_gpu.numpy()
    
    def destroy(self):
        """Free GPU resources."""
        self.base_points_gpu = None
        self.out_points_gpu = None
