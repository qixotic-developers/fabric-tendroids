"""
V2 Tendroid Factory - Multi-spawn with interference checking

Creates batches of V2 tendroids with randomized positions and proper spacing.
"""

import carb
import math
import random

from ..builders import V2TendroidBuilder
from ..config import get_config_value


class V2TendroidFactory:
    """
    Factory for creating V2 Tendroids with randomized positions.
    
    Provides batch creation with interference checking to prevent overlaps.
    """
    
    @staticmethod
    def create_batch(
        stage,
        count: int = None,
        parent_path: str = "/World/Tendroids",
        spawn_area: tuple = None,
        radius_range: tuple = None,
        radial_segments: int = 24,
        height_segments: int = 48,
        max_attempts: int = None,
        get_height_fn = None
    ) -> list:
        """
        Create multiple tendroids with randomized positions and sizes.
        
        Uses 8:1 aspect ratio (±0.5 variation) and interference checking.
        
        Args:
            stage: USD stage
            count: Number of tendroids to create
            parent_path: Parent prim path
            spawn_area: (width, depth) of spawning area
            radius_range: (min, max) radius for variation
            radial_segments: Circumference resolution
            height_segments: Vertical resolution
            max_attempts: Max position attempts per tendroid
            get_height_fn: Terrain height query function
        
        Returns:
            List of tendroid data dicts from V2TendroidBuilder
        """
        # Load config defaults
        if count is None:
            count = get_config_value("tendroid_spawning", "default_count", default=15)
        if spawn_area is None:
            spawn_area = tuple(get_config_value(
                "tendroid_spawning", "spawn_area", default=[200.0, 200.0]
            ))
        if radius_range is None:
            radius_range = tuple(get_config_value(
                "tendroid_spawning", "radius_range", default=[8.0, 12.0]
            ))
        if max_attempts is None:
            max_attempts = get_config_value(
                "tendroid_spawning", "max_placement_attempts", default=200
            )
        
        # Load additional config
        flare_mult = get_config_value(
            "tendroid_geometry", "flare_radius_multiplier", default=2.0
        )
        aspect_range = get_config_value(
            "tendroid_spawning", "aspect_ratio_range", default=[7.5, 8.5]
        )
        spacing_mult = get_config_value(
            "tendroid_spawning", "spacing_multiplier", default=1.2
        )
        
        tendroids = []
        positions = []  # (x, z, base_radius) for interference checking
        width, depth = spawn_area
        
        # Use uniform radius for GPU batching optimization
        uniform_radius = (radius_range[0] + radius_range[1]) / 2.0
        
        for i in range(count):
            radius = uniform_radius
            base_radius = radius * flare_mult
            
            # Find valid position
            position_found = False
            x, z = 0.0, 0.0
            
            for attempt in range(max_attempts):
                x = random.uniform(-width / 2, width / 2)
                z = random.uniform(-depth / 2, depth / 2)
                
                if V2TendroidFactory._check_interference(
                    x, z, base_radius, positions, spacing_mult
                ):
                    position_found = True
                    positions.append((x, z, base_radius))
                    break
            
            if not position_found:
                carb.log_warn(
                    f"[V2TendroidFactory] Could not place tendroid {i} "
                    f"after {max_attempts} attempts (have {len(positions)} placed, "
                    f"spawn_area={width}x{depth}, spacing={spacing_mult})"
                )
                continue
            
            # Calculate length with aspect ratio variation
            aspect_ratio = random.uniform(aspect_range[0], aspect_range[1])
            length = radius * 2.0 * aspect_ratio
            
            # Create tendroid
            tendroid_data = V2TendroidBuilder.create_tendroid(
                stage=stage,
                name=f"Tendroid_{i:02d}",
                position=(x, 0, z),
                radius=radius,
                length=length,
                radial_segments=radial_segments,
                height_segments=height_segments,
                parent_path=parent_path,
                get_height_fn=get_height_fn
            )
            
            if tendroid_data:
                tendroids.append(tendroid_data)
            else:
                positions.pop()  # Remove failed position
                carb.log_warn(f"[V2TendroidFactory] Failed to create tendroid {i}")
        
        carb.log_info(
            f"[V2TendroidFactory] Created {len(tendroids)}/{count} tendroids"
        )
        return tendroids
    
    @staticmethod
    def _check_interference(
        x: float,
        z: float,
        base_radius: float,
        existing_positions: list,
        spacing_multiplier: float
    ) -> bool:
        """
        Check if position interferes with existing tendroids.
        
        Args:
            x, z: Position to check
            base_radius: Flared base radius
            existing_positions: List of (x, z, base_radius)
            spacing_multiplier: Extra spacing factor
        
        Returns:
            True if position is valid (no interference)
        """
        for ex, ez, existing_radius in existing_positions:
            dx = x - ex
            dz = z - ez
            distance = math.sqrt(dx * dx + dz * dz)
            min_separation = spacing_multiplier * (base_radius + existing_radius)
            
            if distance < min_separation:
                return False
        
        return True
