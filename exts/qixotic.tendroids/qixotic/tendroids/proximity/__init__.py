"""
Proximity Detection Module

GPU-accelerated spatial hashing for creature-tendroid proximity detection.
Uses Nvidia Warp HashGrid for O(1) neighbor queries.

TEND-15: Set up Warp Hash Grid infrastructure
TEND-16: Implement proximity kernel for single tendroid
TEND-17: Define approach_epsilon and approach_minimum parameters
TEND-18: Create proximity state manager
TEND-2: Proximity Detection System (Epic)
"""

from .proximity_config import (
    # Grid configuration
    GridConfig,
    SCENE_PRESETS,
    DEFAULT_GRID_CONFIG,
    get_grid_config,
    
    # Approach parameters (TEND-17)
    ApproachParameters,
    ProximityConfig,  # Alias for backwards compatibility
    APPROACH_PRESETS,
    DEFAULT_APPROACH_PARAMS,
    DEFAULT_PROXIMITY_CONFIG,
    get_approach_params,
    get_proximity_config,
    create_custom_approach_params,
    
    # Units enum
    DistanceUnit,
)

from .hash_grid import (
    ProximityHashGrid,
    PointSet,
)

from .hash_grid_helper import (
    combine_position_arrays,
    update_positions_from_list,
    copy_positions_kernel,
    find_neighbors_kernel,
    compute_distances_kernel,
    compute_closest_distances_kernel,
)

# TEND-16: Single tendroid proximity kernel
from .proximity_kernel import (
    SingleTendroidProximity,
    ProximityResult,
)

from .proximity_kernel_helper import (
    proximity_check_kernel,
    horizontal_distance_kernel,
    compute_repulsion_force_kernel,
    compute_zone_based_force_kernel,
)

# TEND-18: Proximity state manager
from .proximity_state import (
    ProximityState,
    VALID_TRANSITIONS,
    is_valid_transition,
    get_zone_for_state,
    get_state_priority,
)

from .state_transitions import (
    determine_next_state,
    get_transition_description,
)

from .state_manager import (
    ProximityStateManager,
    StateChangeEvent,
    TrackedEntity,
    StateCallback,
)

__all__ = [
    # Grid Configuration
    "GridConfig",
    "SCENE_PRESETS",
    "DEFAULT_GRID_CONFIG",
    "get_grid_config",
    
    # Approach Parameters (TEND-17)
    "ApproachParameters",
    "ProximityConfig",
    "APPROACH_PRESETS",
    "DEFAULT_APPROACH_PARAMS",
    "DEFAULT_PROXIMITY_CONFIG",
    "get_approach_params",
    "get_proximity_config",
    "create_custom_approach_params",
    "DistanceUnit",
    
    # Hash Grid
    "ProximityHashGrid",
    "PointSet",
    
    # Helper functions
    "combine_position_arrays",
    "update_positions_from_list",
    
    # Hash Grid Kernels
    "copy_positions_kernel",
    "find_neighbors_kernel",
    "compute_distances_kernel",
    "compute_closest_distances_kernel",
    
    # TEND-16: Single Tendroid Proximity
    "SingleTendroidProximity",
    "ProximityResult",
    
    # TEND-16: Proximity Kernels
    "proximity_check_kernel",
    "horizontal_distance_kernel",
    "compute_repulsion_force_kernel",
    "compute_zone_based_force_kernel",
    
    # TEND-18: Proximity State
    "ProximityState",
    "VALID_TRANSITIONS",
    "is_valid_transition",
    "get_zone_for_state",
    "get_state_priority",
    
    # TEND-18: State Transitions
    "determine_next_state",
    "get_transition_description",
    
    # TEND-18: State Manager
    "ProximityStateManager",
    "StateChangeEvent",
    "TrackedEntity",
    "StateCallback",
]
