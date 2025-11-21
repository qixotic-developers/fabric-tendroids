"""
Enhanced bubble manager with Warp GPU particle option

Supports both sphere-based and Warp-based particle systems.
"""

import carb
from .bubble import Bubble
from .bubble_config import BubbleConfig, DEFAULT_BUBBLE_CONFIG
from .bubble_helpers import create_bubble_sphere
from .deformation_tracker import DeformationWaveTracker
from .bubble_particle import PopParticleManager
from .bubble_particle_warp import WarpPopParticleManager


class BubbleManagerEnhanced:
    """
    Bubble manager with switchable particle system.
    
    Can use either:
    - Sphere-based particles (original)
    - Warp GPU-based particles (new, faster)
    """
    
    def __init__(self, stage, config: BubbleConfig = None, use_warp_particles: bool = True):
        """
        Initialize bubble manager.
        
        Args:
            stage: USD stage
            config: BubbleConfig instance (uses default if None)
            use_warp_particles: Use GPU-accelerated Warp particles if True
        """
        self.stage = stage
        self.config = config or DEFAULT_BUBBLE_CONFIG
        self.use_warp_particles = use_warp_particles
        
        # Track bubbles and wave state per tendroid
        self.bubbles = {}  # {tendroid_name: [Bubble, ...]}
        self.wave_trackers = {}  # {tendroid_name: DeformationWaveTracker}
        self.bubble_spawned_this_cycle = {}  # {tendroid_name: bool}
        self.tendroid_positions = {}  # {tendroid_name: (x, y, z)}
        
        self.bubble_counter = 0
        
        # Create appropriate particle manager
        if use_warp_particles:
            try:
                self.particle_manager = WarpPopParticleManager(stage, config)
                carb.log_info("[BubbleManagerEnhanced] Using Warp GPU particles")
            except Exception as e:
                carb.log_error(f"[BubbleManagerEnhanced] Failed to init Warp particles: {e}")
                carb.log_warn("[BubbleManagerEnhanced] Falling back to sphere particles")
                self.particle_manager = PopParticleManager(stage, config)
                self.use_warp_particles = False
        else:
            self.particle_manager = PopParticleManager(stage, config)
            carb.log_info("[BubbleManagerEnhanced] Using sphere-based particles")
        
        # Parent path for bubble prims
        self.bubble_parent_path = "/World/Bubbles"
        self._ensure_bubble_parent()
    
    def _ensure_bubble_parent(self):
        """Create /World/Bubbles parent if needed."""
        if not self.stage.GetPrimAtPath(self.bubble_parent_path):
            from pxr import UsdGeom
            UsdGeom.Scope.Define(self.stage, self.bubble_parent_path)
    
    def register_tendroid(
        self,
        tendroid_name: str,
        cylinder_length: float,
        deform_start_height: float,
        position: tuple = (0, 0, 0)
    ):
        """
        Register tendroid for bubble tracking.
        
        Args:
            tendroid_name: Unique tendroid identifier
            cylinder_length: Total cylinder length
            deform_start_height: Y position where deformation begins
            position: (x, y, z) world position of tendroid base
        """
        if tendroid_name not in self.wave_trackers:
            self.wave_trackers[tendroid_name] = DeformationWaveTracker(
                cylinder_length=cylinder_length,
                deform_start_height=deform_start_height
            )
            self.bubbles[tendroid_name] = []
            self.bubble_spawned_this_cycle[tendroid_name] = False
            self.tendroid_positions[tendroid_name] = position
    
    def update_tendroid_wave(
        self,
        tendroid_name: str,
        wave_params: dict,
        base_radius: float,
        wave_speed: float,
        top_position: tuple = None
    ):
        """
        Update deformation wave state for tendroid.
        
        Called each frame by tendroid to provide wave data.
        
        Args:
            tendroid_name: Tendroid identifier
            wave_params: Dict from BreathingAnimator.update()
            base_radius: Cylinder base radius
            wave_speed: Deformation wave speed
            top_position: Optional (x, y, z) of tendroid top including wave displacement
        """
        if tendroid_name not in self.wave_trackers:
            return
        
        tracker = self.wave_trackers[tendroid_name]
        
        # Store base position if not already stored
        if tendroid_name not in self.tendroid_positions:
            # Calculate base from top position and cylinder length
            if top_position:
                base_y = top_position[1] - tracker.cylinder_length
                self.tendroid_positions[tendroid_name] = (top_position[0], base_y, top_position[2])
            else:
                self.tendroid_positions[tendroid_name] = (0.0, 0.0, 0.0)
        
        # Store top position for tilt calculations
        if top_position:
            if not hasattr(self, 'tendroid_top_positions'):
                self.tendroid_top_positions = {}
            self.tendroid_top_positions[tendroid_name] = top_position
        
        tracker.update(wave_params, base_radius)
        
        # Calculate tilt factor for adaptive bubble sizing
        tilt_factor = 0.0
        if hasattr(self, 'tendroid_top_positions') and tendroid_name in self.tendroid_top_positions:
            base_pos = self.tendroid_positions.get(tendroid_name, (0.0, 0.0, 0.0))
            top_pos = self.tendroid_top_positions[tendroid_name]
            tilt_dx = top_pos[0] - base_pos[0]
            tilt_dz = top_pos[2] - base_pos[2]
            tilt_magnitude = (tilt_dx * tilt_dx + tilt_dz * tilt_dz) ** 0.5
            max_expected_tilt = 20.0
            tilt_factor = min(tilt_magnitude / max_expected_tilt, 1.0)
        
        # Check for bubble spawn with tilt-adapted sizing
        should_spawn, spawn_y, initial_diameter = tracker.should_spawn_bubble(tilt_factor)
        
        if should_spawn and not self.bubble_spawned_this_cycle[tendroid_name]:
            # Calculate spawn position along tilted axis
            spawn_position = self._calculate_tilted_position(
                tendroid_name, spawn_y, tracker.cylinder_length
            )
            
            self._spawn_bubble_at_position(
                tendroid_name=tendroid_name,
                spawn_position=spawn_position,
                initial_diameter=initial_diameter,
                wave_speed=wave_speed,
                base_radius=base_radius
            )
            self.bubble_spawned_this_cycle[tendroid_name] = True
        
        # Reset spawn flag when wave becomes inactive
        if not wave_params['active']:
            self.bubble_spawned_this_cycle[tendroid_name] = False
        
        # Update locked bubbles with current mouth position
        self._update_locked_bubbles(tendroid_name, tracker, base_radius, top_position)
    
    def _calculate_tilted_position(self, tendroid_name: str, spawn_y: float, cylinder_length: float) -> tuple:
        """
        Calculate spawn position along tilted cylinder axis.
        Returns the TRUE center of the deformed cylinder at the given height,
        with a small safety offset when heavily tilted.
        
        Args:
            tendroid_name: Tendroid identifier
            spawn_y: Y coordinate for spawn
            cylinder_length: Total cylinder length
            
        Returns:
            (x, y, z) position along tilted centerline with safety offset
        """
        base_pos = self.tendroid_positions.get(tendroid_name, (0.0, 0.0, 0.0))
        
        if hasattr(self, 'tendroid_top_positions') and tendroid_name in self.tendroid_top_positions:
            top_pos = self.tendroid_top_positions[tendroid_name]
            
            # Calculate height ratio (0.0 at base, 1.0 at top)
            base_y = base_pos[1] if len(base_pos) > 1 else 0.0
            height_from_base = spawn_y - base_y
            height_ratio = height_from_base / cylinder_length if cylinder_length > 0 else 0.8
            height_ratio = max(0.0, min(1.0, height_ratio))
            
            # Use cubic curve for realistic bending (matches wave controller)
            height_factor = height_ratio * height_ratio * (3.0 - 2.0 * height_ratio)
            
            # Calculate TRUE centerline position at this height
            center_x = base_pos[0] + (top_pos[0] - base_pos[0]) * height_factor
            center_z = base_pos[2] + (top_pos[2] - base_pos[2]) * height_factor
            
            # Calculate tilt amount for safety offset
            tilt_dx = top_pos[0] - base_pos[0]
            tilt_dz = top_pos[2] - base_pos[2]
            tilt_magnitude = (tilt_dx * tilt_dx + tilt_dz * tilt_dz) ** 0.5
            
            # Apply small safety offset when heavily tilted
            # The more tilt, the more we need to compensate for elliptical cross-section
            if tilt_magnitude > 1.0:  # Only apply safety offset for significant tilt
                # Normalize tilt direction
                tilt_dir_x = tilt_dx / tilt_magnitude if tilt_magnitude > 0 else 0
                tilt_dir_z = tilt_dz / tilt_magnitude if tilt_magnitude > 0 else 0
                
                # Calculate tilt angle effect (0 to 1 based on tilt amount)
                # More tilt = more offset needed
                max_expected_tilt = 20.0  # Maximum expected displacement
                tilt_factor = min(tilt_magnitude / max_expected_tilt, 1.0)
                
                # Get cylinder radius for offset calculation
                tracker = self.wave_trackers.get(tendroid_name)
                if tracker:
                    cylinder_radius = tracker.base_radius
                    # Offset increases with both tilt and height
                    # Maximum offset is 15% of radius at maximum tilt and height
                    offset_amount = cylinder_radius * 0.15 * tilt_factor * height_factor
                    
                    # Apply offset OPPOSITE to tilt direction (push bubble back)
                    x = center_x - tilt_dir_x * offset_amount
                    z = center_z - tilt_dir_z * offset_amount
                else:
                    x = center_x
                    z = center_z
            else:
                # Minimal tilt, use centerline position
                x = center_x
                z = center_z
            
            return (x, spawn_y, z)
        else:
            # Fallback to vertical position if no tilt data
            return (base_pos[0], spawn_y, base_pos[2])
    
    def _spawn_bubble_at_position(
        self,
        tendroid_name: str,
        spawn_position: tuple,
        initial_diameter: float,
        wave_speed: float,
        base_radius: float
    ):
        """Create new bubble at calculated position."""
        # Check bubble limit
        active_count = len([b for b in self.bubbles[tendroid_name] if b.is_alive])
        if active_count >= self.config.max_bubbles_per_tendroid:
            return
        
        # Create bubble instance
        self.bubble_counter += 1
        bubble_id = f"bubble_{tendroid_name}_{self.bubble_counter:04d}"
        
        bubble = Bubble(
            bubble_id=bubble_id,
            initial_position=spawn_position,
            initial_diameter=initial_diameter,
            deform_wave_speed=wave_speed,
            base_radius=base_radius,
            config=self.config,
            stage=self.stage
        )
        
        # Create USD geometry
        prim_path = f"{self.bubble_parent_path}/{bubble_id}"
        success = create_bubble_sphere(
            stage=self.stage,
            prim_path=prim_path,
            position=spawn_position,
            diameter=initial_diameter,
            resolution=self.config.resolution,
            config=self.config
        )
        
        if success:
            bubble.prim_path = prim_path
            bubble.prim = self.stage.GetPrimAtPath(prim_path)
            self.bubbles[tendroid_name].append(bubble)
    
    def _update_locked_bubbles(self, tendroid_name: str, tracker, base_radius: float, top_position: tuple = None):
        """Update bubbles in locked phase and detect pops."""
        popped_bubbles = []
        
        for bubble in self.bubbles[tendroid_name]:
            if bubble.is_locked():
                # Calculate diameter at bubble's BOTTOM position
                bubble_center_y = bubble.physics.position[1]
                bubble_radius = bubble.physics.diameter / 2.0
                vertical_stretch = bubble.physics.vertical_stretch
                bubble_bottom_y = bubble_center_y - (bubble_radius * vertical_stretch)
                
                # Get target diameter at bubble BOTTOM
                target_diameter = tracker.get_deformation_at_height(bubble_bottom_y, base_radius) * 2.0
                
                # Apply diameter multiplier
                target_diameter *= self.config.diameter_multiplier
                
                # Calculate bubble's position along tilted centerline
                bubble_position = None
                if top_position:
                    # Calculate where bubble should be based on its Y position
                    bubble_tilted_pos = self._calculate_tilted_position(
                        tendroid_name, bubble_center_y, tracker.cylinder_length
                    )
                    bubble_position = bubble_tilted_pos
                
                # Update bubble with deformation center, target diameter, and calculated position
                bubble.update_locked(
                    dt=1.0/60.0,
                    deform_center_y=tracker.wave_center,
                    deform_radius=target_diameter / 2.0,
                    mouth_position=bubble_position  # Pass bubble's actual position on tilted centerline
                )
                
                # Check if bubble popped during update
                if bubble.has_popped:
                    popped_bubbles.append(bubble)
                
                # Check if bubble should be released
                bubble_radius = bubble.physics.get_radius()
                if tracker.should_release_bubble(bubble.physics.position[1], bubble_radius):
                    bubble.release()
        
        # Handle popped bubbles
        for bubble in popped_bubbles:
            self._handle_bubble_pop(bubble)
    
    def _handle_bubble_pop(self, bubble: Bubble):
        """Handle bubble pop event - create particle spray."""
        pop_position = bubble.get_pop_position()
        bubble_velocity = bubble.physics.velocity
        
        # Create particle spray at pop location
        self.particle_manager.create_pop_spray(pop_position, bubble_velocity)
    
    def update(self, dt: float, wave_controller=None):
        """
        Update all bubbles and particles.
        
        Args:
            dt: Delta time (seconds)
            wave_controller: Optional wave controller for synchronized drift
        """
        popped_bubbles = []
        
        for tendroid_name in list(self.bubbles.keys()):
            bubbles = self.bubbles[tendroid_name]
            
            # Update released bubbles with wave effects
            for i, bubble in enumerate(bubbles):
                if bubble.is_released():
                    # Pass wave controller and unique ID for phase variation
                    bubble.update_released(dt, wave_controller, bubble_id=i)
                    
                    # Check if bubble popped
                    if bubble.has_popped:
                        popped_bubbles.append(bubble)
            
            # Remove dead bubbles
            dead_bubbles = [b for b in bubbles if not b.is_alive]
            for bubble in dead_bubbles:
                bubble.destroy()
                bubbles.remove(bubble)
        
        # Handle any pops that occurred
        for bubble in popped_bubbles:
            self._handle_bubble_pop(bubble)
        
        # Update pop particles
        self.particle_manager.update(dt)
    
    def clear_tendroid_bubbles(self, tendroid_name: str):
        """Remove all bubbles for a specific tendroid."""
        if tendroid_name in self.bubbles:
            for bubble in self.bubbles[tendroid_name]:
                bubble.destroy()
            del self.bubbles[tendroid_name]
            
            if tendroid_name in self.wave_trackers:
                del self.wave_trackers[tendroid_name]
            
            if tendroid_name in self.bubble_spawned_this_cycle:
                del self.bubble_spawned_this_cycle[tendroid_name]
            
            if tendroid_name in self.tendroid_positions:
                del self.tendroid_positions[tendroid_name]
    
    def clear_all_bubbles(self):
        """Remove all bubbles from all tendroids and all particles."""
        for tendroid_name in list(self.bubbles.keys()):
            self.clear_tendroid_bubbles(tendroid_name)
        
        # Clear all pop particles
        self.particle_manager.clear_all()
    
    def get_bubble_count(self, tendroid_name: str = None) -> int:
        """Get bubble count."""
        if tendroid_name:
            if tendroid_name in self.bubbles:
                return len([b for b in self.bubbles[tendroid_name] if b.is_alive])
            return 0
        
        # Total across all tendroids
        total = 0
        for bubbles in self.bubbles.values():
            total += len([b for b in bubbles if b.is_alive])
        return total
    
    def get_particle_count(self) -> int:
        """Get count of active pop particles."""
        if hasattr(self.particle_manager, 'get_particle_count'):
            return self.particle_manager.get_particle_count()
        return len(self.particle_manager.particles)
    
    def get_particle_system_type(self) -> str:
        """Get which particle system is being used."""
        return "Warp GPU" if self.use_warp_particles else "Sphere-based"
