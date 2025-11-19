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
    self.gravity = -20.0  # units/sec^2
    
    # Lifecycle
    self.age = 0.0
    self.is_alive = True
    
    # USD prim
    self.prim = None
    
    # Create geometry
    self._create_geometry()
  
  def _create_geometry(self):
    """Create small sphere for droplet."""
    try:
      sphere = UsdGeom.Sphere.Define(self.stage, self.prim_path)
      sphere.GetRadiusAttr().Set(self.config.particle_size)
      
      # Set initial position
      sphere.AddTranslateOp().Set(Gf.Vec3d(*self.position))
      
      # Apply water material (slightly opaque)
      self._apply_water_material(sphere.GetPrim())
      
      self.prim = sphere.GetPrim()
      
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
    
    # Check lifetime
    if self.age >= self.config.particle_lifetime:
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
  
  def create_pop_spray(self, pop_position: tuple):
    """
    Create spray of particles at pop location.
    
    Args:
        pop_position: (x, y, z) where bubble popped
    """
    # Check particle limit
    if len(self.particles) >= self.config.max_particles:
      return
    
    num_particles = min(
      self.config.particles_per_pop,
      self.config.max_particles - len(self.particles)
    )
    
    for i in range(num_particles):
      self._create_particle(pop_position)
  
  def _create_particle(self, pop_position: tuple):
    """Create single spray particle."""
    self.particle_counter += 1
    particle_id = f"pop_particle_{self.particle_counter:05d}"
    prim_path = f"{self.parent_path}/{particle_id}"
    
    # Random radial velocity with upward bias
    angle = random.uniform(0, 2 * math.pi)
    elevation = random.uniform(
      -self.config.particle_spread / 2,
      self.config.particle_spread
    )
    
    # Convert to velocity vector
    speed = self.config.particle_speed
    vx = speed * math.cos(angle) * math.cos(math.radians(elevation))
    vy = speed * math.sin(math.radians(elevation))
    vz = speed * math.sin(angle) * math.cos(math.radians(elevation))
    
    particle = PopParticle(
      particle_id=particle_id,
      pop_position=pop_position,
      velocity=(vx, vy, vz),
      config=self.config,
      stage=self.stage,
      prim_path=prim_path
    )
    
    self.particles.append(particle)
  
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
