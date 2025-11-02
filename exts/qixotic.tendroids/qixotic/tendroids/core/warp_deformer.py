"""
Warp-based vertex deformer for smooth Tendroid breathing animation

Uses GPU-accelerated Warp kernels to deform cylinder vertices with
radial displacement based on a traveling sine wave.
"""

import warp as wp
import carb
from pxr import Gf


@wp.kernel
def deform_breathing_wave(
    original_positions: wp.array(dtype=wp.vec3),
    deformed_positions: wp.array(dtype=wp.vec3),
    wave_center: float,
    wave_length: float,
    amplitude: float,
    deform_start_y: float
):
    """
    Warp kernel: Apply breathing wave deformation to cylinder vertices.
    
    Displaces vertices radially based on distance from wave center.
    Only affects vertices above deform_start_y (preserves flared base).
    """
    tid = wp.tid()
    
    # Get original position
    pos = original_positions[tid]
    x = pos[0]
    y = pos[1]
    z = pos[2]
    
    # Skip vertices below deformation zone
    if y < deform_start_y:
        deformed_positions[tid] = pos
        return
    
    # Calculate radial distance from Y axis
    radial_dist = wp.sqrt(x * x + z * z)
    
    # Avoid division by zero
    if radial_dist < 0.001:
        deformed_positions[tid] = pos
        return
    
    # Calculate distance from wave center
    distance = wp.abs(y - wave_center)
    
    # Gaussian-like falloff
    falloff = wave_length / 2.0
    
    # Wave displacement (only positive lobe)
    displacement = 1.0
    if distance < falloff * 2.0:
        phase = (distance / falloff) * 3.14159265
        wave_value = wp.cos(phase)
        if wave_value > 0.0:
            displacement = 1.0 + (wave_value * amplitude)
    
    # Apply radial displacement
    scale = displacement
    new_x = x * scale
    new_z = z * scale
    
    deformed_positions[tid] = wp.vec3(new_x, y, new_z)


class WarpDeformer:
    """
    GPU-accelerated mesh deformer using Warp.
    
    Manages vertex buffers and applies breathing wave deformation
    each frame without recreating data structures.
    """

    def __init__(self, original_vertices: list, deform_start_height: float):
        """
        Initialize deformer with mesh geometry.
        
        Args:
            original_vertices: List of Gf.Vec3f vertices
            deform_start_height: Y height where deformation begins
        """
        self.deform_start_height = deform_start_height
        self.num_vertices = len(original_vertices)
        
        # Convert to Warp arrays
        vertices_data = [(v[0], v[1], v[2]) for v in original_vertices]
        self.original_positions = wp.array(vertices_data, dtype=wp.vec3, device="cuda")
        self.deformed_positions = wp.array(vertices_data, dtype=wp.vec3, device="cuda")
        
        carb.log_info(
            f"[WarpDeformer] Initialized with {self.num_vertices} vertices, "
            f"deform_start={deform_start_height:.2f}"
        )

    def update(
        self,
        wave_center: float,
        wave_length: float,
        amplitude: float
    ) -> list:
        """
        Apply deformation and return updated vertex positions.
        
        Args:
            wave_center: Current Y position of wave center
            wave_length: Length of the breathing wave
            amplitude: Maximum radial expansion factor
            
        Returns:
            List of Gf.Vec3f deformed vertices
        """
        # Launch Warp kernel
        wp.launch(
            kernel=deform_breathing_wave,
            dim=self.num_vertices,
            inputs=[
                self.original_positions,
                self.deformed_positions,
                wave_center,
                wave_length,
                amplitude,
                self.deform_start_height
            ],
            device="cuda"
        )
        
        # Copy results back to CPU
        deformed_data = self.deformed_positions.numpy()
        
        # Convert to Gf.Vec3f
        return [Gf.Vec3f(float(v[0]), float(v[1]), float(v[2])) for v in deformed_data]

    def cleanup(self):
        """Release Warp resources."""
        self.original_positions = None
        self.deformed_positions = None
