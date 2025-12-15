"""
Creature Collider Helper - PhysX capsule collider setup

Creates and manages the PhysX capsule collider for the creature envelope.
Implements TEND-12: Implement envelope as PhysX capsule collider.
"""

import carb
from pxr import Gf, Sdf, UsdGeom, UsdPhysics

from .envelope_constants import (CONTACT_OFFSET, DEBUG_COLLIDER_COLOR, DEBUG_COLLIDER_OPACITY, DEBUG_SHOW_COLLIDER,
                                 ENVELOPE_AXIS, ENVELOPE_HALF_HEIGHT, ENVELOPE_RADIUS, REST_OFFSET)


def create_creature_collider(stage, creature_prim_path: str) -> bool:
  """
  Create PhysX capsule collider for creature envelope.

  Args:
      stage: USD stage
      creature_prim_path: Path to creature parent prim (e.g., "/World/Creature")

  Returns:
      True if collider created successfully, False otherwise
  """
  try:
    creature_prim = stage.GetPrimAtPath(creature_prim_path)
    if not creature_prim.IsValid():
      carb.log_error(f"[CreatureCollider] Invalid prim path: {creature_prim_path}")
      return False

    # Create collider child prim
    collider_path = f"{creature_prim_path}/Collider"

    # Remove existing collider if present
    existing = stage.GetPrimAtPath(collider_path)
    if existing.IsValid():
      stage.RemovePrim(collider_path)

    # Create capsule geometry for collider
    capsule = UsdGeom.Capsule.Define(stage, collider_path)
    capsule.CreateRadiusAttr().Set(ENVELOPE_RADIUS)
    capsule.CreateHeightAttr().Set(ENVELOPE_HALF_HEIGHT * 2.0)  # Full height
    capsule.CreateAxisAttr().Set(ENVELOPE_AXIS)

    # Make collider invisible by default (physics only)
    if not DEBUG_SHOW_COLLIDER:
      UsdGeom.Imageable(capsule).MakeInvisible()
    else:
      _apply_debug_material(stage, capsule, collider_path)

    # Apply collision API to the capsule
    collider_prim = capsule.GetPrim()
    UsdPhysics.CollisionAPI.Apply(collider_prim)

    # Configure PhysX collision attributes
    _configure_physx_collision(stage, collider_prim)

    carb.log_info(
      f"[CreatureCollider] Created capsule collider at {collider_path} "
      f"(r={ENVELOPE_RADIUS}, h={ENVELOPE_HALF_HEIGHT * 2.0}, axis={ENVELOPE_AXIS})"
    )

    return True

  except Exception as e:
    carb.log_error(f"[CreatureCollider] Failed to create collider: {e}")
    import traceback
    traceback.print_exc()
    return False


def _configure_physx_collision(stage, collider_prim):
  """
  Configure PhysX-specific collision attributes.

  Args:
      stage: USD stage
      collider_prim: The collider prim to configure
  """
  try:
    # Try to import PhysxSchema - may not be available in all environments
    from pxr import PhysxSchema

    physx_collision = PhysxSchema.PhysxCollisionAPI.Apply(collider_prim)
    physx_collision.CreateContactOffsetAttr().Set(CONTACT_OFFSET)
    physx_collision.CreateRestOffsetAttr().Set(REST_OFFSET)

    carb.log_info(
      f"[CreatureCollider] PhysX configured: "
      f"contactOffset={CONTACT_OFFSET}, restOffset={REST_OFFSET}"
    )

  except ImportError:
    carb.log_warn(
      "[CreatureCollider] PhysxSchema not available - "
      "contact offsets not configured"
    )
  except Exception as e:
    carb.log_warn(f"[CreatureCollider] PhysX config failed: {e}")


def _apply_debug_material(stage, capsule, collider_path: str):
  """
  Apply semi-transparent debug material to collider visualization.

  Args:
      stage: USD stage
      capsule: UsdGeom.Capsule object
      collider_path: Path to the collider prim
  """
  from pxr import UsdShade

  mat_path = f"{collider_path}/DebugMaterial"
  material = UsdShade.Material.Define(stage, mat_path)

  shader = UsdShade.Shader.Define(stage, f"{mat_path}/Surface")
  shader.CreateIdAttr("UsdPreviewSurface")

  shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
    Gf.Vec3f(*DEBUG_COLLIDER_COLOR)
  )
  shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(DEBUG_COLLIDER_OPACITY)
  shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
  shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.8)

  material.CreateSurfaceOutput().ConnectToSource(
    shader.ConnectableAPI(), "surface"
  )

  UsdShade.MaterialBindingAPI(capsule).Bind(material)


def destroy_creature_collider(stage, creature_prim_path: str):
  """
  Remove creature collider from stage.

  Args:
      stage: USD stage
      creature_prim_path: Path to creature parent prim
  """
  collider_path = f"{creature_prim_path}/Collider"
  prim = stage.GetPrimAtPath(collider_path)
  if prim.IsValid():
    stage.RemovePrim(collider_path)
    carb.log_info(f"[CreatureCollider] Removed collider at {collider_path}")


def get_collider_bounds(stage, creature_prim_path: str) -> tuple:
  """
  Get the world-space bounding box of the creature collider.

  Args:
      stage: USD stage
      creature_prim_path: Path to creature parent prim

  Returns:
      Tuple of (min_point, max_point) as Gf.Vec3f, or None if not found
  """
  collider_path = f"{creature_prim_path}/Collider"
  prim = stage.GetPrimAtPath(collider_path)

  if not prim.IsValid():
    return None

  imageable = UsdGeom.Imageable(prim)
  bounds = imageable.ComputeWorldBound(0, "default")
  box = bounds.GetBox()

  return (box.GetMin(), box.GetMax())


def update_contact_offsets(
  stage,
  creature_prim_path: str,
  contact_offset: float = None,
  rest_offset: float = None
) -> bool:
  """
  Update PhysX contact offset attributes at runtime.

  Implements TEND-13: Configure contact offset attributes.
  Allows dynamic tuning of collision detection sensitivity.

  Args:
      stage: USD stage
      creature_prim_path: Path to creature parent prim
      contact_offset: New contact offset value (meters). If None, keeps current.
      rest_offset: New rest offset value (meters). If None, keeps current.

  Returns:
      True if updated successfully, False otherwise

  Note:
      contact_offset must be >= rest_offset (PhysX requirement)
  """
  try:
    from pxr import PhysxSchema

    collider_path = f"{creature_prim_path}/Collider"
    prim = stage.GetPrimAtPath(collider_path)

    if not prim.IsValid():
      carb.log_error(f"[CreatureCollider] Collider not found: {collider_path}")
      return False

    # Validate offset relationship
    if contact_offset is not None and rest_offset is not None:
      if contact_offset < rest_offset:
        carb.log_error(
          f"[CreatureCollider] contact_offset ({contact_offset}) must be "
          f">= rest_offset ({rest_offset})"
        )
        return False

    physx_api = PhysxSchema.PhysxCollisionAPI(prim)
    if not physx_api:
      carb.log_error("[CreatureCollider] PhysxCollisionAPI not found on prim")
      return False

    if contact_offset is not None:
      physx_api.GetContactOffsetAttr().Set(contact_offset)
      carb.log_info(f"[CreatureCollider] Updated contactOffset: {contact_offset}")

    if rest_offset is not None:
      physx_api.GetRestOffsetAttr().Set(rest_offset)
      carb.log_info(f"[CreatureCollider] Updated restOffset: {rest_offset}")

    return True

  except ImportError:
    carb.log_error("[CreatureCollider] PhysxSchema not available")
    return False
  except Exception as e:
    carb.log_error(f"[CreatureCollider] Failed to update offsets: {e}")
    return False


def get_contact_offsets(stage, creature_prim_path: str) -> dict:
  """
  Get current PhysX contact offset values.

  Args:
      stage: USD stage
      creature_prim_path: Path to creature parent prim

  Returns:
      Dict with 'contact_offset' and 'rest_offset', or None if not found
  """
  try:
    from pxr import PhysxSchema

    collider_path = f"{creature_prim_path}/Collider"
    prim = stage.GetPrimAtPath(collider_path)

    if not prim.IsValid():
      return None

    physx_api = PhysxSchema.PhysxCollisionAPI(prim)
    if not physx_api:
      return None

    return {
      'contact_offset': physx_api.GetContactOffsetAttr().Get(),
      'rest_offset': physx_api.GetRestOffsetAttr().Get(),
    }

  except ImportError:
    return None
  except Exception:
    return None


def set_collider_visibility(stage, creature_prim_path: str, visible: bool):
  """
  Toggle collider visibility for debugging.

  Args:
      stage: USD stage
      creature_prim_path: Path to creature parent prim
      visible: True to show collider, False to hide
  """
  collider_path = f"{creature_prim_path}/Collider"
  prim = stage.GetPrimAtPath(collider_path)

  if not prim.IsValid():
    return

  imageable = UsdGeom.Imageable(prim)
  if visible:
    imageable.MakeVisible()
    # Apply debug material if not already present
    mat_path = f"{collider_path}/DebugMaterial"
    if not stage.GetPrimAtPath(mat_path).IsValid():
      capsule = UsdGeom.Capsule(prim)
      _apply_debug_material(stage, capsule, collider_path)
    carb.log_info("[CreatureCollider] Collider visible")
  else:
    imageable.MakeInvisible()
    carb.log_info("[CreatureCollider] Collider hidden")
