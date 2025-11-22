"""
V2 Deformer - Bubble-guided cylinder deformation (CPU version)

Creates a bulge profile that follows the rising bubble.
Deformation scales with bubble size - no deformation when bubble
equals cylinder diameter, full deformation at max bubble diameter.
"""

import math
import carb


class V2Deformer:
    """
    Deforms cylinder vertices based on bubble position and size.
    
    Displacement is zero when bubble_radius == cylinder_radius,
    and scales up to max_amplitude when bubble reaches max_radius.
    """
    
    def __init__(
        self,
        cylinder_radius: float = 10.0,
        cylinder_length: float = 100.0,
        max_bulge_amplitude: float = 0.8,
        bulge_width: float = 2.0
    ):
        """
        Args:
            cylinder_radius: Base radius of cylinder
            cylinder_length: Total cylinder height (Y-axis)
            max_bulge_amplitude: Maximum radial expansion at full bubble size
            bulge_width: Width of bulge as multiple of bubble radius
        """
        self.cylinder_radius = cylinder_radius
        self.cylinder_length = cylinder_length
        self.max_amplitude = max_bulge_amplitude
        self.bulge_width = bulge_width
    
    def calculate_displacement(
        self,
        vertex_y: float,
        bubble_y: float,
        bubble_radius: float
    ) -> float:
        """
        Calculate radial displacement.
        
        Args:
            vertex_y: Y position of the vertex
            bubble_y: Current Y position of bubble center
            bubble_radius: Current radius of the bubble
            
        Returns:
            Displacement as fraction (0 when bubble=cylinder, max when full)
        """
        max_radius = self.cylinder_radius * (1.0 + self.max_amplitude)
        radius_range = max_radius - self.cylinder_radius
        
        if radius_range <= 0:
            return 0.0
        
        growth_factor = (bubble_radius - self.cylinder_radius) / radius_range
        growth_factor = max(0.0, min(1.0, growth_factor))
        
        current_amplitude = self.max_amplitude * growth_factor
        sigma = bubble_radius * self.bulge_width
        dist = vertex_y - bubble_y
        gaussian = math.exp(-(dist * dist) / (2.0 * sigma * sigma))
        
        return current_amplitude * gaussian
