"""
Warp Deflection Deformer Kernel - Combined wave/bubble/bend in single pass

Applies deflection bending along with wave and bubble deformation.
Order: base_points → bend → wave → bubble → output

This ensures consistent mesh state without accumulated distortion.
"""

import math
import warp as wp

wp.init()


@wp.kernel
def deform_with_deflection_kernel(
    base_points: wp.array(dtype=wp.vec3),
    out_points: wp.array(dtype=wp.vec3),
    height_factors: wp.array(dtype=float),
    # Bubble parameters
    bubble_y: float,
    bubble_radius: float,
    cylinder_radius: float,
    cylinder_length: float,
    max_amplitude: float,
    bulge_width: float,
    # Wave parameters
    wave_dx: float,
    wave_dz: float,
    # Deflection parameters
    deflection_angle: float,
    deflection_axis_x: float,
    deflection_axis_z: float,
):
    """
    Combined deformation kernel: bend → wave → bubble.
    
    Each vertex is processed in order:
    1. Apply progressive bend based on height
    2. Apply wave displacement
    3. Apply bubble bulge deformation
    
    This ensures consistent mesh state each frame.
    """
    tid = wp.tid()
    
    pos = base_points[tid]
    vertex_y = pos[1]
    h_factor = height_factors[tid]
    
    # =========================================================================
    # Step 1: Apply deflection bend
    # =========================================================================
    bent_x = pos[0]
    bent_y = vertex_y
    bent_z = pos[2]
    
    if wp.abs(deflection_angle) > 0.0001:
        # Vertex-specific bend angle (more at top, less at base)
        v_angle = deflection_angle * h_factor
        
        if wp.abs(v_angle) > 0.0001:
            # Normalize axis (should already be normalized but ensure)
            axis_len = wp.sqrt(deflection_axis_x * deflection_axis_x + 
                               deflection_axis_z * deflection_axis_z)
            ax = deflection_axis_x
            az = deflection_axis_z
            if axis_len > 0.0001:
                ax = deflection_axis_x / axis_len
                az = deflection_axis_z / axis_len
            
            # Perpendicular direction in XZ plane (bend direction)
            perp_x = -az
            perp_z = ax
            
            cos_a = wp.cos(v_angle)
            sin_a = wp.sin(v_angle)
            
            # Distance from center along perpendicular direction
            perp_dist = pos[0] * perp_x + pos[2] * perp_z
            
            # Distance along axis direction
            axis_dist = pos[0] * ax + pos[2] * az
            
            # Apply rotation in plane perpendicular to axis
            new_perp_dist = perp_dist * cos_a - vertex_y * sin_a
            new_y = perp_dist * sin_a + vertex_y * cos_a
            
            # Reconstruct XZ position
            bent_x = ax * axis_dist + perp_x * new_perp_dist
            bent_z = az * axis_dist + perp_z * new_perp_dist
            bent_y = new_y
    
    # =========================================================================
    # Step 2: Apply bubble deformation (on bent position)
    # =========================================================================
    # Use bent_y for bubble calculation but original vertex_y for height-based effects
    max_radius = cylinder_radius * (1.0 + max_amplitude)
    radius_range = max_radius - cylinder_radius
    
    growth_factor = 0.0
    if radius_range > 0.0:
        growth_factor = (bubble_radius - cylinder_radius) / radius_range
        growth_factor = wp.clamp(growth_factor, 0.0, 1.0)
    
    current_amplitude = max_amplitude * growth_factor
    
    sigma = bubble_radius * bulge_width
    # Use original vertex_y for bubble position calculation
    dist = vertex_y - bubble_y
    gaussian = wp.exp(-(dist * dist) / (2.0 * sigma * sigma))
    
    displacement = current_amplitude * gaussian
    scale = 1.0 + displacement
    
    # Apply radial scaling to bent XZ position
    scaled_x = bent_x * scale
    scaled_z = bent_z * scale
    
    # =========================================================================
    # Step 3: Apply wave displacement (after scaling)
    # =========================================================================
    final_x = scaled_x + wave_dx * h_factor
    final_z = scaled_z + wave_dz * h_factor
    
    out_points[tid] = wp.vec3(final_x, bent_y, final_z)


def launch_deflection_deform(
    base_points_gpu: wp.array,
    out_points_gpu: wp.array,
    height_factors_gpu: wp.array,
    bubble_y: float,
    bubble_radius: float,
    cylinder_radius: float,
    cylinder_length: float,
    max_amplitude: float,
    bulge_width: float,
    wave_dx: float,
    wave_dz: float,
    deflection_angle: float,
    deflection_axis: tuple,
    device: str = "cuda:0"
) -> None:
    """
    Launch combined deformation kernel.
    
    Args:
        base_points_gpu: Input vertex positions
        out_points_gpu: Output vertex positions
        height_factors_gpu: Pre-computed height factors
        bubble_y: Bubble center Y position
        bubble_radius: Current bubble radius
        cylinder_radius: Base cylinder radius
        cylinder_length: Cylinder height
        max_amplitude: Maximum radial expansion
        bulge_width: Gaussian width multiplier
        wave_dx: Wave displacement X
        wave_dz: Wave displacement Z
        deflection_angle: Bend angle in radians
        deflection_axis: (x, z) bend axis direction
        device: Warp device
    """
    num_points = base_points_gpu.shape[0]
    
    # Extract axis components
    ax, az = deflection_axis if deflection_axis else (1.0, 0.0)
    
    # Normalize axis
    length = math.sqrt(ax * ax + az * az)
    if length > 0.0001:
        ax /= length
        az /= length
    else:
        ax, az = 1.0, 0.0
    
    wp.launch(
        kernel=deform_with_deflection_kernel,
        dim=num_points,
        inputs=[
            base_points_gpu,
            out_points_gpu,
            height_factors_gpu,
            bubble_y,
            bubble_radius,
            cylinder_radius,
            cylinder_length,
            max_amplitude,
            bulge_width,
            wave_dx,
            wave_dz,
            deflection_angle,
            ax,
            az,
        ],
        device=device
    )
