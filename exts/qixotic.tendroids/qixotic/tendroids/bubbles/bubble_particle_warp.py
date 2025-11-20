"""
Warp-based GPU particle system for bubble pop effects - FIXED VERSION

High-performance particle system using Warp kernels for GPU acceleration.
Replaces sphere-based particles with point cloud rendering.
"""

import carb
import numpy as np
from pxr import Gf, UsdGeom, Sdf
import random
import math

# Try to import warp - handle gracefully if not available
try:
    import warp as wp
    WARP_AVAILABLE = True
except ImportError:
    carb.log_warn("[WarpParticles] Warp module not available - GPU particles disabled")
    WARP_AVAILABLE = False
    wp = None


# Only define kernel if Warp is available
if WARP_AVAILABLE:
    @wp.kernel
    def update_particles_kernel(
        positions: wp.array(dtype=wp.vec3),
        velocities: wp.array(dtype=wp.vec3),
        ages: wp.array(dtype=float),
        lifetimes: wp.array(dtype=float),
        alive_flags: wp.array(dtype=int),
        gravity: float,
        dt: float,
        num_particles: int
    ):
        """GPU kernel to update all particle physics in parallel."""
        tid = wp.tid()
        
        if tid >= num_particles:
            return
        
        # Skip dead particles
        if alive_flags[tid] == 0:
            return
        
        # Update age
        age = ages[tid] + dt
        ages[tid] = age
        
        # Check lifetime
        if age >= lifetimes[tid]:
            alive_flags[tid] = 0
            return
        
        # Apply gravity to velocity
        vel = velocities[tid]
        vel[1] = vel[1] - gravity * dt
        velocities[tid] = vel
        
        # Update position
        pos = positions[tid]
        pos = pos + vel * dt
        positions[tid] = pos


class WarpPopParticleManager:
    """
    GPU-accelerated particle manager using Warp.
    
    Manages particle data on GPU and renders as point cloud.
    Falls back gracefully if Warp is not available.
    """
    
    def __init__(self, stage, config):
        """
        Initialize Warp particle manager.
        
        Args:
            stage: USD stage
            config: BubbleConfig instance
        
        Raises:
            RuntimeError: If Warp is not available
        """
        if not WARP_AVAILABLE:
            raise RuntimeError("Warp module not available for GPU particles")
        
        self.stage = stage
        self.config = config
        self.debug = True  # Enable debug logging
        
        # Particle pool size (pre-allocate for performance)
        self.pool_size = config.max_particles * 2  # Extra headroom
        self.active_count = 0
        self.next_slot = 0
        self.total_created = 0  # Track total particles created
        
        # Initialize Warp and detect device
        try:
            wp.init()
            
            # Try to use CUDA device if available
            if wp.is_cuda_available():
                self.device = "cuda"
                carb.log_info(f"[WarpParticles] Using CUDA GPU acceleration")
            else:
                self.device = "cpu"
                carb.log_warn("[WarpParticles] No CUDA available, using CPU")
                
        except Exception as e:
            # Try alternate initialization
            try:
                wp.init()
                self.device = None  # Let Warp choose
                carb.log_info("[WarpParticles] Initialized with default device")
            except Exception as e2:
                carb.log_error(f"[WarpParticles] Failed to initialize Warp: {e2}")
                raise RuntimeError(f"Failed to initialize Warp: {e2}")
        
        # Allocate arrays on selected device
        try:
            self.positions = wp.zeros(self.pool_size, dtype=wp.vec3, device=self.device)
            self.velocities = wp.zeros(self.pool_size, dtype=wp.vec3, device=self.device)
            self.ages = wp.zeros(self.pool_size, dtype=float, device=self.device)
            self.lifetimes = wp.zeros(self.pool_size, dtype=float, device=self.device)
            self.alive_flags = wp.zeros(self.pool_size, dtype=int, device=self.device)
            
            carb.log_info(f"[WarpParticles] Allocated arrays for {self.pool_size} particles")
            
        except Exception as e:
            carb.log_error(f"[WarpParticles] Failed to allocate arrays: {e}")
            raise RuntimeError(f"Failed to allocate arrays: {e}")
        
        # CPU staging arrays for new particles - these will be batch uploaded
        self.cpu_positions = np.zeros((self.pool_size, 3), dtype=np.float32)
        self.cpu_velocities = np.zeros((self.pool_size, 3), dtype=np.float32)
        self.cpu_ages = np.zeros(self.pool_size, dtype=np.float32)
        self.cpu_lifetimes = np.zeros(self.pool_size, dtype=np.float32)
        self.cpu_alive = np.zeros(self.pool_size, dtype=np.int32)
        
        # Gravity constant
        self.gravity = 5.0  # units/sec^2
        
        # Create point cloud geometry
        self.point_cloud_path = "/World/Bubbles/PopParticleCloud"
        self._create_point_cloud()
        
        carb.log_info(f"[WarpParticles] Initialized successfully with pool size {self.pool_size}")
    
    def _create_point_cloud(self):
        """Create USD point cloud for particle rendering."""
        try:
            # Create points prim
            self.points_prim = UsdGeom.Points.Define(self.stage, self.point_cloud_path)
            
            # Set initial empty positions
            self.points_prim.GetPointsAttr().Set([])
            
            # Make the point cloud visible
            self.points_prim.GetVisibilityAttr().Set("inherited")
            
            # Set larger particle size for visibility
            initial_size = self.config.particle_size * 3.0  # Make bigger for testing
            self.points_prim.GetWidthsAttr().Set([initial_size])
            
            # Create primvar for particle colors/opacity
            primvars = UsdGeom.PrimvarsAPI(self.points_prim)
            
            # Add display color - bright white for maximum visibility
            color_primvar = primvars.CreatePrimvar(
                "displayColor",
                Sdf.ValueTypeNames.Color3fArray,
                UsdGeom.Tokens.vertex
            )
            # Bright white color for maximum visibility
            water_color = Gf.Vec3f(1.0, 1.0, 1.0)
            color_primvar.Set([water_color])
            
            # Add opacity - fully opaque
            opacity_primvar = primvars.CreatePrimvar(
                "displayOpacity",
                Sdf.ValueTypeNames.FloatArray,
                UsdGeom.Tokens.vertex
            )
            opacity_primvar.Set([1.0])  # Fully opaque
            
            carb.log_info(f"[WarpParticles] Created point cloud at {self.point_cloud_path}")
            
            # Verify the prim was created
            if self.stage.GetPrimAtPath(self.point_cloud_path):
                carb.log_info("[WarpParticles] Point cloud prim verified in stage")
            else:
                carb.log_error("[WarpParticles] Point cloud prim NOT found in stage!")
            
        except Exception as e:
            carb.log_error(f"[WarpParticles] Failed to create point cloud: {e}")
    
    def create_pop_spray(self, pop_position: tuple, bubble_velocity: list = None):
        """
        Create spray of particles at pop location.
        
        Args:
            pop_position: (x, y, z) where bubble popped
            bubble_velocity: [vx, vy, vz] bubble's velocity at pop
        """
        if self.debug:
            carb.log_warn(f"[WarpParticles] create_pop_spray called at position {pop_position}")
        
        if bubble_velocity is None:
            bubble_velocity = [0.0, 0.0, 0.0]
        
        # Check if we have room
        if self.active_count >= self.config.max_particles:
            carb.log_warn(f"[WarpParticles] Max particles reached: {self.active_count}/{self.config.max_particles}")
            return
        
        num_particles = min(
            self.config.particles_per_pop,
            self.config.max_particles - self.active_count
        )
        
        if self.debug:
            carb.log_warn(f"[WarpParticles] Creating {num_particles} particles")
        
        # Generate particles on CPU and collect for batch upload
        new_particles = []
        for i in range(num_particles):
            # Find free slot
            slot = self._find_free_slot()
            if slot < 0:
                carb.log_warn("[WarpParticles] No free slots available")
                break
            
            # Random radial velocity with more upward bias
            angle = random.uniform(0, 2 * math.pi)
            elevation = random.uniform(0, 45)  # Upward spray
            
            # Convert to velocity vector
            spray_speed = self.config.particle_speed
            vx = spray_speed * math.cos(angle) * math.cos(math.radians(elevation))
            vy = spray_speed * math.sin(math.radians(elevation)) + 10.0  # Add upward bias
            vz = spray_speed * math.sin(angle) * math.cos(math.radians(elevation))
            
            # Add bubble velocity
            vx += bubble_velocity[0]
            vy += bubble_velocity[1]
            vz += bubble_velocity[2]
            
            # Set particle data in CPU arrays
            self.cpu_positions[slot] = pop_position
            self.cpu_velocities[slot] = [vx, vy, vz]
            self.cpu_ages[slot] = 0.0
            self.cpu_lifetimes[slot] = self.config.particle_lifetime * random.uniform(0.7, 1.3)
            self.cpu_alive[slot] = 1
            
            new_particles.append(slot)
            self.active_count += 1
            self.total_created += 1
        
        # Upload to GPU if we created particles
        if new_particles:
            self._upload_new_particles(new_particles)
            if self.debug:
                carb.log_warn(f"[WarpParticles] Created {len(new_particles)} particles, active: {self.active_count}")
                carb.log_info(f"[WarpParticles] Lifetimes set to ~{self.config.particle_lifetime} seconds")
        else:
            carb.log_error("[WarpParticles] No particles were created!")
    
    def _find_free_slot(self):
        """Find next available particle slot."""
        # Simple round-robin search
        start = self.next_slot
        for i in range(self.pool_size):
            idx = (start + i) % self.pool_size
            if self.cpu_alive[idx] == 0:
                self.next_slot = (idx + 1) % self.pool_size
                return idx
        return -1
    
    def _upload_new_particles(self, slots: list):
        """Upload new particle data to GPU for specific slots only."""
        try:
            # First, download current GPU data to preserve existing particles
            positions_gpu = self.positions.numpy()
            velocities_gpu = self.velocities.numpy()
            ages_gpu = self.ages.numpy()
            lifetimes_gpu = self.lifetimes.numpy()
            alive_gpu = self.alive_flags.numpy()
            
            # Update only the new particle slots
            for slot in slots:
                positions_gpu[slot] = self.cpu_positions[slot]
                velocities_gpu[slot] = self.cpu_velocities[slot]
                ages_gpu[slot] = self.cpu_ages[slot]
                lifetimes_gpu[slot] = self.cpu_lifetimes[slot]
                alive_gpu[slot] = self.cpu_alive[slot]
            
            # Upload the modified arrays back to GPU
            wp.copy(self.positions, wp.from_numpy(positions_gpu.astype(np.float32).reshape(-1, 3), dtype=wp.vec3))
            wp.copy(self.velocities, wp.from_numpy(velocities_gpu.astype(np.float32).reshape(-1, 3), dtype=wp.vec3))
            wp.copy(self.ages, wp.from_numpy(ages_gpu, dtype=float))
            wp.copy(self.lifetimes, wp.from_numpy(lifetimes_gpu, dtype=float))
            wp.copy(self.alive_flags, wp.from_numpy(alive_gpu, dtype=int))
            
            # Synchronize to ensure upload completes
            wp.synchronize()
            
            if self.debug:
                carb.log_info(f"[WarpParticles] Uploaded {len(slots)} new particles to GPU")
                # Verify the upload by checking one particle
                if slots:
                    test_slot = slots[0]
                    carb.log_info(f"[WarpParticles] Slot {test_slot}: lifetime={self.cpu_lifetimes[test_slot]:.2f}s")
                
        except Exception as e:
            carb.log_error(f"[WarpParticles] Failed to upload particles: {e}")
    
    def update(self, dt: float):
        """Update all particles on GPU."""
        if self.active_count == 0:
            return
        
        try:
            # Launch GPU kernel
            wp.launch(
                kernel=update_particles_kernel,
                dim=self.pool_size,
                inputs=[
                    self.positions,
                    self.velocities,
                    self.ages,
                    self.lifetimes,
                    self.alive_flags,
                    self.gravity,
                    dt,
                    self.pool_size
                ],
                device=self.device
            )
            
            # Sync and update render geometry
            self._update_point_cloud()
            
            # Count alive particles periodically
            if random.random() < 0.1:  # Check 10% of frames
                self._count_active_particles()
                
        except Exception as e:
            carb.log_error(f"[WarpParticles] Update failed: {e}")
    
    def _update_point_cloud(self):
        """Update USD point cloud with active particles."""
        try:
            # Synchronize GPU computation
            wp.synchronize()
            
            # Copy GPU data back to CPU for rendering
            positions_cpu = self.positions.numpy()
            alive_cpu = self.alive_flags.numpy()
            ages_cpu = self.ages.numpy()
            lifetimes_cpu = self.lifetimes.numpy()
            
            # Filter active positions and calculate properties
            active_positions = []
            active_sizes = []
            active_colors = []
            active_opacities = []
            
            for i in range(self.pool_size):
                if alive_cpu[i] > 0 and lifetimes_cpu[i] > 0:
                    # Add position
                    active_positions.append(Gf.Vec3f(float(positions_cpu[i][0]), 
                                                    float(positions_cpu[i][1]), 
                                                    float(positions_cpu[i][2])))
                    
                    # Calculate size (shrink over time)
                    age_ratio = ages_cpu[i] / lifetimes_cpu[i] if lifetimes_cpu[i] > 0 else 1.0
                    size = self.config.particle_size * 3.0 * (1.0 - age_ratio * 0.5)
                    active_sizes.append(size)
                    
                    # Color changes over lifetime (white -> cyan -> blue)
                    if age_ratio < 0.3:
                        color = Gf.Vec3f(1.0, 1.0, 1.0)  # White
                    elif age_ratio < 0.7:
                        color = Gf.Vec3f(0.5, 0.8, 1.0)  # Light blue
                    else:
                        color = Gf.Vec3f(0.2, 0.4, 0.8)  # Dark blue
                    active_colors.append(color)
                    
                    # Opacity fades near end
                    opacity = 1.0 if age_ratio < 0.7 else (1.0 - (age_ratio - 0.7) / 0.3)
                    active_opacities.append(opacity)
            
            # Update USD points
            if active_positions:
                self.points_prim.GetPointsAttr().Set(active_positions)
                self.points_prim.GetWidthsAttr().Set(active_sizes)
                
                # Update colors
                primvars = UsdGeom.PrimvarsAPI(self.points_prim)
                color_primvar = primvars.GetPrimvar("displayColor")
                if color_primvar:
                    color_primvar.Set(active_colors)
                
                # Update opacity
                opacity_primvar = primvars.GetPrimvar("displayOpacity")
                if opacity_primvar:
                    opacity_primvar.Set(active_opacities)
                
                # Make sure it's visible
                self.points_prim.GetVisibilityAttr().Set("inherited")
                
                if self.debug and random.random() < 0.05:  # Log 5% of the time
                    carb.log_info(f"[WarpParticles] Rendering {len(active_positions)} particles")
            else:
                # Clear display if no particles
                self.points_prim.GetPointsAttr().Set([])
                if self.debug and self.total_created > 0:
                    carb.log_info("[WarpParticles] No active particles to render")
                
        except Exception as e:
            carb.log_error(f"[WarpParticles] Failed to update point cloud: {e}")
    
    def _count_active_particles(self):
        """Update active particle count."""
        try:
            alive_cpu = self.alive_flags.numpy()
            old_count = self.active_count
            self.active_count = int(np.sum(alive_cpu))
            
            if self.debug and old_count != self.active_count:
                carb.log_info(f"[WarpParticles] Active particle count: {self.active_count}")
            
            # Also update CPU cache for free slot finding
            self.cpu_alive[:] = alive_cpu
            
        except Exception as e:
            carb.log_error(f"[WarpParticles] Failed to count particles: {e}")
    
    def clear_all(self):
        """Clear all particles."""
        try:
            # Zero out GPU arrays
            self.ages.fill_(0.0)
            self.alive_flags.fill_(0)
            
            # Clear CPU cache
            self.cpu_alive.fill(0)
            self.active_count = 0
            self.total_created = 0
            
            # Clear USD display
            self.points_prim.GetPointsAttr().Set([])
            
            if self.debug:
                carb.log_info("[WarpParticles] Cleared all particles")
            
        except Exception as e:
            carb.log_error(f"[WarpParticles] Failed to clear particles: {e}")
    
    def get_particle_count(self) -> int:
        """Get current active particle count."""
        return self.active_count
