"""
Deflection Integration - Bridge between DeflectionController and animation system

TEND-86: Integrate DeflectionController with existing animation system

Provides the integration layer that connects the deflection system
to the existing creature controller and tendroid wrappers.
"""

import carb
from typing import Dict, List, Optional, Tuple

from .deflection_controller import DeflectionController, TendroidDeflectionState
from .deflection_config import DeflectionConfig
from .approach_calculators import TendroidGeometry
from .scene_config import create_scene_unit_config


class DeflectionIntegration:
    """
    Integration layer between DeflectionController and animation system.
    """
    
    def __init__(self, config: Optional[DeflectionConfig] = None):
        """Initialize deflection integration."""
        self._provided_config = config
        self._controller: Optional[DeflectionController] = None
        self._tendroid_map: Dict[str, int] = {}
        self._enabled = True
        self._debug_frame_count = 0
        
        carb.log_info("[DeflectionIntegration] Initialized")
    
    @property
    def enabled(self) -> bool:
        if self._controller is None:
            return False
        return self._enabled and self._controller.enabled
    
    @enabled.setter
    def enabled(self, value: bool):
        self._enabled = value
        if self._controller:
            self._controller.enabled = value
    
    def register_tendroids(
        self,
        tendroid_wrappers: List,
        creature_radius: float = 6.0
    ) -> None:
        """Register multiple tendroids from wrapper objects."""
        if not tendroid_wrappers:
            carb.log_warn("[DeflectionIntegration] No tendroids to register")
            return
        
        first_radius = tendroid_wrappers[0].radius
        
        if self._provided_config:
            config = self._provided_config
        else:
            config = create_scene_unit_config(
                tendroid_radius=first_radius,
                creature_radius=creature_radius
            )
        
        self._controller = DeflectionController(config)
        
        zones = config.zones
        carb.log_info(
            f"[DeflectionIntegration] Detection zones: "
            f"radius={zones.tendroid_radius:.1f}, "
            f"buffer={zones.approach_buffer:.1f}, "
            f"range={zones.detection_range:.1f}"
        )
        
        for idx, wrapper in enumerate(tendroid_wrappers):
            self._register_single(
                tendroid_id=idx,
                name=wrapper.name,
                position=wrapper.position,
                height=wrapper.length,
                radius=wrapper.radius
            )
            # Log tendroid geometry for debug
            carb.log_info(
                f"[DeflectionIntegration] Tendroid '{wrapper.name}': "
                f"pos=({wrapper.position[0]:.1f}, {wrapper.position[1]:.1f}, {wrapper.position[2]:.1f}), "
                f"height={wrapper.length:.1f}, radius={wrapper.radius:.1f}"
            )
        
        carb.log_info(
            f"[DeflectionIntegration] Registered {len(tendroid_wrappers)} tendroids"
        )
    
    def _register_single(
        self,
        tendroid_id: int,
        name: str,
        position: Tuple[float, float, float],
        height: float,
        radius: float
    ) -> None:
        """Register a single tendroid for deflection tracking."""
        geometry = TendroidGeometry(
            center_x=position[0],
            center_z=position[2],
            base_y=position[1],
            height=height,
            radius=radius
        )
        
        self._controller.register_tendroid(tendroid_id, geometry)
        self._tendroid_map[name] = tendroid_id
    
    def unregister_tendroid(self, name: str) -> None:
        """Remove a tendroid from tracking."""
        if name in self._tendroid_map and self._controller:
            tendroid_id = self._tendroid_map.pop(name)
            self._controller.unregister_tendroid(tendroid_id)
    
    def update(
        self,
        creature_controller,
        dt: float
    ) -> Dict[str, TendroidDeflectionState]:
        """Update deflection system from creature controller."""
        if not self._enabled or self._controller is None:
            return {}
        
        if creature_controller is None:
            return {}
        
        creature_pos = self._get_creature_position(creature_controller)
        creature_vel = self._get_creature_velocity(creature_controller)
        
        # Debug logging every 60 frames
        self._debug_frame_count += 1
        debug_this_frame = (self._debug_frame_count % 60 == 0)
        
        if debug_this_frame:
            carb.log_info(
                f"[Deflection DEBUG] Creature pos=({creature_pos[0]:.1f}, {creature_pos[1]:.1f}, {creature_pos[2]:.1f}), "
                f"vel=({creature_vel[0]:.1f}, {creature_vel[1]:.1f}, {creature_vel[2]:.1f})"
            )
        
        self._controller.update(creature_pos, creature_vel, dt)
        
        result = {}
        for name, tendroid_id in self._tendroid_map.items():
            state = self._controller.get_state(tendroid_id)
            if state:
                result[name] = state
                
                if debug_this_frame:
                    carb.log_info(
                        f"[Deflection DEBUG] {name}: "
                        f"approach={state.last_approach_type}, "
                        f"target={state.target_angle:.3f}, "
                        f"current={state.current_angle:.3f}, "
                        f"deflecting={state.is_deflecting}"
                    )
        
        return result
    
    def _get_creature_position(self, creature_controller) -> Tuple[float, float, float]:
        """Extract position from creature controller."""
        if hasattr(creature_controller, 'get_position'):
            pos = creature_controller.get_position()
            return (float(pos[0]), float(pos[1]), float(pos[2]))
        if hasattr(creature_controller, 'position'):
            pos = creature_controller.position
            return (float(pos[0]), float(pos[1]), float(pos[2]))
        return (0.0, 0.0, 0.0)
    
    def _get_creature_velocity(self, creature_controller) -> Tuple[float, float, float]:
        """Extract velocity from creature controller."""
        if hasattr(creature_controller, 'velocity'):
            vel = creature_controller.velocity
            return (float(vel[0]), float(vel[1]), float(vel[2]))
        return (0.0, 0.0, 0.0)
    
    def get_deflection_states(self) -> Dict[str, TendroidDeflectionState]:
        """Get all current deflection states keyed by name."""
        if self._controller is None:
            return {}
        
        result = {}
        for name, tendroid_id in self._tendroid_map.items():
            state = self._controller.get_state(tendroid_id)
            if state:
                result[name] = state
        
        return result
    
    def get_state_by_name(self, name: str) -> Optional[TendroidDeflectionState]:
        """Get deflection state for a specific tendroid by name."""
        if self._controller is None or name not in self._tendroid_map:
            return None
        return self._controller.get_state(self._tendroid_map[name])
    
    def get_debug_info(self) -> Dict:
        """Get debugging information."""
        if self._controller is None:
            return {'enabled': False, 'tendroid_count': 0}
        
        return {
            'enabled': self._enabled,
            'tendroid_count': len(self._tendroid_map),
            'controller_info': self._controller.get_debug_info(),
        }
    
    def destroy(self) -> None:
        """Cleanup resources."""
        self._tendroid_map.clear()
        self._controller = None
        carb.log_info("[DeflectionIntegration] Destroyed")
