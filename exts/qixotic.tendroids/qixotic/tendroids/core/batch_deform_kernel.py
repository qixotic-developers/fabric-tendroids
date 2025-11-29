"""
Batch Warp GPU Kernel for Multi-Tendroid Deformation

Processes ALL vertices from ALL tendroids in a SINGLE kernel launch.
Eliminates per-tendroid kernel overhead for massive performance gains.
"""

import warp as wp

wp.init()


@wp.kernel
def batch_deform_kernel(
    # Vertex data (all tendroids concatenated)
    base_points: wp.array(dtype=wp.vec3),
    out_points: wp.array(dtype=wp.vec3),
    height_factors: wp.array(dtype=float),
    
    # Per-vertex tendroid mapping
    vertex_tendroid_ids: wp.array(dtype=int),
    
    # Per-tendroid bubble state
    bubble_y: wp.array(dtype=float),
    bubble_radius: wp.array(dtype=float),
    
    # Per-tendroid wave displacement (pre-computed with spatial variation)
    wave_dx: wp.array(dtype=float),
    wave_dz: wp.array(dtype=float),
    
    # Per-tendroid geometry
    cylinder_radius: wp.array(dtype=float),
    cylinder_length: wp.array(dtype=float),
    max_amplitude: wp.array(dtype=float),
    bulge_width: wp.array(dtype=float),
):
    """
    Batch deform all vertices from all tendroids.
    
    Each thread processes one vertex:
    1. Look up which tendroid this vertex belongs to
    2. Fetch that tendroid's bubble state
    3. Apply deformation + wave
    """
    tid = wp.tid()
    
    # Which tendroid does this vertex belong to?
    tendroid_id = vertex_tendroid_ids[tid]
    
    # Fetch tendroid-specific parameters
    t_bubble_y = bubble_y[tendroid_id]
    t_bubble_radius = bubble_radius[tendroid_id]
    t_wave_dx = wave_dx[tendroid_id]
    t_wave_dz = wave_dz[tendroid_id]
    t_cyl_radius = cylinder_radius[tendroid_id]
    t_max_amp = max_amplitude[tendroid_id]
    t_bulge_width = bulge_width[tendroid_id]
    
    # Fetch vertex data
    pos = base_points[tid]
    h_factor = height_factors[tid]
    vertex_y = pos[1]
    
    # Calculate bubble deformation
    max_radius = t_cyl_radius * (1.0 + t_max_amp)
    radius_range = max_radius - t_cyl_radius
    
    growth_factor = 0.0
    if radius_range > 0.0:
        growth_factor = (t_bubble_radius - t_cyl_radius) / radius_range
        growth_factor = wp.clamp(growth_factor, 0.0, 1.0)
    
    current_amplitude = t_max_amp * growth_factor
    
    sigma = t_bubble_radius * t_bulge_width
    dist = vertex_y - t_bubble_y
    
    gaussian = 0.0
    if sigma > 0.0:
        gaussian = wp.exp(-(dist * dist) / (2.0 * sigma * sigma))
    
    displacement = current_amplitude * gaussian
    scale = 1.0 + displacement
    
    # Apply radial scaling
    scaled_x = pos[0] * scale
    scaled_z = pos[2] * scale
    
    # Add wave displacement
    final_x = scaled_x + t_wave_dx * h_factor
    final_z = scaled_z + t_wave_dz * h_factor
    
    out_points[tid] = wp.vec3(final_x, vertex_y, final_z)
