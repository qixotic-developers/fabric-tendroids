"""
Color Effect Controller - USD material color management for shock effects

Applies color changes to creature materials based on contact events.
Manages the connection between color state and USD shader properties.

Implements TEND-26: Implement shock color change effect.
Implements TEND-100: Create color_effect_controller.py module.
"""

import carb

from .color_effect_helpers import (
    ColorConfig,
    ColorEffectState,
    ColorEffectStatus,
    trigger_shock,
    check_shock_exit,
    reset_to_normal,
    is_shocked,
)


class ColorEffectController:
    """
    Controller for creature color effects on contact.
    
    Manages shock color changes and integrates with USD materials.
    """
    
    def __init__(
        self,
        stage=None,
        material_path: str = "/World/Materials/CreatureBody",
        config: ColorConfig = None,
    ):
        """
        Initialize color effect controller.
        
        Args:
            stage: USD stage (optional, for testing without USD)
            material_path: Path to creature body material
            config: Color configuration
        """
        self._stage = stage
        self._material_path = material_path
        self._shader_path = f"{material_path}/Surface"
        self._config = config or ColorConfig()
        
        # Current state
        self._status = ColorEffectStatus()
        
        # Cache shader reference
        self._shader = None
        self._diffuse_input = None
        
        if stage is not None:
            self._cache_shader_reference()
    
    def _cache_shader_reference(self) -> bool:
        """Cache reference to shader for efficient updates."""
        try:
            from pxr import UsdShade, Sdf
            
            shader_prim = self._stage.GetPrimAtPath(self._shader_path)
            if not shader_prim or not shader_prim.IsValid():
                carb.log_warn(
                    f"[ColorEffectController] Shader not found: {self._shader_path}"
                )
                return False
            
            self._shader = UsdShade.Shader(shader_prim)
            self._diffuse_input = self._shader.GetInput("diffuseColor")
            
            if not self._diffuse_input:
                carb.log_warn(
                    "[ColorEffectController] diffuseColor input not found"
                )
                return False
            
            return True
            
        except Exception as e:
            carb.log_error(f"[ColorEffectController] Failed to cache shader: {e}")
            return False
    
    @property
    def status(self) -> ColorEffectStatus:
        """Get current color effect status."""
        return self._status
    
    @property
    def is_shocked(self) -> bool:
        """Check if currently showing shock color."""
        return is_shocked(self._status)
    
    @property
    def shock_count(self) -> int:
        """Get total number of shocks received."""
        return self._status.shock_count
    
    def on_contact(self) -> None:
        """
        Handle contact event - trigger shock color.
        
        Called when creature contacts a tendroid.
        """
        self._status = trigger_shock(self._status, self._config)
        self._apply_color_to_material()
        
        carb.log_info(
            f"[ColorEffectController] Shock triggered, count={self._status.shock_count}"
        )
    
    def update(self, distance_to_tendroid: float) -> None:
        """
        Update color state based on distance.
        
        Should be called each frame when in shocked state.
        
        Args:
            distance_to_tendroid: Current horizontal distance to nearest tendroid
        """
        if self._status.state == ColorEffectState.NORMAL:
            return
        
        old_state = self._status.state
        self._status = check_shock_exit(
            self._status, distance_to_tendroid, self._config
        )
        
        if self._status.state != old_state:
            self._apply_color_to_material()
            carb.log_info(
                f"[ColorEffectController] State changed: {old_state} -> {self._status.state}"
            )
    
    def reset(self) -> None:
        """Reset to normal color immediately."""
        self._status = reset_to_normal(self._status, self._config)
        self._apply_color_to_material()
    
    def _apply_color_to_material(self) -> None:
        """Apply current color to USD material."""
        if self._diffuse_input is None:
            return
        
        try:
            from pxr import Gf
            
            r, g, b = self._status.current_color
            self._diffuse_input.Set(Gf.Vec3f(r, g, b))
            
        except Exception as e:
            carb.log_error(f"[ColorEffectController] Failed to apply color: {e}")
    
    def set_stage(self, stage) -> None:
        """
        Set USD stage reference.
        
        Useful for deferred initialization or testing.
        """
        self._stage = stage
        if stage is not None:
            self._cache_shader_reference()
