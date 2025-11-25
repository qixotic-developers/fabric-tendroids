"""
V2 Environment - Sea floor, sky, and lighting setup
"""

from .sea_floor_config import SeaFloorConfig
from .sea_floor_controller import SeaFloorController
from .sea_floor_helper import initialize_height_map, get_height_at
from .environment_config import (
    EnvironmentConfig,
    SkyConfig,
    DistantLightConfig,
    SeaFloorMaterialConfig,
)
from .environment_setup import EnvironmentSetup

__all__ = [
    # Sea floor
    "SeaFloorConfig",
    "SeaFloorController",
    "initialize_height_map",
    "get_height_at",
    # Environment
    "EnvironmentConfig",
    "SkyConfig",
    "DistantLightConfig",
    "SeaFloorMaterialConfig",
    "EnvironmentSetup",
]
