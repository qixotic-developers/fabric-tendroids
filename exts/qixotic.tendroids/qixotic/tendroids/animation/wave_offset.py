"""
Wave Offset - The single Python copy of the per-tendroid wave displacement

Pure function, no USD or Warp imports. The GPU kernels keep their own copy of
this formula; the surface parity test guards the two against drifting apart.
"""

import math
from typing import Tuple


def wave_offset(position: Tuple[float, float, float], wave_state: dict) -> Tuple[float, float]:
    """
    Horizontal displacement of a tendroid's tip caused by the wave.

    Args:
        position: Tendroid base world position (x, y, z); only x and z matter
        wave_state: Wave dict with enabled, displacement, amplitude, dir_x, dir_z

    Returns:
        (wave_dx, wave_dz), or (0.0, 0.0) when the wave is disabled
    """
    if not wave_state.get('enabled', False):
        return 0.0, 0.0

    # Slow spatial variation keeps neighbouring tendroids from swaying in lockstep.
    spatial_phase = position[0] * 0.003 + position[2] * 0.002
    spatial_factor = 1.0 + math.sin(spatial_phase) * 0.15
    displacement = wave_state['displacement'] * spatial_factor * wave_state['amplitude']
    return displacement * wave_state['dir_x'], displacement * wave_state['dir_z']
