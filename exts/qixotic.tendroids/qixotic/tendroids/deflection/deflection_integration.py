"""
Deflection Integration - Bridge between DeflectionController and animation system

TEND-86: Integrate DeflectionController with existing animation system

Provides the integration layer that connects the deflection system
to the existing creature controller and tendroid wrappers.
"""

import carb
from typing import Dict, List, Optional, Tuple

from ..deflection import (
    DeflectionController,
    DeflectionConfig,
    TendroidGeometry,
    TendroidDeflectionState,
    get_deflection_config,
)


class DeflectionIntegration:
    """
    Integration layer between DeflectionController and animation system.
    
    Handles:
    - Automatic tendroid registration from wrappers
    - Creature position/velocity extraction
    - Deflection state application to deformers
    
    Usage:
        integration = DeflectionIntegration()
        integration.register_tendroids(tendroid_wrappers)
        
        # In animation loop:
        integration.update(creature_controller, dt)
        deflection_states = integration.get_deflection_states()
    """
    
    def __init__(self, config: Optional[DeflectionConfig] = None):
        """
        Initialize deflection integration.
        
        Args:
            config: Deflection configuration (uses default if None)
        """
        self.config = config or get_deflection_config()
        self._controller = DeflectionController(self.config)
        self._tendroid_map: Dict[str, int] = {}  # name -> id mapping
        self._enabled = True
        
        carb.log_info("[DeflectionIntegration] Initialized")
    
    @property
    def enabled(self) -> bool:
        """Check if deflection system is enabled."""
        return self._enabled and self._controller.enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        """Enable or disable deflection system."""
        self._enabled = value
        self._controller.enabled = value
        carb.log_info(f"[DeflectionIntegration] {'Enabled' if value else 'Disabled'}")
    
    def register_tendroid(
        self,
        tendroid_id: int,
        name: str,
        position: Tuple[float, float, float],
        height: float,
        radius: float
    ) -> None:
        """
        Register a single tendroid for deflection tracking.
        
        Args:
            tendroid_id: Unique integer ID
            name: Tendroid name for lookup
            position: (x, y, z) world position
            height: Tendroid cylinder height
            radius: Tendroid cylinder radius
        """
        geometry = TendroidGeometry(
            center_x=position[0],
            center_z=position[2],
            base_y=position[1],
            height=height,
            radius=radius
        )
        
        self._controller.register_tendroid(tendroid_id, geometry)
        self._tendroid_map[name] = tendroid_id
    
    def register_tendroids(self, tendroid_wrappers: List) -> None:
        """
        Register multiple tendroids from wrapper objects.
        
        Extracts geometry from V2TendroidWrapper instances.
        
        Args:
            tendroid_wrappers: List of V2TendroidWrapper objects
        """
        for idx, wrapper in enumerate(tendroid_wrappers):
            self.register_tendroid(
                tendroid_id=idx,
                name=wrapper.name,
                position=wrapper.position,
                height=wrapper.length,
                radius=wrapper.radius
            )
        
        carb.log_info(
            f"[DeflectionIntegration] Registered {len(tendroid_wrappers)} tendroids"
        )
    
    def unregister_tendroid(self, name: str) -> None:
        """Remove a tendroid from tracking."""
        if name in self._tendroid_map:
            tendroid_id = self._tendroid_map.pop(name)
            self._controller.unregister_tendroid(tendroid_id)
    
    def update(
        self,
        creature_controller,
        dt: float
    ) -> Dict[str, TendroidDeflectionState]:
        """
        Update deflection system from creature controller.
        
        Extracts position and velocity from creature, updates all
        tendroid deflections, and returns states keyed by name.
        
        Args:
            creature_controller: CreatureController instance
            dt: Delta time in seconds
            
        Returns:
            Dict mapping tendroid name to deflection state
        """
        if not self._enabled or creature_controller is None:
            return {}
        
        # Extract creature position and velocity
        creature_pos = creature_controller.get_position()
        creature_vel = self._get_creature_velocity(creature_controller)
        
        # Update controller
        self._controller.update(creature_pos, creature_vel, dt)
        
        # Build name-keyed result
        result = {}
        for name, tendroid_id in self._tendroid_map.items():
            state = self._controller.get_state(tendroid_id)
            if state:
                result[name] = state
        
        return result
    
    def _get_creature_velocity(self, creature_controller) -> Tuple[float, float, float]:
        """Extract velocity from creature controller."""
        if hasattr(creature_controller, 'velocity'):
            vel = creature_controller.velocity
            return (float(vel[0]), float(vel[1]), float(vel[2]))
        return (0.0, 0.0, 0.0)
    
    def get_deflection_states(self) -> Dict[str, TendroidDeflectionState]:
        """Get all current deflection states keyed by name."""
        result = {}
        for name, tendroid_id in self._tendroid_map.items():
            state = self._controller.get_state(tendroid_id)
            if state:
                result[name] = state
        
        return result
    
    def get_deflecting_tendroids(self) -> List[str]:
        """Get names of tendroids currently deflecting."""
        deflecting_ids = self._controller.get_deflecting_tendroids()
        id_to_name = {v: k for k, v in self._tendroid_map.items()}
        return [id_to_name[tid] for tid in deflecting_ids if tid in id_to_name]
    
    def get_state_by_name(self, name: str) -> Optional[TendroidDeflectionState]:
        """Get deflection state for a specific tendroid by name."""
        if name not in self._tendroid_map:
            return None
        return self._controller.get_state(self._tendroid_map[name])
    
    def get_debug_info(self) -> Dict:
        """Get debugging information."""
        return {
            'enabled': self._enabled,
            'tendroid_count': len(self._tendroid_map),
            'deflecting': self.get_deflecting_tendroids(),
            'controller_info': self._controller.get_debug_info(),
        }
    
    def destroy(self) -> None:
        """Cleanup resources."""
        self._tendroid_map.clear()
        carb.log_info("[DeflectionIntegration] Destroyed")
