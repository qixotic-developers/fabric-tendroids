"""
Material safety checker for Tendroid animation

Detects glass/transparent materials that could cause GPU crashes with dynamic geometry.
"""

import carb
import omni.usd
from pxr import UsdShade


class MaterialSafetyChecker:
  """
  Monitors mesh materials for GPU-unsafe configurations.
  
  Glass materials with dynamic geometry are EXTREMELY GPU-intensive
  in path-traced rendering and WILL cause GPU crashes.
  
  This checker periodically examines material bindings and blocks
  animation when unsafe materials are detected.
  """
  
  def __init__(self, mesh_path: str, check_interval: int = 30):
    """
    Initialize material safety checker.
    
    Args:
        mesh_path: USD path to mesh to monitor
        check_interval: Frames between material checks
    """
    self.mesh_path = mesh_path
    self.check_interval = check_interval
    self.check_counter = 0
    
    # Safety state
    self.is_glass_material = False
    self.animation_disabled_reason = None
    
    # Glass detection keywords
    self.glass_keywords = [
      'glass', 'transparent', 'translucent',
      'omni', 'clear', 'crystal', 'refract'
    ]
  
  def check_material(self) -> bool:
    """
    Check if mesh has glass/transparent material applied.
    
    Returns:
        True if material is safe for animation, False if glass detected
    """
    try:
      usd_context = omni.usd.get_context()
      if not usd_context:
        return True
      
      stage = usd_context.get_stage()
      if not stage:
        return True
      
      mesh_prim = stage.GetPrimAtPath(self.mesh_path)
      if not mesh_prim or not mesh_prim.IsValid():
        return True
      
      # Check material binding
      binding_api = UsdShade.MaterialBindingAPI(mesh_prim)
      material, _ = binding_api.ComputeBoundMaterial()
      
      if material:
        material_path = str(material.GetPrim().GetPath())
        material_name = material_path.split('/')[-1]
        
        # Clean strings for matching
        material_path_clean = self._clean_string(material_path)
        material_name_clean = self._clean_string(material_name)
        
        # Check for glass keywords
        was_glass = self.is_glass_material
        self.is_glass_material = any(
          keyword in material_path_clean or keyword in material_name_clean
          for keyword in self.glass_keywords
        )
        
        # Log material changes
        self._log_material_change(was_glass, material_name, material_path)
      
      return not self.is_glass_material
      
    except Exception as e:
      carb.log_warn(f"[MaterialSafetyChecker] Detection failed: {e}")
      return True  # Fail-safe: allow animation if check fails
  
  def should_check_now(self) -> bool:
    """
    Check if this frame should perform material check.
    
    Returns:
        True if enough frames have passed since last check
    """
    self.check_counter += 1
    if self.check_counter >= self.check_interval:
      self.check_counter = 0
      return True
    return False
  
  def is_safe_for_animation(self) -> bool:
    """Check if animation is safe (not glass material)."""
    return not self.is_glass_material
  
  def get_status_message(self) -> str:
    """Get human-readable safety status."""
    if self.is_glass_material:
      return f"⚠️ Animation disabled: {self.animation_disabled_reason}"
    return "✓ Material safe for animation"
  
  def _clean_string(self, text: str) -> str:
    """Remove separators and lowercase for matching."""
    return text.lower().replace('_', '').replace('-', '').replace(' ', '')
  
  def _log_material_change(self, was_glass: bool, material_name: str, material_path: str):
    """Log material detection results."""
    if self.is_glass_material and not was_glass:
      carb.log_error(
        f"[MaterialSafetyChecker] ⚠️⚠️⚠️ GLASS MATERIAL DETECTED: '{material_name}' ⚠️⚠️⚠️\n"
        f"                        Path: {material_path}\n"
        f"                        Animation BLOCKED to prevent GPU crash!"
      )
      self.animation_disabled_reason = f"Glass material: {material_name}"
    elif not self.is_glass_material and not was_glass:
      carb.log_info(f"[MaterialSafetyChecker] Material: '{material_name}' (safe)")
