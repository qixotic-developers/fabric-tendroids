"""
Creature Update Helpers - Movement and physics update logic

Separated from CreatureController for maintainability.
Handles physics updates, wave drift, bubble collisions, and tendroid interactions.

Implements movement physics for LTEND-28 integration.
"""

import math
from pxr import Gf


def apply_wave_drift(position: Gf.Vec3f, wave_state: dict, dt: float) -> Gf.Vec3f:
    """
    Apply wave drift to position.
    
    Args:
        position: Current position
        wave_state: Wave controller state dict
        dt: Delta time
    
    Returns:
        Updated position with drift applied
    """
    if not wave_state or not wave_state.get('enabled', False):
        return position
    
    x, y, z = position
    spatial_phase = x * 0.003 + z * 0.002
    spatial_factor = 1.0 + math.sin(spatial_phase) * 0.15
    
    wave_disp = wave_state.get('displacement', 0.0)
    wave_amp = wave_state.get('amplitude', 0.0)
    wave_dir_x = wave_state.get('dir_x', 0.0)
    wave_dir_z = wave_state.get('dir_z', 0.0)
    
    disp = wave_disp * spatial_factor
    drift_speed = 8.0
    
    new_x = x + disp * wave_amp * wave_dir_x * drift_speed * dt
    new_z = z + disp * wave_amp * wave_dir_z * drift_speed * dt
    
    return Gf.Vec3f(new_x, y, new_z)


def clamp_to_bounds(
    position: Gf.Vec3f,
    bounds_min: Gf.Vec3f,
    bounds_max: Gf.Vec3f,
) -> Gf.Vec3f:
    """Clamp position to scene bounds."""
    return Gf.Vec3f(
        max(bounds_min[0], min(bounds_max[0], position[0])),
        max(bounds_min[1], min(bounds_max[1], position[1])),
        max(bounds_min[2], min(bounds_max[2], position[2])),
    )


def check_bubble_collisions(
    position: Gf.Vec3f,
    creature_radius: float,
    bubble_positions: dict,
    bubble_radii: dict,
    velocity: Gf.Vec3f,
) -> tuple:
    """
    Check for bubble collisions and apply impulse.
    
    Returns:
        Tuple of (new_velocity, popped_bubbles_list)
    """
    import carb
    
    popped = []
    new_velocity = Gf.Vec3f(velocity[0], velocity[1], velocity[2])
    
    if not bubble_positions or not bubble_radii:
        return new_velocity, popped
    
    for tendroid_name, bubble_pos in bubble_positions.items():
        bubble_radius = bubble_radii.get(tendroid_name, 0.0)
        if bubble_radius <= 0.0:
            continue
        
        bubble_vec = Gf.Vec3f(
            float(bubble_pos[0]),
            float(bubble_pos[1]),
            float(bubble_pos[2])
        )
        distance_vec = position - bubble_vec
        distance = distance_vec.GetLength()
        
        collision_distance = (creature_radius + bubble_radius) * 0.9
        if distance < collision_distance:
            if distance > 0.01:
                collision_dir = distance_vec / distance
            else:
                collision_dir = Gf.Vec3f(0, 1, 0)
            
            bubble_impulse = 5.0
            new_velocity += collision_dir * bubble_impulse
            popped.append((tendroid_name, collision_dir))
            
            carb.log_info(f"[Creature] Bubble collision at {tendroid_name}")
    
    return new_velocity, popped


def check_tendroid_interactions(
    position: Gf.Vec3f,
    velocity: Gf.Vec3f,
    creature_radius: float,
    tendroids: list,
) -> tuple:
    """
    Check for tendroid avoidance and shock interactions.
    
    Returns:
        Tuple of (new_velocity, interactions_dict)
    """
    import carb
    
    interactions = {}
    new_velocity = Gf.Vec3f(velocity[0], velocity[1], velocity[2])
    
    if not tendroids:
        return new_velocity, interactions
    
    avoidance_epsilon = 30.0
    shock_impulse = 25.0
    
    for tendroid in tendroids:
        tendroid_pos = Gf.Vec3f(*tendroid.position)
        distance_vec = position - tendroid_pos
        distance = distance_vec.GetLength()
        
        if distance > avoidance_epsilon:
            continue
        
        if distance > 0.01:
            direction_to_tendroid = -distance_vec / distance
            approach_velocity = velocity.GetDot(direction_to_tendroid)
        else:
            approach_velocity = 0.0
        
        if approach_velocity > 0.1:
            contact_distance = creature_radius + tendroid.radius
            if distance > contact_distance:
                avoidance_factor = 1.0 - (
                    (distance - contact_distance) /
                    (avoidance_epsilon - contact_distance)
                )
                avoidance_factor = max(0.0, min(1.0, avoidance_factor))
                
                avoidance_dir = distance_vec / distance
                interactions[tendroid.name] = {
                    'type': 'avoidance',
                    'distance': distance,
                    'approach_velocity': approach_velocity,
                    'avoidance_factor': avoidance_factor,
                    'avoidance_direction': tuple(avoidance_dir),
                }
            else:
                shock_dir = distance_vec / distance if distance > 0.01 else Gf.Vec3f(0, 1, 0)
                new_velocity += shock_dir * shock_impulse
                
                interactions[tendroid.name] = {
                    'type': 'shock',
                    'distance': distance,
                    'shock_direction': tuple(shock_dir),
                }
                carb.log_info(f"[Creature] Shocked by {tendroid.name}!")
    
    return new_velocity, interactions


def calculate_rotation(
    intended_velocity: Gf.Vec3f,
    current_rotation: Gf.Vec3f,
    lerp_factor: float = 0.2,
) -> Gf.Vec3f:
    """
    Calculate smooth rotation toward intended velocity direction.
    
    Args:
        intended_velocity: Velocity from keyboard input
        current_rotation: Current rotation angles
        lerp_factor: Smoothing factor
    
    Returns:
        New rotation angles
    """
    if intended_velocity.GetLength() <= 1.0:
        return current_rotation
    
    vx, vy, vz = intended_velocity[0], intended_velocity[1], intended_velocity[2]
    
    # Yaw
    target_yaw = 90.0 - math.degrees(math.atan2(vz, vx))
    
    # Pitch
    horizontal_dist = math.sqrt(vx*vx + vz*vz)
    current_yaw = current_rotation[1]
    current_pitch = current_rotation[0]
    
    if horizontal_dist > 0.01:
        target_pitch = -math.degrees(math.atan2(vy, horizontal_dist))
    elif abs(vy) > 0.01:
        target_pitch = -90.0 if vy > 0 else 90.0
    else:
        target_pitch = current_pitch
    
    # Handle yaw wraparound
    yaw_diff = target_yaw - current_yaw
    if yaw_diff > 180:
        yaw_diff -= 360
    elif yaw_diff < -180:
        yaw_diff += 360
    
    new_yaw = current_yaw + yaw_diff * lerp_factor
    new_pitch = current_pitch + (target_pitch - current_pitch) * lerp_factor
    
    return Gf.Vec3f(new_pitch, new_yaw, 0)
