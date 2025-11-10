"""
Environment configuration for Sky, Lighting, and Materials

Stores default settings for scene environment elements.
"""

from dataclasses import dataclass
from typing import Tuple
from pxr import Gf


@dataclass
class SkyConfig:
    """Sky dome configuration."""
    path: str = "/Environment/Sky"
    translate_y: float = 325.0
    rotate_y: float = -90.0
    rotate_z: float = -90.0
    intensity: float = 0.4


@dataclass
class DistantLightConfig:
    """Distant light configuration."""
    path: str = "/Environment/DistantLight"
    translate_x: float = -275.0
    translate_y: float = 550.0
    rotate_y: float = -75.0
    rotate_z: float = -50.0
    angle: float = 2.0
    intensity: float = 1.0
    exposure: float = 10.0
    color: Tuple[float, float, float] = (1.0, 1.0, 1.0)  # White


@dataclass
class SeaFloorMaterialConfig:
    """Sea floor material configuration."""
    path: str = "/World/Looks/Sand"
    use_existing: bool = True  # Use existing material if available
    
    # Fallback settings if material doesn't exist
    diffuse_color: Tuple[float, float, float] = (0.76, 0.70, 0.50)  # Sandy brown
    roughness: float = 0.9
    metallic: float = 0.0


@dataclass
class EnvironmentConfig:
    """Complete environment configuration."""
    sky: SkyConfig = None
    distant_light: DistantLightConfig = None
    sea_floor_material: SeaFloorMaterialConfig = None
    
    def __post_init__(self):
        """Initialize sub-configs if not provided."""
        if self.sky is None:
            self.sky = SkyConfig()
        if self.distant_light is None:
            self.distant_light = DistantLightConfig()
        if self.sea_floor_material is None:
            self.sea_floor_material = SeaFloorMaterialConfig()
