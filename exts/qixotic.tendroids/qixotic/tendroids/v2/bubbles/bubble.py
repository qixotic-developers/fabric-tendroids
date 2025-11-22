"""
V2 Bubble - Rising bubble that drives cylinder deformation

Bubble grows from cylinder diameter (no deformation) to max diameter
(full deformation) over a configurable height range.
"""

import carb


class V2Bubble:
    """
    Rising bubble that drives deformation.
    
    Radius interpolates from cylinder_radius (no bulge) to max_radius
    (full bulge) between starting_diameter_height and max_diameter_height.
    """
    
    def __init__(
        self,
        cylinder_radius: float = 10.0,
        cylinder_length: float = 200.0,
        max_radius: float = 18.0,
        rise_speed: float = 15.0,
        starting_diameter_pct: float = 0.10,
        max_diameter_pct: float = 0.75,
        exit_distance: float = None
    ):
        """
        Args:
            cylinder_radius: Base cylinder radius (bubble starts at this size)
            cylinder_length: Total cylinder height
            max_radius: Maximum bubble radius (full deformation)
            rise_speed: Units per second
            starting_diameter_pct: % of cylinder height where growth starts
            max_diameter_pct: % of cylinder height where growth completes
            exit_distance: Distance past mouth before reset
        """
        self.cylinder_radius = cylinder_radius
        self.cylinder_length = cylinder_length
        self.max_radius = max_radius
        self.rise_speed = rise_speed
        
        # Convert percentages to absolute heights
        self.starting_diameter_height = cylinder_length * starting_diameter_pct
        self.max_diameter_height = cylinder_length * max_diameter_pct
        
        self.exit_distance = exit_distance if exit_distance else max_radius * 2.0
        
        self.y = self.starting_diameter_height
        self.active = True
        
        carb.log_info(
            f"[V2Bubble] cyl_r={cylinder_radius:.1f}, max_r={max_radius:.1f}, "
            f"growth: {self.starting_diameter_height:.0f}-{self.max_diameter_height:.0f}"
        )
    
    def get_current_radius(self) -> float:
        """Get interpolated radius based on Y position."""
        if self.y <= self.starting_diameter_height:
            return self.cylinder_radius
        
        if self.y >= self.max_diameter_height:
            return self.max_radius
        
        zone_length = self.max_diameter_height - self.starting_diameter_height
        progress = (self.y - self.starting_diameter_height) / zone_length
        return self.cylinder_radius + progress * (self.max_radius - self.cylinder_radius)
    
    def update(self, dt: float) -> bool:
        """Update bubble position. Returns False when exited."""
        if not self.active:
            return False
        
        self.y += self.rise_speed * dt
        
        if self.y > self.cylinder_length + self.exit_distance:
            self.active = False
            return False
        
        return True
    
    def reset(self):
        """Reset bubble to starting position."""
        self.y = self.starting_diameter_height
        self.active = True
