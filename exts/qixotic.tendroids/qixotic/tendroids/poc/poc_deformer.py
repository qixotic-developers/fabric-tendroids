"""
POC Deformer - Bubble-guided cylinder deformation

Creates a bulge profile that follows and contains the rising bubble.
Uses smooth Gaussian curve for natural falloff.
"""

import math
import carb


class POCDeformer:
    """
    Deforms cylinder vertices based on bubble position.
    
    Profile: Smooth bell curve centered at bubble, ensuring gradual falloff.
    """
    
    def __init__(
        self,
        cylinder_radius: float = 10.0,
        cylinder_length: float = 100.0,
        max_bulge_amplitude: float = 0.6,
        bulge_width: float = 3.0,
        visual_bubble_radius: float = None
    ):
        """
        Initialize deformer.
        
        Args:
            cylinder_radius: Base radius of cylinder
            cylinder_length: Total cylinder height (Y-axis)
            max_bulge_amplitude: Maximum radial expansion (0.6 = 60% larger)
            bulge_width: Width of bulge as multiple of bubble radius
            visual_bubble_radius: Unused, kept for API compatibility
        """
        self.cylinder_radius = cylinder_radius
        self.cylinder_length = cylinder_length
        self.max_amplitude = max_bulge_amplitude
        self.bulge_width = bulge_width
        
        carb.log_info(
            f"[POCDeformer] amp={max_bulge_amplitude:.2f}, width={bulge_width:.1f}x"
        )
    
    def calculate_displacement(
        self,
        vertex_y: float,
        bubble_y: float,
        bubble_radius: float
    ) -> float:
        """
        Calculate radial displacement using smooth Gaussian curve.
        
        Args:
            vertex_y: Y position of the vertex (height)
            bubble_y: Current Y position of bubble center
            bubble_radius: Radius of the bubble
            
        Returns:
            Displacement as fraction (0 to max_amplitude)
        """
        # Gaussian sigma controls the width of the bell curve
        sigma = bubble_radius * self.bulge_width
        
        # Distance from vertex to bubble center
        dist = vertex_y - bubble_y
        
        # Gaussian bell curve: e^(-x²/2σ²)
        gaussian = math.exp(-(dist * dist) / (2.0 * sigma * sigma))
        
        return self.max_amplitude * gaussian
