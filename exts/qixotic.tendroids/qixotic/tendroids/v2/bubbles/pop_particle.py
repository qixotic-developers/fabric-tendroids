"""
Bubble pop particle spray system (GPU-accelerated)

Handles droplet particles created when bubbles pop.
Physics computed on GPU via Warp kernels.
"""

import carb
from pxr import Gf, UsdGeom

from .pop_particle_gpu_manager import PopParticleGPUManager


class PopParticleVisual:
    """
    USD visual representation for a single particle.
    
    Thin wrapper - only handles prim creation and transform updates.
    Physics handled by GPU manager.
    """
    
    def __init__(self, stage, prim_path: str, position: tuple, radius: float):
        """
        Create particle visual.
        
        Args:
            stage: USD stage
            prim_path: USD path for this particle
            position: Initial (x, y, z) position
            radius: Sphere radius
        """
        self.stage = stage
        self.prim_path = prim_path
        self.prim = None
        self.translate_op = None
        
        self._create_geometry(position, radius)
    
    def _create_geometry(self, position: tuple, radius: float):
        """Create sphere geometry."""
        try:
            # Ensure clean slate
            if self.stage.GetPrimAtPath(self.prim_path):
                self.stage.RemovePrim(self.prim_path)
            
            sphere = UsdGeom.Sphere.Define(self.stage, self.prim_path)
            sphere.GetRadiusAttr().Set(radius)
            
            # Get or create translate op
            existing_ops = sphere.GetOrderedXformOps()
            has_translate = any(
                op.GetOpType() == UsdGeom.XformOp.TypeTranslate 
                for op in existing_ops
            )
            
            if has_translate:
                self.translate_op = sphere.GetTranslateOp()
            else:
                self.translate_op = sphere.AddTranslateOp()
            
            self.translate_op.Set(Gf.Vec3d(*position))
            
            # Simple display appearance
            sphere.CreateDisplayColorAttr([Gf.Vec3f(0.7, 0.9, 1.0)])
            sphere.CreateDisplayOpacityAttr([0.6])
            
            self.prim = sphere.GetPrim()
            
        except Exception as e:
            carb.log_error(f"[PopParticleVisual] Failed to create geometry: {e}")
    
    def update_position(self, position: tuple):
        """Update USD transform."""
        if self.translate_op:
            try:
                self.translate_op.Set(Gf.Vec3d(*position))
            except Exception as e:
                carb.log_error(f"[PopParticleVisual] Transform update failed: {e}")
    
    def destroy(self):
        """Remove from stage."""
        if self.prim and self.stage:
            try:
                self.stage.RemovePrim(self.prim_path)
            except Exception as e:
                carb.log_error(f"[PopParticleVisual] Destroy failed: {e}")
        
        self.prim = None
        self.translate_op = None


class PopParticleManager:
    """
    Manages pop particle creation and lifecycle.
    
    Coordinates between:
    - PopParticleGPUManager: Physics on GPU
    - PopParticleVisual: USD prim management
    """
    
    def __init__(self, stage, config):
        """
        Initialize particle manager.
        
        Args:
            stage: USD stage
            config: BubbleConfig instance
        """
        self.stage = stage
        self.config = config
        
        # GPU physics manager
        self.gpu_manager = PopParticleGPUManager(
            max_particles=config.max_particles,
            device="cuda:0"
        )
        
        # USD visuals indexed by slot
        self.visuals = {}  # slot_index -> PopParticleVisual
        
        # Parent path for organization
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
            bubble_velocity: [vx, vy, vz] bubble's velocity at pop
        """
        if bubble_velocity is None:
            bubble_velocity = [0.0, 0.0, 0.0]
        
        # Check capacity
        if not self.gpu_manager.has_capacity(1):
            return
        
        num_particles = min(
            self.config.particles_per_pop,
            len(self.gpu_manager.free_slots)
        )
        
        if num_particles == 0:
            return
        
        # Spawn on GPU and get assigned slots
        spawned_slots = self.gpu_manager.spawn_spray(
            pop_position=pop_position,
            bubble_velocity=bubble_velocity,
            num_particles=num_particles,
            particle_speed=self.config.particle_speed,
            particle_spread=self.config.particle_spread,
            base_lifetime=self.config.particle_lifetime
        )
        
        # Create USD visuals for spawned particles
        for slot_idx in spawned_slots:
            prim_path = f"{self.parent_path}/particle_{slot_idx:04d}"
            visual = PopParticleVisual(
                stage=self.stage,
                prim_path=prim_path,
                position=pop_position,
                radius=self.config.particle_size
            )
            self.visuals[slot_idx] = visual
    
    def update(self, dt: float):
        """
        Update all particles.
        
        1. Run GPU physics kernel
        2. Update USD transforms from GPU positions
        3. Clean up dead particles
        """
        if not self.visuals:
            return
        
        # Update physics on GPU, get dead particle slots
        dead_slots = self.gpu_manager.update(dt)
        
        # Remove dead visuals
        for slot_idx in dead_slots:
            if slot_idx in self.visuals:
                self.visuals[slot_idx].destroy()
                del self.visuals[slot_idx]
        
        # Batch update USD transforms from GPU positions
        if self.visuals:
            positions = self.gpu_manager.get_active_positions()
            for slot_idx, pos in positions.items():
                if slot_idx in self.visuals:
                    self.visuals[slot_idx].update_position(pos)
    
    def clear_all(self):
        """Remove all particles."""
        # Clear GPU state
        self.gpu_manager.clear_all()
        
        # Destroy all visuals
        for visual in self.visuals.values():
            visual.destroy()
        self.visuals.clear()
    
    def destroy(self):
        """Full cleanup."""
        self.clear_all()
        self.gpu_manager.destroy()
    
    @property
    def particles(self):
        """
        Compatibility property for code expecting particle list.
        
        Returns list of slot indices (not actual particle objects).
        """
        return list(self.visuals.keys())
