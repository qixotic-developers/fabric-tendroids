"""
Deflection Module - Tendroid bending/deflection behavior

TEND-3: Tendroid Deflection System

This module implements tendroid deflection in response to creature proximity.
Supports three approach types:
- Vertical (pass-over): Y-axis aware, deflection proportional to height
- Head-on: Direct approach, deflection inversely proportional to distance
- Pass-by: Detection circle triggers deflection for lateral movement

Usage:
    from qixotic.tendroids.deflection import (
        DeflectionController,
        DeflectionConfig,
        TendroidGeometry
    )
    
    config = DeflectionConfig()
    controller = DeflectionController(config)
    
    # Register tendroids
    controller.register_tendroid(0, TendroidGeometry(
        center_x=0.0, center_z=0.0,
        base_y=0.0, height=1.0, radius=0.05
    ))
    
    # Update each frame
    states = controller.update(creature_pos, creature_vel, dt)
"""

from .deflection_config import (
    ApproachType,
    DeflectionLimits,
    DetectionZones,
    DeflectionConfig,
    DEFLECTION_PRESETS,
    get_deflection_config,
)

from .approach_calculators import (
    TendroidGeometry,
    ApproachResult,
    calculate_vertical_proximity,
    calculate_head_on_approach,
    calculate_pass_by_approach,
    detect_approach_type,
)

from .deflection_helpers import (
    DeflectionResult,
    calculate_height_ratio,
    lerp_deflection,
    calculate_proportional_deflection,
    calculate_cylinder_normal,
    calculate_deflection_direction,
    calculate_bend_axis,
    calculate_deflection,
    smooth_deflection_transition,
)

from .deflection_controller import (
    TendroidDeflectionState,
    DeflectionController,
)

from .deflection_integration import (
    DeflectionIntegration,
)

try:
    from .batch_deflection_manager import (
        BatchDeflectionState,
        BatchDeflectionManager,
    )
except ImportError:
    BatchDeflectionState = None
    BatchDeflectionManager = None

try:
    from .wrapper_deflection import (
        DeflectionTransform,
        TendroidDeflectionMixin,
        create_deflectable_tendroid_class,
        apply_deflection_to_wrapper,
        get_deflection_from_wrapper,
    )
except ImportError:
    DeflectionTransform = None
    TendroidDeflectionMixin = None
    create_deflectable_tendroid_class = None
    apply_deflection_to_wrapper = None
    get_deflection_from_wrapper = None


__all__ = [
    # Config
    'ApproachType',
    'DeflectionLimits',
    'DetectionZones',
    'DeflectionConfig',
    'DEFLECTION_PRESETS',
    'get_deflection_config',
    
    # Approach calculators
    'TendroidGeometry',
    'ApproachResult',
    'calculate_vertical_proximity',
    'calculate_head_on_approach',
    'calculate_pass_by_approach',
    'detect_approach_type',
    
    # Deflection helpers
    'DeflectionResult',
    'calculate_height_ratio',
    'lerp_deflection',
    'calculate_proportional_deflection',
    'calculate_cylinder_normal',
    'calculate_deflection_direction',
    'calculate_bend_axis',
    'calculate_deflection',
    'smooth_deflection_transition',
    
    # Controller
    'TendroidDeflectionState',
    'DeflectionController',
    
    # Integration
    'DeflectionIntegration',
    
    # Batch GPU processing
    'BatchDeflectionState',
    'BatchDeflectionManager',
    
    # Wrapper utilities
    'DeflectionTransform',
    'TendroidDeflectionMixin',
    'create_deflectable_tendroid_class',
    'apply_deflection_to_wrapper',
    'get_deflection_from_wrapper',
]
