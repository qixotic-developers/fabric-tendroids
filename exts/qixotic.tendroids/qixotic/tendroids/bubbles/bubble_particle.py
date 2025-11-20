"""
Bubble pop particle spray system

Handles droplet particles created when bubbles pop.
"""

import carb
import random
import math
from pxr import Gf, UsdGeom, UsdShade, Sdf


class PopParticle:
  """
  Single water droplet particle from bubble pop.
  
  Simple physics:
  - Initial radial velocity from pop center
  - Gravity (downward acceleration)
  - Fade out over lifetime
  """
  
  def __init__(
    self,
    particle_id: str,
    pop_position: tuple,
    velocity: tuple,
    lifetime: float,
    config,
    stage,
    prim_path: str
  ):
    """
    Initialize pop particle.
    
    Args:
        particle_id: Unique identifier
        pop_position: (x, y, z) where bubble popped
        velocity: (vx, vy, vz) initial velocity
        lifetime: Seconds before particle fades
        config: BubbleConfig instance
        stage: USD stage
        prim_path: USD path for this particle
    """
    self.particle_id = particle_id
    self.config = config
    self.stage = stage
    self.prim_path = prim_path
    
    # Physics
    self.position = list(pop_position)
    self.velocity = list(velocity)
    self.gravity = -5.0  # units/sec^2 (reduced for visibility)
    
    # Lifecycle with randomized lifetime
    self.age = 0.0
    self.lifetime = lifetime
    self.is_alive = True
    
    # USD prim
    self.prim = None
    
    # Create geometry
    self._create_geometry()
  
  def _create_geometry(self):
    """Create small sphere for droplet."""
    try:
      carb.log_warn(f"[PopParticle] Creating geometry at '{self.prim_path}'")
      
      sphere = UsdGeom.Sphere.Define(self.stage, self.prim_path)
      sphere.GetRadiusAttr().Set(self.config.particle_size)
      
      # Set initial position
      sphere.AddTranslateOp().Set(Gf.Vec3d(*self.position))
      
      carb.log_warn(
        f"[PopParticle] Sphere created with radius={self.config.particle_size}, "
        f"position={self.position}"
      )
      
      # Apply water material (slightly opaque)
      self._apply_water_material(sphere.GetPrim())
      
      self.prim = sphere.GetPrim()
      carb.log_warn(f"[PopParticle] Geometry creation complete")
      
    except Exception as e:
      carb.log_error(f"[PopParticle] Failed to create geometry: {e}")
  
  def _apply_water_material(self, prim):
    """Apply semi-transparent water material."""
    try:
      material_path = Sdf.Path(f"{self.prim_path}/Material")
      material = UsdShade.Material.Define(self.stage, material_path)
      
      shader = UsdShade.Shader.Define(
        self.stage,
        material_path.AppendPath("Shader")
      )
      shader.CreateIdAttr("UsdPreviewSurface")
      
      # Water droplet properties
      shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(0.7, 0.9, 1.0)
      )
      shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
      shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.1)
      shader.CreateInput("opacity", Sdf.ValueTypeNames.Float).Set(0.7)
      shader.CreateInput("ior", Sdf.ValueTypeNames.Float).Set(1.33)
      
      material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(),
        "surface"
      )
      
      UsdShade.MaterialBindingAPI(prim).Bind(material)
      
    except Exception as e:
      carb.log_error(f"[PopParticle] Failed to apply material: {e}")
  
  def update(self, dt: float):
    """
    Update particle physics and check lifetime.
    
    Args:
        dt: Delta time in seconds
    """
    if not self.is_alive:
      return
    
    self.age += dt
    
    # Check individual lifetime (randomized per particle)
    if self.age >= self.lifetime:
      self.is_alive = False
      return
    
    # Apply gravity
    self.velocity[1] += self.gravity * dt
    
    # Update position
    self.position[0] += self.velocity[0] * dt
    self.position[1] += self.velocity[1] * dt
    self.position[2] += self.velocity[2] * dt
    
    # Update USD transform
    self._update_transform()
  
  def _update_transform(self):
    """Update USD position."""
    if not self.prim:
      return
    
    try:
      xform = UsdGeom.Xformable(self.prim)
      xform.ClearXformOpOrder()
      
      translate_op = xform.AddTranslateOp()
      translate_op.Set(Gf.Vec3d(*self.position))
      
    except Exception as e:
      carb.log_error(f"[PopParticle] Failed to update transform: {e}")
  
  def destroy(self):
    """Remove particle from stage."""
    if self.prim and self.stage:
      try:
        self.stage.RemovePrim(self.prim_path)
      except Exception as e:
        carb.log_error(f"[PopParticle] Failed to destroy: {e}")
    
    self.prim = None
    self.is_alive = False


class PopParticleManager:
  """Manages pop particle creation and lifecycle."""
  
  def __init__(self, stage, config):
    """
    Initialize particle manager.
    
    Args:
        stage: USD stage
        config: BubbleConfig instance
    """
    self.stage = stage
    self.config = config
    self.particles = []
    self.particle_counter = 0
    
    # Parent path
    self.parent_path = "/World/Bubbles/PopParticles"
    self._ensure_parent()
  
  def _ensure_parent(self):
    """Create parent prim if needed."""
    if not self.stage.GetPrimAtPath(self.parent_path):
      UsdGeom.Scope.Define(self.stage, self.parent_path)
  
  def create_pop_spray(self, pop_position: tuple, bubble_velocity: list = None):
    """
    Create spray of particles at pop location.
    
    Args:
        pop_position: (x, y, z) where bubble popped
        bubble_velocity: [vx, vy, vz] bubble's velocity at pop (optional)
    """
    if bubble_velocity is None:
      bubble_velocity = [0.0, 0.0, 0.0]
    
    carb.log_warn(
      f"[PopParticleManager] create_pop_spray called at {pop_position}, "
      f"bubble_velocity={bubble_velocity}, current particles: {len(self.particles)}/{self.config.max_particles}"
    )
    
    # Check particle limit
    if len(self.particles) >= self.config.max_particles:
      carb.log_warn("[PopParticleManager] Particle limit reached, skipping spray")
      return
    
    num_particles = min(
      self.config.particles_per_pop,
      self.config.max_particles - len(self.particles)
    )
    
    carb.log_warn(f"[PopParticleManager] Creating {num_particles} particles")
    
    for i in range(num_particles):
      self._create_particle(pop_position, bubble_velocity)
  
  def _create_particle(self, pop_position: tuple, bubble_velocity: list):
    """Create single spray particle."""
    self.particle_counter += 1
    particle_id = f"pop_particle_{self.particle_counter:05d}"
    prim_path = f"{self.parent_path}/{particle_id}"
    
    carb.log_warn(f"[PopParticleManager] Creating particle '{particle_id}' at {pop_position}")
    
    # Random radial velocity with upward bias
    angle = random.uniform(0, 2 * math.pi)
    elevation = random.uniform(
      -self.config.particle_spread / 2,
      self.config.particle_spread
    )
    
    # Convert to spray velocity vector
    spray_speed = self.config.particle_speed
    spray_vx = spray_speed * math.cos(angle) * math.cos(math.radians(elevation))
    spray_vy = spray_speed * math.sin(math.radians(elevation))
    spray_vz = spray_speed * math.sin(angle) * math.cos(math.radians(elevation))
    
    # Add bubble's velocity to spray velocity (inherit upward motion)
    vx = bubble_velocity[0] + spray_vx
    vy = bubble_velocity[1] + spray_vy
    vz = bubble_velocity[2] + spray_vz
    
    # Randomize lifetime for staggered fade (70% to 130% of base)
    lifetime = self.config.particle_lifetime * random.uniform(0.7, 1.3)
    
    carb.log_warn(
      f"[PopParticleManager] Velocity: ({vx:.2f}, {vy:.2f}, {vz:.2f}), "
      f"lifetime: {lifetime:.2f}s"
    )
    
    particle = PopParticle(
      particle_id=particle_id,
      pop_position=pop_position,
      velocity=(vx, vy, vz),
      lifetime=lifetime,
      config=self.config,
      stage=self.stage,
      prim_path=prim_path
    )
    
    self.particles.append(particle)
    carb.log_warn(f"[PopParticleManager] Particle created, total: {len(self.particles)}")
  
  def update(self, dt: float):
    """Update all particles and remove dead ones."""
    for particle in self.particles:
      particle.update(dt)
    
    # Remove dead particles
    dead = [p for p in self.particles if not p.is_alive]
    for particle in dead:
      particle.destroy()
      self.particles.remove(particle)
  
  def clear_all(self):
    """Remove all particles."""
    for particle in self.particles:
      particle.destroy()
    self.particles.clear()
