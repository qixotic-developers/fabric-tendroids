"""
Wrapper Deflection - Deflection utilities for TendroidWrapper

TEND-87: Create TendroidWrapper deflection integration

Provides mixin and utility functions to add deflection capabilities
to existing V2TendroidWrapper instances.
"""

import math
from dataclasses import dataclass
from typing import Tuple, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .deflection_controller import TendroidDeflectionState


@dataclass
class DeflectionTransform:
    """
    Transform data for applying deflection to a tendroid mesh.
    
    Attributes:
        bend_angle: Deflection angle in radians
        bend_axis: (x, y, z) rotation axis
        pivot_y: Y position of bend pivot point (usually base)
    """
    bend_angle: float = 0.0
    bend_axis: Tuple[float, float, float] = (1.0, 0.0, 0.0)
    pivot_y: float = 0.0
    
    @property
    def is_deflecting(self) -> bool:
        """Check if deflection is active."""
        return abs(self.bend_angle) > 0.001
    
    def to_euler_degrees(self) -> Tuple[float, float, float]:
        """
        Convert bend to approximate Euler angles in degrees.
        
        Returns:
            (rx, ry, rz) rotation in degrees
        """
        ax, ay, az = self.bend_axis
        angle_deg = math.degrees(self.bend_angle)
        
        # Approximate axis-angle to euler (simplified for small angles)
        return (
            angle_deg * ax,
            angle_deg * ay,
            angle_deg * az
        )


class TendroidDeflectionMixin:
    """
    Mixin class to add deflection capabilities to TendroidWrapper.
    
    Add to existing wrapper class or use create_deflectable_tendroid_class().
    
    Requires base class to have:
        - name: str
        - position: tuple
        - length: float
        - radius: float
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize deflection state."""
        super().__init__(*args, **kwargs)
        self._deflection_transform = DeflectionTransform()
        self._deflection_enabled = True
    
    @property
    def deflection_enabled(self) -> bool:
        """Check if deflection is enabled for this tendroid."""
        return self._deflection_enabled
    
    @deflection_enabled.setter
    def deflection_enabled(self, value: bool):
        """Enable or disable deflection."""
        self._deflection_enabled = value
        if not value:
            self._deflection_transform = DeflectionTransform()
    
    @property
    def deflection_transform(self) -> DeflectionTransform:
        """Get current deflection transform."""
        return self._deflection_transform
    
    @property
    def is_deflecting(self) -> bool:
        """Check if tendroid is currently deflecting."""
        return self._deflection_transform.is_deflecting
    
    def update_deflection(self, state: 'TendroidDeflectionState') -> None:
        """
        Update deflection transform from controller state.
        
        Args:
            state: TendroidDeflectionState from DeflectionController
        """
        if not self._deflection_enabled:
            return
        
        self._deflection_transform = DeflectionTransform(
            bend_angle=state.current_angle,
            bend_axis=state.deflection_axis,
            pivot_y=getattr(self, 'position', (0, 0, 0))[1]
        )
    
    def clear_deflection(self) -> None:
        """Reset deflection to zero."""
        self._deflection_transform = DeflectionTransform()
    
    def get_deflection_info(self) -> dict:
        """Get deflection debugging info."""
        return {
            'enabled': self._deflection_enabled,
            'is_deflecting': self.is_deflecting,
            'angle_deg': math.degrees(self._deflection_transform.bend_angle),
            'axis': self._deflection_transform.bend_axis,
        }


def create_deflectable_tendroid_class(base_class):
    """
    Create a new tendroid class with deflection capabilities.
    
    Args:
        base_class: Base tendroid wrapper class (e.g., V2TendroidWrapper)
        
    Returns:
        New class with TendroidDeflectionMixin
        
    Usage:
        DeflectableTendroid = create_deflectable_tendroid_class(V2TendroidWrapper)
        tendroid = DeflectableTendroid(name="tendroid_0", ...)
    """
    class DeflectableTendroid(TendroidDeflectionMixin, base_class):
        """Tendroid wrapper with deflection capabilities."""
        pass
    
    DeflectableTendroid.__name__ = f"Deflectable{base_class.__name__}"
    return DeflectableTendroid


def apply_deflection_to_wrapper(
    wrapper,
    state: 'TendroidDeflectionState'
) -> DeflectionTransform:
    """
    Apply deflection state to an existing wrapper instance.
    
    For wrappers that don't use the mixin pattern.
    
    Args:
        wrapper: Any tendroid wrapper with position attribute
        state: TendroidDeflectionState from controller
        
    Returns:
        DeflectionTransform to apply to mesh
    """
    if not hasattr(wrapper, '_deflection_transform'):
        wrapper._deflection_transform = DeflectionTransform()
    
    wrapper._deflection_transform = DeflectionTransform(
        bend_angle=state.current_angle,
        bend_axis=state.deflection_axis,
        pivot_y=wrapper.position[1] if hasattr(wrapper, 'position') else 0.0
    )
    
    return wrapper._deflection_transform


def get_deflection_from_wrapper(wrapper) -> Optional[DeflectionTransform]:
    """
    Get deflection transform from a wrapper if available.
    
    Args:
        wrapper: Tendroid wrapper instance
        
    Returns:
        DeflectionTransform or None if no deflection applied
    """
    if hasattr(wrapper, '_deflection_transform'):
        return wrapper._deflection_transform
    return None
