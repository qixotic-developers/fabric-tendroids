"""
Scene manager for multiple Tendroids

Handles creation, placement, and update of all Tendroids in the scene.
"""

import carb
import omni.usd
from ..core.tendroid import Tendroid
import random


class TendroidSceneManager:
  """
  Manages a collection of Tendroids in the scene.

  Handles spawning, positioning, animation updates, and cleanup
  for all Tendroids.
  """

  def __init__(self):
    """Initialize scene manager."""
    self.tendroids = []
    self.update_subscription = None
    self.is_running = False

    carb.log_info("[TendroidSceneManager] Initialized")

  def create_tendroids(
    self,
    count: int = 15,
    spawn_area: tuple = (200, 200),
    radius_range: tuple = (8, 12),
    length_range: tuple = (80, 120),
    num_segments: int = 16
  ) -> bool:
    """
    Create multiple Tendroids in the scene.

    Args:
        count: Number of Tendroids to create
        spawn_area: (width, depth) of spawning area
        radius_range: (min, max) radius for random variation
        length_range: (min, max) length for random variation
        num_segments: Number of segments per Tendroid

    Returns:
        True if successful, False otherwise
    """
    try:
      # Get USD context
      ctx = omni.usd.get_context()
      if not ctx:
        carb.log_error("[TendroidSceneManager] No USD context available")
        return False

      stage = ctx.get_stage()
      if not stage:
        carb.log_error("[TendroidSceneManager] No USD stage available")
        return False

      # Clear existing Tendroids
      self.clear_tendroids(stage)

      # Create new Tendroids with random positions
      width, depth = spawn_area

      for i in range(count):
        # Random position within spawn area
        x = random.uniform(-width / 2, width / 2)
        z = random.uniform(-depth / 2, depth / 2)
        y = 0  # Ground level

        # Random size variation
        radius = random.uniform(*radius_range)
        length = random.uniform(*length_range)

        # Create Tendroid
        tendroid = Tendroid(
          name=f"Tendroid_{i:02d}",
          position=(x, y, z),
          radius=radius,
          length=length,
          num_segments=num_segments
        )

        if tendroid.create(stage):
          self.tendroids.append(tendroid)
        else:
          carb.log_warn(f"[TendroidSceneManager] Failed to create Tendroid {i}")

      carb.log_info(
        f"[TendroidSceneManager] Created {len(self.tendroids)} Tendroids"
      )
      return True

    except Exception as e:
      carb.log_error(f"[TendroidSceneManager] Failed to create Tendroids: {e}")
      import traceback
      traceback.print_exc()
      return False

  def create_single_tendroid(
    self,
    position: tuple = (0, 0, 0),
    radius: float = 10.0,
    length: float = 100.0,
    num_segments: int = 32,
    bulge_length_percent: float = 40.0,
    amplitude: float = 0.35,
    wave_speed: float = 40.0,
    cycle_delay: float = 2.0
  ) -> bool:
    """
    Create a single Tendroid with custom parameters.

    Args:
        position: (x, y, z) world position
        radius: Cylinder radius
        length: Total length
        num_segments: Vertical resolution
        bulge_length_percent: Bulge size as % of length
        amplitude: Maximum radial expansion (0.35 = 35%)
        wave_speed: Wave travel speed
        cycle_delay: Pause between cycles

    Returns:
        True if successful, False otherwise
    """
    try:
      # Get USD context
      ctx = omni.usd.get_context()
      if not ctx:
        carb.log_error("[TendroidSceneManager] No USD context available")
        return False

      stage = ctx.get_stage()
      if not stage:
        carb.log_error("[TendroidSceneManager] No USD stage available")
        return False

      # Clear existing Tendroids
      self.clear_tendroids(stage)

      # Create single Tendroid
      tendroid = Tendroid(
        name="Tendroid_Single",
        position=position,
        radius=radius,
        length=length,
        num_segments=num_segments
      )

      if tendroid.create(stage):
        # Set custom breathing parameters
        if tendroid.breathing_animator:
          tendroid.breathing_animator.set_parameters(
            bulge_length_percent=bulge_length_percent,
            amplitude=amplitude,
            wave_speed=wave_speed,
            cycle_delay=cycle_delay
          )

        self.tendroids.append(tendroid)

        carb.log_info(
          f"[TendroidSceneManager] Created single Tendroid: "
          f"R={radius:.1f}, L={length:.1f}, "
          f"Wave={bulge_length_percent:.0f}%, "
          f"Amp={amplitude:.2f}, Speed={wave_speed:.0f}"
        )
        return True
      else:
        carb.log_error("[TendroidSceneManager] Failed to create single Tendroid")
        return False

    except Exception as e:
      carb.log_error(f"[TendroidSceneManager] Failed to create single Tendroid: {e}")
      import traceback
      traceback.print_exc()
      return False

  def start_animation(self):
    """Start animating all Tendroids."""
    if self.is_running:
      return

    # Subscribe to update events
    update_stream = omni.kit.app.get_app().get_update_event_stream()
    self.update_subscription = update_stream.create_subscription_to_pop(
      self._on_update,
      name="TendroidSceneManager.Update"
    )

    self.is_running = True
    carb.log_info("[TendroidSceneManager] Animation started")

  def stop_animation(self):
    """Stop animating all Tendroids."""
    if not self.is_running:
      return

    if self.update_subscription:
      self.update_subscription.unsubscribe()
      self.update_subscription = None

    self.is_running = False
    carb.log_info("[TendroidSceneManager] Animation stopped")

  def _on_update(self, event):
    """
    Update callback called every frame.

    Args:
        event: Update event with timing information
    """
    try:
      # Get delta time (assume 60fps if not available)
      dt = 1.0 / 60.0
      if hasattr(event.payload, 'dt'):
        dt = event.payload['dt']

      # Update all Tendroids
      for tendroid in self.tendroids:
        tendroid.update(dt)

    except Exception as e:
      carb.log_error(f"[TendroidSceneManager] Update error: {e}")

  def clear_tendroids(self, stage=None):
    """
    Remove all Tendroids from the scene.

    Args:
        stage: USD stage (if None, will get current stage)
    """
    if not stage:
      ctx = omni.usd.get_context()
      if ctx:
        stage = ctx.get_stage()

    if stage:
      for tendroid in self.tendroids:
        tendroid.destroy(stage)

    self.tendroids.clear()
    carb.log_info("[TendroidSceneManager] Cleared all Tendroids")

  def get_tendroid_count(self) -> int:
    """Get the number of active Tendroids."""
    return len(self.tendroids)

  def set_all_active(self, active: bool):
    """Enable or disable animation for all Tendroids."""
    for tendroid in self.tendroids:
      tendroid.set_active(active)

  def shutdown(self):
    """Cleanup when shutting down."""
    self.stop_animation()

    ctx = omni.usd.get_context()
    if ctx:
      stage = ctx.get_stage()
      if stage:
        self.clear_tendroids(stage)

    carb.log_info("[TendroidSceneManager] Shutdown complete")
