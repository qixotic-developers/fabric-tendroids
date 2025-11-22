"""
Environment setup helper for Sky, Lighting, and Materials

Applies configured settings to create consistent scene environment.
"""

import carb
from pxr import UsdGeom, UsdLux, Gf, UsdShade, Sdf
from .environment_config import EnvironmentConfig


class EnvironmentSetup:
    """Helper for setting up scene environment elements."""
    
    @staticmethod
    def setup_environment(stage, config: EnvironmentConfig = None) -> bool:
        """
        Setup complete environment: Sky, DistantLight, and materials.
        
        Args:
            stage: USD stage
            config: Environment configuration
        
        Returns:
            True if successful
        """
        if config is None:
            config = EnvironmentConfig()
        
        try:
            # Ensure /Environment exists
            env_path = "/Environment"
            if not stage.GetPrimAtPath(env_path).IsValid():
                UsdGeom.Xform.Define(stage, env_path)
            
            # Setup Sky - ALWAYS update settings
            EnvironmentSetup._setup_sky(stage, config.sky)
            
            # Setup DistantLight - ALWAYS update settings
            EnvironmentSetup._setup_distant_light(stage, config.distant_light)
            
            carb.log_info("[EnvironmentSetup] Environment setup complete")
            return True
            
        except Exception as e:
            carb.log_error(f"[EnvironmentSetup] Failed to setup environment: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def _setup_sky(stage, config):
        """Setup Sky dome - creates or updates."""
        sky_prim = stage.GetPrimAtPath(config.path)
        
        if sky_prim.IsValid():
            # Update existing
            sky = UsdLux.DomeLight(sky_prim)
            carb.log_info(f"[EnvironmentSetup] Updating existing Sky at {config.path}")
        else:
            # Create new
            sky = UsdLux.DomeLight.Define(stage, config.path)
            carb.log_info(f"[EnvironmentSetup] Creating Sky at {config.path}")
        
        # Set/update intensity
        sky.CreateIntensityAttr().Set(config.intensity)
        
        # Setup transform - use GetOrAdd to handle existing ops
        xform = UsdGeom.Xformable(sky)
        
        # Get or add translate op
        translate_ops = [op for op in xform.GetOrderedXformOps() 
                        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate]
        if translate_ops:
            translate_op = translate_ops[0]
        else:
            translate_op = xform.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(0, config.translate_y, 0))
        
        # Get or add rotate op
        rotate_ops = [op for op in xform.GetOrderedXformOps() 
                     if op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ]
        if rotate_ops:
            rotate_op = rotate_ops[0]
        else:
            rotate_op = xform.AddRotateXYZOp()
        
        # Set rotation value with correct precision
        if rotate_op.GetPrecision() == UsdGeom.XformOp.PrecisionDouble:
            rotate_op.Set(Gf.Vec3d(0, config.rotate_y, config.rotate_z))
        else:
            rotate_op.Set(Gf.Vec3f(0, config.rotate_y, config.rotate_z))
        
        carb.log_info(
            f"[EnvironmentSetup] Sky configured: "
            f"intensity={config.intensity}, Y={config.translate_y}, "
            f"rot=[0,{config.rotate_y},{config.rotate_z}]"
        )
    
    @staticmethod
    def _setup_distant_light(stage, config):
        """Setup DistantLight (sun) - creates or updates."""
        light_prim = stage.GetPrimAtPath(config.path)
        
        if light_prim.IsValid():
            # Update existing
            light = UsdLux.DistantLight(light_prim)
            carb.log_info(
                f"[EnvironmentSetup] Updating existing DistantLight at {config.path}"
            )
        else:
            # Create new
            light = UsdLux.DistantLight.Define(stage, config.path)
            carb.log_info(f"[EnvironmentSetup] Creating DistantLight at {config.path}")
        
        # Set/update light properties
        light.CreateIntensityAttr().Set(config.intensity)
        light.CreateExposureAttr().Set(config.exposure)
        light.CreateAngleAttr().Set(config.angle)
        light.CreateColorAttr().Set(Gf.Vec3f(*config.color))
        
        # Setup transform - use GetOrAdd to handle existing ops
        xform = UsdGeom.Xformable(light)
        
        # Get or add translate op
        translate_ops = [op for op in xform.GetOrderedXformOps() 
                        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate]
        if translate_ops:
            translate_op = translate_ops[0]
        else:
            translate_op = xform.AddTranslateOp()
        translate_op.Set(Gf.Vec3d(config.translate_x, config.translate_y, 0))
        
        # Get or add rotate op
        rotate_ops = [op for op in xform.GetOrderedXformOps() 
                     if op.GetOpType() == UsdGeom.XformOp.TypeRotateXYZ]
        if rotate_ops:
            rotate_op = rotate_ops[0]
        else:
            rotate_op = xform.AddRotateXYZOp()
        
        # Set rotation value with correct precision
        if rotate_op.GetPrecision() == UsdGeom.XformOp.PrecisionDouble:
            rotate_op.Set(Gf.Vec3d(0, config.rotate_y, config.rotate_z))
        else:
            rotate_op.Set(Gf.Vec3f(0, config.rotate_y, config.rotate_z))
        
        carb.log_info(
            f"[EnvironmentSetup] DistantLight configured: "
            f"pos=[{config.translate_x},{config.translate_y},0], "
            f"rot=[0,{config.rotate_y},{config.rotate_z}], "
            f"intensity={config.intensity}, exposure={config.exposure}, angle={config.angle}"
        )
    
    @staticmethod
    def get_sea_floor_material(stage, config) -> UsdShade.Material:
        """
        Get or create sea floor material.
        
        Args:
            stage: USD stage
            config: SeaFloorMaterialConfig
        
        Returns:
            UsdShade.Material
        """
        # Check if material already exists at specified path
        material_prim = stage.GetPrimAtPath(config.path)
        
        if config.use_existing and material_prim.IsValid():
            carb.log_info(
                f"[EnvironmentSetup] Using existing material at {config.path}"
            )
            return UsdShade.Material(material_prim)
        
        # Material doesn't exist - log warning but create fallback
        if config.use_existing:
            carb.log_warn(
                f"[EnvironmentSetup] Material not found at {config.path}, "
                f"creating fallback"
            )
        
        # Ensure /World/Looks exists
        looks_path = config.path.rsplit('/', 1)[0]
        if not stage.GetPrimAtPath(looks_path).IsValid():
            UsdGeom.Scope.Define(stage, looks_path)
        
        # Create material
        material = UsdShade.Material.Define(stage, config.path)
        
        # Create shader
        shader_path = f"{config.path}/Shader"
        shader = UsdShade.Shader.Define(stage, shader_path)
        shader.CreateIdAttr("UsdPreviewSurface")
        
        # Set material properties
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
            Gf.Vec3f(*config.diffuse_color)
        )
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(
            config.roughness
        )
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(
            config.metallic
        )
        
        # Connect shader to material
        material.CreateSurfaceOutput().ConnectToSource(
            shader.ConnectableAPI(), "surface"
        )
        
        carb.log_info(
            f"[EnvironmentSetup] Created fallback sea floor material at {config.path}"
        )
        return material
