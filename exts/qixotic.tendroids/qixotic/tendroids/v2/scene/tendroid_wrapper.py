"""
V2 Tendroid Wrapper - Lightweight wrapper for tendroid mesh with Warp deformer

Provides unified interface for wave displacement and bubble deformation.
"""


class V2TendroidWrapper:
    """
    Lightweight wrapper for V2 tendroid with Warp deformer.

    Wave displacement and bubble deformation are combined in a single GPU pass.
    The bubble manager passes wave displacement to apply_deformation().
    """

    def __init__(
        self,
        name: str,
        position: tuple,
        radius: float,
        length: float,
        mesh_prim,
        deformer,
        deform_start_height: float,
        flare_height: float = 0.0
    ):
        self.name = name
        self.position = position
        self.radius = radius
        self.length = length
        self.mesh_prim = mesh_prim
        self.deformer = deformer
        self.deform_start_height = deform_start_height
        self.flare_height = flare_height
        self.points_attr = mesh_prim.GetPointsAttr() if mesh_prim else None
        
        # Track if bubble is currently active (for wave-only mode)
        self._bubble_active = False
        
        # Cache last wave displacement for wave-only updates
        self._last_wave_dx = 0.0
        self._last_wave_dz = 0.0

    def apply_deformation(
        self, 
        bubble_y: float, 
        bubble_radius: float,
        wave_dx: float = 0.0,
        wave_dz: float = 0.0
    ):
        """
        Apply bubble-guided deformation with wave displacement.
        
        Both wave and deformation are combined in a single GPU pass.
        
        Args:
            bubble_y: Bubble center Y position (local coords)
            bubble_radius: Current bubble radius
            wave_dx: Wave displacement in X direction
            wave_dz: Wave displacement in Z direction
        """
        if not self.deformer or not self.points_attr:
            return

        self._bubble_active = True
        self._last_wave_dx = wave_dx
        self._last_wave_dz = wave_dz

        new_points = self.deformer.deform(
            bubble_y, 
            bubble_radius,
            wave_dx,
            wave_dz
        )
        if new_points is not None:
            self.points_attr.Set(new_points)

    def apply_wave_only(self, wave_dx: float, wave_dz: float):
        """
        Apply wave displacement only (no bubble deformation).
        
        Used when tendroid has no active bubble.
        """
        if not self.deformer or not self.points_attr:
            return

        self._bubble_active = False
        self._last_wave_dx = wave_dx
        self._last_wave_dz = wave_dz

        new_points = self.deformer.deform_wave_only(wave_dx, wave_dz)
        if new_points is not None:
            self.points_attr.Set(new_points)

    def reset_deformation(self, wave_dx: float = 0.0, wave_dz: float = 0.0):
        """
        Reset to cylinder shape with optional wave displacement.
        
        Called when bubble exits to smoothly return to base shape.
        """
        if not self.deformer or not self.points_attr:
            return
        
        self._bubble_active = False
        
        # Deform at cylinder radius = no bulge
        new_points = self.deformer.deform(
            bubble_y=0.0,
            bubble_radius=self.radius,
            wave_dx=wave_dx,
            wave_dz=wave_dz
        )
        if new_points is not None:
            self.points_attr.Set(new_points)

    def get_spawn_height(self, spawn_pct: float = 0.10) -> float:
        """
        Get bubble spawn Y position accounting for flared base.
        
        The spawn position should be above the flared foot, not inside it.
        
        Args:
            spawn_pct: Fraction of cylinder length for spawn position
            
        Returns:
            Y position in local coordinates
        """
        # Start above the flare, then add percentage of remaining length
        cylinder_start = self.flare_height
        usable_length = self.length - self.flare_height
        return cylinder_start + (usable_length * spawn_pct)

    def get_top_position(self) -> tuple:
        """Get world position of tendroid top (mouth)."""
        return (
            self.position[0],
            self.position[1] + self.length,
            self.position[2]
        )

    @property
    def is_bubble_active(self) -> bool:
        """Check if bubble is currently driving deformation."""
        return self._bubble_active
