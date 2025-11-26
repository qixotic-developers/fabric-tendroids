"""
Fabric/USDRT utilities for GPU-accelerated mesh deformation

Provides helper functions for working with Fabric-backed USD attributes
and USDRT stage access for zero-copy GPU operations.
"""

import carb


class FabricHelper:
    """
    Helper utilities for Fabric/USDRT integration.
    
    Provides stage attachment, prim access, and attribute
    validation for GPU-resident mesh operations.
    """
    
    _cached_stage = None
    _cached_stage_id = None
    
    @staticmethod
    def get_usdrt_stage(stage_id):
        """
        Get USDRT stage handle with caching.
        
        Args:
            stage_id: USD stage ID from omni.usd.get_context().get_stage_id()
        
        Returns:
            usdrt.Usd.Stage attached to Fabric
        """
        from usdrt import Usd
        
        # Cache stage handle to avoid repeated attachments
        if FabricHelper._cached_stage_id != stage_id:
            FabricHelper._cached_stage = Usd.Stage.Attach(stage_id)
            FabricHelper._cached_stage_id = stage_id
        
        return FabricHelper._cached_stage
    
    @staticmethod
    def verify_fabric_mesh(stage_id, mesh_path):
        """
        Verify mesh is Fabric-ready for deformation.
        
        Checks for:
        1. Prim exists in Fabric
        2. Has points attribute
        3. Has Deformable tag
        
        Args:
            stage_id: USD stage ID
            mesh_path: Prim path to mesh
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        from usdrt import Sdf
        
        try:
            usdrt_stage = FabricHelper.get_usdrt_stage(stage_id)
            prim = usdrt_stage.GetPrimAtPath(Sdf.Path(mesh_path))
            
            if not prim:
                return False, f"Prim at path {mesh_path} not in Fabric"
            
            if not prim.HasAttribute("points"):
                return False, f"Prim at {mesh_path} has no points attribute"
            
            if not prim.HasAttribute("Deformable"):
                carb.log_warn(
                    f"[FabricHelper] Mesh {mesh_path} missing Deformable tag - "
                    "OmniHydra will render from USD instead of Fabric"
                )
            
            return True, "Fabric mesh verified"
            
        except Exception as e:
            return False, f"Fabric verification failed: {e}"
    
    @staticmethod
    def get_fabric_points_attribute(usdrt_stage, mesh_path):
        """
        Get Fabric-backed points attribute for mesh.
        
        Args:
            usdrt_stage: USDRT stage handle
            mesh_path: Prim path to mesh
        
        Returns:
            usdrt.UsdAttribute for points, or None if failed
        """
        from usdrt import Sdf
        
        try:
            prim = usdrt_stage.GetPrimAtPath(Sdf.Path(mesh_path))
            if not prim:
                carb.log_error(
                    f"[FabricHelper] Prim not found in Fabric: {mesh_path}"
                )
                return None
            
            points_attr = prim.GetAttribute("points")
            if not points_attr:
                carb.log_error(
                    f"[FabricHelper] Points attribute not found: {mesh_path}"
                )
                return None
            
            return points_attr
            
        except Exception as e:
            carb.log_error(
                f"[FabricHelper] Failed to get points attribute for "
                f"{mesh_path}: {e}"
            )
            return None
    
    @staticmethod
    def clear_cache():
        """Clear cached stage handle (call on stage changes)."""
        FabricHelper._cached_stage = None
        FabricHelper._cached_stage_id = None
