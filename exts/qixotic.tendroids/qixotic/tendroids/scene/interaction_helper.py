"""
Tendroid-Creature Interaction Helper - Phase 1 Step 3 Fixes (v4)

FIXES:
1. Bubble suppression now actually blocks bubble creation
2. Repulsion direction CORRECTED (was still inverted)
3. Much stronger repulsion to prevent fast penetration
4. Velocity damping on contact for instant stop
5. Y-extent check - creature must vertically overlap tendroid
6. Contact uses bent tip position, not base position
"""

from pxr import Gf
import carb
import math


class TendroidCreatureInteraction:
    """
    Manages interaction state and physics between tendroids and creature.
    """
    
    def __init__(self):
        # Configuration parameters
        self.detection_start_distance = 50.0  # When tendroid first detects creature
        self.shock_impulse = 25.0  # Pushback strength
        self.shock_cooldown = 1.5  # Seconds between shocks
        self.shock_duration = 0.3  # Visual flash duration
        
        # Avoidance tuning
        self.avoidance_speed = 30.0  # Base bend rate (degrees/sec)
        self.avoidance_acceleration = 2.0  # Multiplier when creature approaching fast
        
        # Repulsion force - MUCH stronger to prevent penetration
        self.repulsion_strength = 500.0  # Force when penetrating (was 100, now 500!)
        self.repulsion_range = 2.0  # Start repulsion this many units before contact
        self.velocity_damping = 0.5  # Reduce velocity on contact (0.5 = half speed)
        
    def update_interaction(
        self,
        tendroid,
        creature_pos: Gf.Vec3f,
        creature_vel: Gf.Vec3f,
        creature_radius: float,
        creature_length: float,
        dt: float,
        gpu_bubble_adapter=None
    ) -> dict:
        """
        Update single tendroid's interaction with creature.
        
        Returns:
            dict with keys:
                - repulsion_force: Gf.Vec3f to apply to creature
                - shock_triggered: bool
                - bubble_suppressed: bool
                - suppress_bubble_id: str (tendroid name if suppressing)
        """
        result = {
            'repulsion_force': Gf.Vec3f(0, 0, 0),
            'shock_triggered': False,
            'bubble_suppressed': False,
            'suppress_bubble_id': None
        }
        
        # FIX #2: Check Y-extent overlap first
        # Creature must be vertically within tendroid's extent to interact
        tendroid_pos = Gf.Vec3f(*tendroid.position)
        tendroid_bottom = tendroid_pos[1]
        tendroid_top = tendroid_pos[1] + tendroid.length
        
        # Creature vertical extent (cylinder oriented along velocity)
        creature_bottom = creature_pos[1] - creature_length / 2.0
        creature_top = creature_pos[1] + creature_length / 2.0
        
        # Check for vertical overlap
        if creature_top < tendroid_bottom or creature_bottom > tendroid_top:
            # No vertical overlap - creature is above or below tendroid
            # Natural recovery if was previously interacting
            if tendroid.avoidance_angle > 0.0:
                tendroid.avoidance_angle = max(
                    0.0,
                    tendroid.avoidance_angle - tendroid.avoidance_recovery_rate * dt
                )
            return result
        
        # Calculate horizontal distance from creature CENTER to tendroid BASE
        dx = creature_pos[0] - tendroid_pos[0]
        dz = creature_pos[2] - tendroid_pos[2]
        distance_to_base = (dx * dx + dz * dz) ** 0.5
        
        # Check if within interaction zone (based on base position)
        if distance_to_base > self.detection_start_distance:
            # Too far - natural recovery
            if tendroid.avoidance_angle > 0.0:
                tendroid.avoidance_angle = max(
                    0.0,
                    tendroid.avoidance_angle - tendroid.avoidance_recovery_rate * dt
                )
            return result
        
        # Within interaction zone - suppress bubble activity
        result['bubble_suppressed'] = True
        result['suppress_bubble_id'] = tendroid.name
        
        # Pop existing bubble on first entry to interaction zone
        if tendroid.avoidance_angle == 0.0 and gpu_bubble_adapter:
            gpu_bubble_adapter.pop_bubble(tendroid.name)
            carb.log_info(
                f"[Interaction] {tendroid.name} suppressed bubble "
                f"(creature within {distance_to_base:.1f} units, Y overlap)"
            )
        
        # Calculate horizontal direction FROM tendroid TO creature
        if distance_to_base > 0.01:
            # Direction vector points from tendroid toward creature
            horiz_dir_x = dx / distance_to_base
            horiz_dir_z = dz / distance_to_base
        else:
            horiz_dir_x, horiz_dir_z = 1.0, 0.0
        
        # Calculate approach velocity (how fast creature is approaching)
        if distance_to_base > 0.01:
            # Project velocity onto direction: positive = approaching, negative = retreating
            approach_velocity = (creature_vel[0] * horiz_dir_x + creature_vel[2] * horiz_dir_z)
        else:
            approach_velocity = 0.0
        
        # Contact distance (where surfaces touch at BASE)
        contact_distance = creature_radius + tendroid.radius
        
        # Calculate target avoidance angle based on proximity TO BASE
        if distance_to_base >= self.detection_start_distance:
            closeness_factor = 0.0
        elif distance_to_base <= contact_distance:
            closeness_factor = 1.0
        else:
            # Linear interpolation between detection and contact
            closeness_factor = 1.0 - ((distance_to_base - contact_distance) / 
                                      (self.detection_start_distance - contact_distance))
        
        target_angle = closeness_factor * tendroid.max_avoidance_angle
        
        # Calculate bend rate - faster when creature approaching quickly
        base_rate = self.avoidance_speed
        if approach_velocity > 0:  # Approaching
            bend_rate = base_rate + approach_velocity * self.avoidance_acceleration
        else:  # Retreating or stationary
            bend_rate = base_rate
        
        # Update avoidance angle toward target
        angle_error = target_angle - tendroid.avoidance_angle
        
        if abs(angle_error) < 0.1:
            tendroid.avoidance_angle = target_angle
        elif angle_error > 0:
            tendroid.avoidance_angle = min(target_angle, tendroid.avoidance_angle + bend_rate * dt)
        else:
            tendroid.avoidance_angle = max(target_angle, tendroid.avoidance_angle - bend_rate * dt)
        
        # Direction to lean (AWAY from creature - negate the direction TO creature)
        tendroid.avoidance_dir_x = -horiz_dir_x
        tendroid.avoidance_dir_z = -horiz_dir_z
        
        # FIX #1: Calculate bent TIP position for contact detection
        # When tendroid bends at angle θ away from creature, tip moves horizontally
        angle_rad = math.radians(tendroid.avoidance_angle)
        
        # Tip offset in the AWAY direction (negative of creature direction)
        tip_offset_x = tendroid.length * math.sin(angle_rad) * (-horiz_dir_x)
        tip_offset_z = tendroid.length * math.sin(angle_rad) * (-horiz_dir_z)
        
        # Bent tip position
        tip_x = tendroid_pos[0] + tip_offset_x
        tip_z = tendroid_pos[2] + tip_offset_z
        
        # Distance from creature to bent TIP (for contact detection)
        dx_tip = creature_pos[0] - tip_x
        dz_tip = creature_pos[2] - tip_z
        distance_to_tip = (dx_tip * dx_tip + dz_tip * dz_tip) ** 0.5
        
        # Log avoidance state (throttled)
        if self._should_log_avoidance(tendroid):
            carb.log_info(
                f"[Avoidance] {tendroid.name}: base_dist={distance_to_base:.1f}, "
                f"tip_dist={distance_to_tip:.1f}, "
                f"target={target_angle:.1f}°, current={tendroid.avoidance_angle:.1f}°, "
                f"approach_vel={approach_velocity:.1f}"
            )
        
        # Check for contact/penetration using TIP distance
        repulsion_start_distance = contact_distance + self.repulsion_range
        
        if distance_to_tip <= repulsion_start_distance:
            # CONTACT ZONE - Apply repulsion based on TIP position
            
            # Calculate how deep into repulsion zone
            repulsion_depth = repulsion_start_distance - distance_to_tip
            
            # Repulsion force scales linearly from 0 at edge to max at full penetration
            if repulsion_depth > 0:
                # Scale force: 0% at edge, 100% at full repulsion_range penetration
                force_factor = min(1.0, repulsion_depth / self.repulsion_range)
                repulsion_magnitude = self.repulsion_strength * force_factor
                
                # Direction FROM TIP TO creature (push away from tip)
                if distance_to_tip > 0.01:
                    tip_dir_x = dx_tip / distance_to_tip
                    tip_dir_z = dz_tip / distance_to_tip
                else:
                    tip_dir_x, tip_dir_z = horiz_dir_x, horiz_dir_z
                
                # Push creature AWAY from bent tip
                repulsion_dir = Gf.Vec3f(tip_dir_x, 0.0, tip_dir_z)
                result['repulsion_force'] = repulsion_dir * repulsion_magnitude
                
                # If actually penetrating (past contact distance), apply velocity damping
                if distance_to_tip < contact_distance:
                    penetration = contact_distance - distance_to_tip
                    # Damp velocity in the direction toward tip
                    vel_toward_tip = -(creature_vel[0] * tip_dir_x + creature_vel[2] * tip_dir_z)
                    vel_toward_tip = max(0.0, vel_toward_tip)  # Only damp if moving toward
                    
                    if vel_toward_tip > 0:
                        # Reduce velocity component toward tip
                        damping_force = Gf.Vec3f(-tip_dir_x, 0.0, -tip_dir_z) * vel_toward_tip * self.velocity_damping
                        result['repulsion_force'] += damping_force
                    
                    carb.log_info(
                        f"[Penetration] {tendroid.name}: depth={penetration:.1f}, "
                        f"repulsion={repulsion_magnitude:.1f}, "
                        f"tip_pos=({tip_x:.1f}, {tip_z:.1f}), "
                        f"dir=({tip_dir_x:.2f}, 0, {tip_dir_z:.2f}), "
                        f"damping={vel_toward_tip:.1f}"
                    )
            
            # Shock effect (only if cooldown expired and actually touching TIP)
            if distance_to_tip <= contact_distance and tendroid.can_shock():
                result['shock_triggered'] = True
                tendroid.shock_cooldown_timer = self.shock_cooldown
                
                carb.log_info(
                    f"[Shock] {tendroid.name} shocked creature! "
                    f"(tip_distance: {distance_to_tip:.1f}, contact: {contact_distance:.1f})"
                )
        
        return result
    
    def _should_log_avoidance(self, tendroid) -> bool:
        """Throttle avoidance logging to avoid spam."""
        if not hasattr(self, '_log_counters'):
            self._log_counters = {}
        
        if tendroid.name not in self._log_counters:
            self._log_counters[tendroid.name] = 0
        
        self._log_counters[tendroid.name] += 1
        
        # Log every 30 frames (roughly 0.5 seconds at 60fps)
        if self._log_counters[tendroid.name] >= 30:
            self._log_counters[tendroid.name] = 0
            return True
        
        return False
