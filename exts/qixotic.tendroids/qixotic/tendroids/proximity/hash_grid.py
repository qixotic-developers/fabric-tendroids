"""
Warp Hash Grid Controller

GPU-accelerated spatial hashing for O(1) proximity queries.
Manages grid lifecycle, position updates, and neighbor searches.

TEND-15: Set up Warp Hash Grid infrastructure
TEND-64: Initialize Warp HashGrid with scene dimensions
TEND-65: Create Warp arrays for position data
"""

import carb
import warp as wp
from typing import Optional, List, Tuple
from dataclasses import dataclass

from .proximity_config import GridConfig, DEFAULT_GRID_CONFIG

# Initialize Warp (safe to call multiple times)
wp.init()


@dataclass
class PointSet:
    """Collection of points registered in the hash grid."""
    name: str
    positions_gpu: wp.array
    count: int
    
    def update_positions(self, positions: List[Tuple[float, float, float]]):
        """Update positions from CPU list."""
        if len(positions) != self.count:
            raise ValueError(f"Position count mismatch: {len(positions)} != {self.count}")
        self.positions_gpu = wp.array(positions, dtype=wp.vec3, device=self.positions_gpu.device)


class ProximityHashGrid:
    """
    Warp Hash Grid wrapper for creature-tendroid proximity detection.
    
    Provides GPU-accelerated spatial hashing with O(1) neighbor queries.
    Manages separate point sets for creatures and tendroids.
    
    Usage:
        grid = ProximityHashGrid()
        grid.initialize()
        
        # Register objects
        grid.register_creatures(creature_positions)
        grid.register_tendroids(tendroid_positions)
        
        # Each frame
        grid.update_creatures(new_positions)
        grid.rebuild()
        
        # Query neighbors
        neighbors = grid.query_neighbors(query_point, radius)
    """
    
    def __init__(self, config: Optional[GridConfig] = None):
        """
        Initialize hash grid controller.
        
        Args:
            config: Grid configuration (uses defaults if None)
        """
        self.config = config or DEFAULT_GRID_CONFIG
        self._grid: Optional[wp.HashGrid] = None
        self._initialized = False
        
        # Point sets
        self._creatures: Optional[PointSet] = None
        self._tendroids: Optional[PointSet] = None
        
        # Combined positions for grid building
        self._all_positions_gpu: Optional[wp.array] = None
        self._total_points = 0
        
        # Index offsets for identifying point types
        self._creature_start = 0
        self._tendroid_start = 0
    
    @property
    def is_initialized(self) -> bool:
        """Check if grid is ready for use."""
        return self._initialized and self._grid is not None
    
    def initialize(self) -> bool:
        """
        Initialize the Warp HashGrid.
        
        TEND-64: Initialize Warp HashGrid with scene dimensions
        
        Returns:
            True if initialization successful
        """
        try:
            self._grid = wp.HashGrid(
                dim_x=self.config.dim_x,
                dim_y=self.config.dim_y,
                dim_z=self.config.dim_z,
                device=self.config.device
            )
            self._initialized = True
            carb.log_info(
                f"[ProximityHashGrid] Initialized {self.config.dim_x}x"
                f"{self.config.dim_y}x{self.config.dim_z} grid on {self.config.device}"
            )
            return True
        except Exception as e:
            carb.log_error(f"[ProximityHashGrid] Initialization failed: {e}")
            self._initialized = False
            return False
    
    def register_creatures(self, positions: List[Tuple[float, float, float]]) -> bool:
        """
        Register creature positions with the grid.
        
        TEND-65: Create Warp arrays for position data
        
        Args:
            positions: List of (x, y, z) creature positions
            
        Returns:
            True if registration successful
        """
        if not positions:
            carb.log_warn("[ProximityHashGrid] No creature positions to register")
            return False
        
        try:
            positions_gpu = wp.array(positions, dtype=wp.vec3, device=self.config.device)
            self._creatures = PointSet(
                name="creatures",
                positions_gpu=positions_gpu,
                count=len(positions)
            )
            self._rebuild_combined_array()
            carb.log_info(f"[ProximityHashGrid] Registered {len(positions)} creatures")
            return True
        except Exception as e:
            carb.log_error(f"[ProximityHashGrid] Creature registration failed: {e}")
            return False
    
    def register_tendroids(self, positions: List[Tuple[float, float, float]]) -> bool:
        """
        Register tendroid positions with the grid.
        
        Args:
            positions: List of (x, y, z) tendroid center positions
            
        Returns:
            True if registration successful
        """
        if not positions:
            carb.log_warn("[ProximityHashGrid] No tendroid positions to register")
            return False
        
        try:
            positions_gpu = wp.array(positions, dtype=wp.vec3, device=self.config.device)
            self._tendroids = PointSet(
                name="tendroids",
                positions_gpu=positions_gpu,
                count=len(positions)
            )
            self._rebuild_combined_array()
            carb.log_info(f"[ProximityHashGrid] Registered {len(positions)} tendroids")
            return True
        except Exception as e:
            carb.log_error(f"[ProximityHashGrid] Tendroid registration failed: {e}")
            return False
    
    def update_creatures(self, positions: List[Tuple[float, float, float]]) -> bool:
        """
        Update creature positions (called each frame).
        
        TEND-66: Implement grid rebuild on position updates
        
        Args:
            positions: New creature positions
            
        Returns:
            True if update successful
        """
        if self._creatures is None:
            return self.register_creatures(positions)
        
        if len(positions) != self._creatures.count:
            # Count changed - re-register
            return self.register_creatures(positions)
        
        try:
            self._creatures.positions_gpu = wp.array(
                positions, dtype=wp.vec3, device=self.config.device
            )
            return True
        except Exception as e:
            carb.log_error(f"[ProximityHashGrid] Creature update failed: {e}")
            return False
    
    def update_tendroids(self, positions: List[Tuple[float, float, float]]) -> bool:
        """
        Update tendroid positions (called when tendroids move).
        
        Args:
            positions: New tendroid positions
            
        Returns:
            True if update successful
        """
        if self._tendroids is None:
            return self.register_tendroids(positions)
        
        if len(positions) != self._tendroids.count:
            return self.register_tendroids(positions)
        
        try:
            self._tendroids.positions_gpu = wp.array(
                positions, dtype=wp.vec3, device=self.config.device
            )
            return True
        except Exception as e:
            carb.log_error(f"[ProximityHashGrid] Tendroid update failed: {e}")
            return False
    
    def _rebuild_combined_array(self):
        """Rebuild combined position array from creatures and tendroids."""
        from .hash_grid_helper import combine_position_arrays
        
        creatures_gpu = self._creatures.positions_gpu if self._creatures else None
        tendroids_gpu = self._tendroids.positions_gpu if self._tendroids else None
        
        self._all_positions_gpu, self._creature_start, self._tendroid_start = \
            combine_position_arrays(creatures_gpu, tendroids_gpu, self.config.device)
        
        creature_count = self._creatures.count if self._creatures else 0
        tendroid_count = self._tendroids.count if self._tendroids else 0
        self._total_points = creature_count + tendroid_count
    
    def rebuild(self, search_radius: float = 1.0) -> bool:
        """
        Rebuild hash grid with current positions.
        
        TEND-66: Implement grid rebuild on position updates
        TEND-67: Integrate HashGrid with simulation loop
        
        Must be called after position updates before queries.
        
        Args:
            search_radius: Radius for neighbor searches
            
        Returns:
            True if rebuild successful
        """
        if not self.is_initialized:
            carb.log_error("[ProximityHashGrid] Grid not initialized")
            return False
        
        if self._all_positions_gpu is None or self._total_points == 0:
            self._rebuild_combined_array()
        
        if self._all_positions_gpu is None:
            carb.log_warn("[ProximityHashGrid] No positions to build grid")
            return False
        
        try:
            self._grid.build(
                points=self._all_positions_gpu,
                radius=search_radius
            )
            return True
        except Exception as e:
            carb.log_error(f"[ProximityHashGrid] Grid rebuild failed: {e}")
            return False
    
    def get_grid_id(self) -> Optional[wp.uint64]:
        """Get hash grid ID for kernel use."""
        if self._grid is None:
            return None
        return self._grid.id
    
    def get_creature_count(self) -> int:
        """Get number of registered creatures."""
        return self._creatures.count if self._creatures else 0
    
    def get_tendroid_count(self) -> int:
        """Get number of registered tendroids."""
        return self._tendroids.count if self._tendroids else 0
    
    def is_creature_index(self, idx: int) -> bool:
        """Check if index refers to a creature."""
        creature_end = self._creature_start + self.get_creature_count()
        return self._creature_start <= idx < creature_end
    
    def is_tendroid_index(self, idx: int) -> bool:
        """Check if index refers to a tendroid."""
        tendroid_end = self._tendroid_start + self.get_tendroid_count()
        return self._tendroid_start <= idx < tendroid_end
    
    def destroy(self):
        """Release GPU resources."""
        self._grid = None
        self._creatures = None
        self._tendroids = None
        self._all_positions_gpu = None
        self._initialized = False
        self._total_points = 0
        carb.log_info("[ProximityHashGrid] Destroyed")
