"""
V2 Warp GPU Kernel for Bubble-Guided Cylinder Deformation

Runs deformation calculations on GPU for maximum performance.
Each vertex is processed in parallel by a separate GPU thread.

Now includes wave displacement composition - wave and deformation
are applied together in a single GPU pass.
"""

import warp as wp

wp.init()


@wp.kernel
def deform_cylinder_kernel(
    base_points: wp.array(dtype=wp.vec3),
    out_points: wp.array(dtype=wp.vec3),
    height_factors: wp.array(dtype=float),
    bubble_y: float,
    bubble_radius: float,
    cylinder_radius: float,
    cylinder_length: float,
    max_amplitude: float,
    bulge_width: float,
    wave_dx: float,
    wave_dz: float,
):
    """
    GPU kernel to deform cylinder vertices based on bubble position.
    
    Each thread processes one vertex:
    1. Calculate bubble deformation (Gaussian bulge) on ORIGINAL position
    2. Apply wave displacement AFTER radial scaling
    3. This ensures wave and deformation are independent
    
    CRITICAL: Wave displacement must be added AFTER radial scaling,
    not multiplied through it. Otherwise the centerline moves when
    the bubble passes and the visual won't match.
    """
    tid = wp.tid()
    
    pos = base_points[tid]
    vertex_y = pos[1]
    h_factor = height_factors[tid]
    
    # Step 1: Calculate bubble deformation on ORIGINAL position
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
    
    # Step 2: Apply radial scaling to ORIGINAL position
    scaled_x = pos[0] * scale
    scaled_z = pos[2] * scale
    
    # Step 3: Add wave displacement AFTER scaling (independent of bulge)
    final_x = scaled_x + wave_dx * h_factor
    final_z = scaled_z + wave_dz * h_factor
    
    out_points[tid] = wp.vec3(final_x, vertex_y, final_z)


@wp.kernel
def deform_cylinder_kernel_with_wave_state(
    base_points: wp.array(dtype=wp.vec3),
    out_points: wp.array(dtype=wp.vec3),
    height_factors: wp.array(dtype=float),
    bubble_y: float,
    bubble_radius: float,
    cylinder_radius: float,
    cylinder_length: float,
    max_amplitude: float,
    bulge_width: float,
    # Wave state (computed on GPU)
    wave_displacement: float,
    wave_amplitude: float,
    wave_dir_x: float,
    wave_dir_z: float,
    tendroid_world_x: float,
    tendroid_world_z: float,
):
    """
    GPU kernel with wave computed internally.
    
    Computes spatial variation per-vertex on GPU, eliminating
    per-tendroid Python get_displacement() calls.
    """
    tid = wp.tid()
    
    pos = base_points[tid]
    vertex_y = pos[1]
    h_factor = height_factors[tid]
    
    # Compute wave displacement with spatial variation ON GPU
    spatial_phase = tendroid_world_x * 0.003 + tendroid_world_z * 0.002
    spatial_factor = 1.0 + wp.sin(spatial_phase) * 0.15
    
    displacement_value = wave_displacement * spatial_factor
    wave_dx = displacement_value * wave_amplitude * wave_dir_x
    wave_dz = displacement_value * wave_amplitude * wave_dir_z
    
    # Bubble deformation on ORIGINAL position
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
    
    # Apply radial scaling to ORIGINAL position
    scaled_x = pos[0] * scale
    scaled_z = pos[2] * scale
    
    # Add wave displacement AFTER scaling
    final_x = scaled_x + wave_dx * h_factor
    final_z = scaled_z + wave_dz * h_factor
    
    out_points[tid] = wp.vec3(final_x, vertex_y, final_z)


class V2WarpDeformer:
    """
    Warp-accelerated cylinder deformer with wave composition.
    
    Pre-allocates GPU arrays and launches kernel each frame.
    Wave displacement and bubble deformation are combined in one pass.
    """
    
    def __init__(
        self,
        base_points_list: list,
        cylinder_radius: float = 10.0,
        cylinder_length: float = 100.0,
        max_amplitude: float = 0.8,
        bulge_width: float = 0.9,
        device: str = "cuda:0"
    ):
        """
        Args:
            base_points_list: List of Gf.Vec3f base vertex positions
            cylinder_radius: Base cylinder radius
            cylinder_length: Cylinder height (for height factor calc)
            max_amplitude: Maximum radial expansion fraction
            bulge_width: Gaussian width multiplier
            device: Warp device ("cuda:0" for GPU)
        """
        self.cylinder_radius = cylinder_radius
        self.cylinder_length = cylinder_length
        self.max_amplitude = max_amplitude
        self.bulge_width = bulge_width
        self.device = device
        self.num_points = len(base_points_list)
        
        # Convert points to tuples
        points_data = [(p[0], p[1], p[2]) for p in base_points_list]
        
        # Pre-compute height factors (cubic interpolation for smooth sway)
        height_factors = []
        for p in base_points_list:
            if cylinder_length > 0:
                ratio = max(0.0, min(1.0, p[1] / cylinder_length))
                # Smooth cubic: t^2 * (3 - 2t)
                factor = ratio * ratio * (3.0 - 2.0 * ratio)
            else:
                factor = 0.0
            height_factors.append(factor)
        
        # Upload to GPU
        self.base_points_gpu = wp.array(points_data, dtype=wp.vec3, device=device)
        self.height_factors_gpu = wp.array(height_factors, dtype=float, device=device)
        self.out_points_gpu = wp.zeros(self.num_points, dtype=wp.vec3, device=device)
    
    def deform(
        self, 
        bubble_y: float, 
        bubble_radius: float,
        wave_dx: float = 0.0,
        wave_dz: float = 0.0
    ) -> list:
        """
        Run deformation kernel with wave composition.
        
        Args:
            bubble_y: Bubble center Y position
            bubble_radius: Current bubble radius
            wave_dx: Wave displacement in X
            wave_dz: Wave displacement in Z
            
        Returns:
            NumPy array of deformed points
        """
        wp.launch(
            kernel=deform_cylinder_kernel,
            dim=self.num_points,
            inputs=[
                self.base_points_gpu,
                self.out_points_gpu,
                self.height_factors_gpu,
                bubble_y,
                bubble_radius,
                self.cylinder_radius,
                self.cylinder_length,
                self.max_amplitude,
                self.bulge_width,
                wave_dx,
                wave_dz,
            ],
            device=self.device
        )
        
        return self.out_points_gpu.numpy()
    
    def deform_wave_only(self, wave_dx: float, wave_dz: float) -> list:
        """
        Apply wave displacement only (no bubble deformation).
        
        Used when no bubble is active.
        """
        return self.deform(
            bubble_y=0.0,
            bubble_radius=self.cylinder_radius,  # No deformation at cylinder radius
            wave_dx=wave_dx,
            wave_dz=wave_dz
        )
    
    def deform_with_wave_state(
        self,
        bubble_y: float,
        bubble_radius: float,
        wave_state: dict,
        tendroid_world_x: float,
        tendroid_world_z: float
    ) -> list:
        """
        Run deformation with wave computed on GPU.
        
        This is faster than deform() because wave spatial variation
        is computed per-vertex on GPU, not per-tendroid in Python.
        
        Args:
            bubble_y: Bubble center Y position
            bubble_radius: Current bubble radius
            wave_state: Dict from WaveController.get_wave_state()
            tendroid_world_x: Tendroid world X position
            tendroid_world_z: Tendroid world Z position
            
        Returns:
            NumPy array of deformed points
        """
        if not wave_state.get('enabled', False):
            # Wave disabled - use simple kernel
            return self.deform(bubble_y, bubble_radius, 0.0, 0.0)
        
        wp.launch(
            kernel=deform_cylinder_kernel_with_wave_state,
            dim=self.num_points,
            inputs=[
                self.base_points_gpu,
                self.out_points_gpu,
                self.height_factors_gpu,
                bubble_y,
                bubble_radius,
                self.cylinder_radius,
                self.cylinder_length,
                self.max_amplitude,
                self.bulge_width,
                wave_state['displacement'],
                wave_state['amplitude'],
                wave_state['dir_x'],
                wave_state['dir_z'],
                tendroid_world_x,
                tendroid_world_z,
            ],
            device=self.device
        )
        
        return self.out_points_gpu.numpy()
    
    def deform_wave_only_with_state(
        self,
        wave_state: dict,
        tendroid_world_x: float,
        tendroid_world_z: float
    ) -> list:
        """
        Apply wave displacement only using GPU-computed spatial variation.
        
        Used when no bubble is active.
        """
        return self.deform_with_wave_state(
            bubble_y=0.0,
            bubble_radius=self.cylinder_radius,
            wave_state=wave_state,
            tendroid_world_x=tendroid_world_x,
            tendroid_world_z=tendroid_world_z
        )
    
    def destroy(self):
        """Free GPU resources."""
        self.base_points_gpu = None
        self.height_factors_gpu = None
        self.out_points_gpu = None
