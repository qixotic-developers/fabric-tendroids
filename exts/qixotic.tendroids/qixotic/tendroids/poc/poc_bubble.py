"""
POC Bubble - Simple rising bubble that drives deformation

A bubble that rises at constant speed and provides its position
to the deformer. Height is along Y-axis (Omniverse convention).
"""

import carb


class POCBubble:
    """
    Simple bubble that rises through the cylinder.
    
    The bubble's Y position drives the deformation bulge location.
    """
    
    def __init__(
        self,
        start_y: float = 0.0,
        radius: float = 5.0,
        rise_speed: float = 20.0,
        cylinder_length: float = 100.0,
        exit_distance: float = None
    ):
        """
        Initialize bubble.
        
        Args:
            start_y: Starting Y position (base of cylinder)
            radius: Bubble radius
            rise_speed: Units per second rise rate
            cylinder_length: Height at which bubble exits
            exit_distance: How far past cylinder top before reset (default: 3x radius)
        """
        self.y = start_y
        self.radius = radius
        self.rise_speed = rise_speed
        self.cylinder_length = cylinder_length
        self.exit_distance = exit_distance if exit_distance else radius * 3.0
        self.active = True
        
        carb.log_info(
            f"[POCBubble] Created: r={radius:.1f}, speed={rise_speed:.1f}, "
            f"exit_dist={self.exit_distance:.1f}"
        )
    
    def update(self, dt: float) -> bool:
        """
        Update bubble position.
        
        Args:
            dt: Delta time in seconds
            
        Returns:
            True if bubble still active, False if exited cylinder
        """
        if not self.active:
            return False
        
        # Rise at constant speed along Y
        self.y += self.rise_speed * dt
        
        # Check if bubble has traveled far enough past cylinder top
        # for deformation to fully dissipate
        if self.y > self.cylinder_length + self.exit_distance:
            self.active = False
            carb.log_info(f"[POCBubble] Exited at y={self.y:.1f}")
            return False
        
        return True
    
    def get_position_normalized(self) -> float:
        """
        Get bubble position as 0-1 normalized along cylinder length.
        
        Returns:
            0.0 at base, 1.0 at mouth, can exceed 1.0 after exit
        """
        return self.y / self.cylinder_length
    
    def reset(self):
        """Reset bubble to starting position."""
        self.y = self.radius  # Start with bubble center at radius height
        self.active = True
        carb.log_info(f"[POCBubble] Reset to y={self.y:.1f}")
