"""
Tests for the tendroid surface query and its parity with the Warp deformation kernel.

The parity tests run the real kernel on CPU. They fail, not skip, when Warp is missing.
"""

import ast
import importlib.util
import math
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from qixotic.tendroids.animation.wave_offset import wave_offset
from qixotic.tendroids.contact.tendroid_surface import (
    TendroidShape,
    centerline_point,
    closest_point,
    surface_hit,
)

LENGTH = 100.0
RADIUS = 6.0
KERNEL_PATH = (
    Path(__file__).parent.parent
    / "qixotic" / "tendroids" / "core" / "warp_deflection_deformer.py"
)


def approx3(expected, abs_tol=1e-3):
    return pytest.approx(expected, abs=abs_tol)


# =============================================================================
# WAVE OFFSET
# =============================================================================

class TestWaveOffset:
    WAVE = {'enabled': True, 'displacement': 0.5, 'amplitude': 10.0, 'dir_x': 0.6, 'dir_z': 0.8}

    def test_disabled_wave_is_zero(self):
        assert wave_offset((100.0, 0.0, 50.0), {**self.WAVE, 'enabled': False}) == (0.0, 0.0)

    def test_offset_follows_wave_direction(self):
        dx, dz = wave_offset((0.0, 0.0, 0.0), self.WAVE)
        assert dx == pytest.approx(0.5 * 10.0 * 0.6)
        assert dz == pytest.approx(0.5 * 10.0 * 0.8)

    def test_spatial_variation_depends_on_position(self):
        origin = wave_offset((0.0, 0.0, 0.0), self.WAVE)
        far = wave_offset((300.0, 0.0, 200.0), self.WAVE)
        assert far[0] != pytest.approx(origin[0])


# =============================================================================
# SURFACE QUERY (pure geometry)
# =============================================================================

def test_surface_module_has_no_usd_or_warp_imports():
    source = (KERNEL_PATH.parent.parent / "contact" / "tendroid_surface.py").read_text()
    imported = {
        node.module.split(".")[0] if isinstance(node, ast.ImportFrom) else alias.name.split(".")[0]
        for node in ast.walk(ast.parse(source))
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in (node.names if isinstance(node, ast.Import) else [None])
    }
    assert not imported & {"warp", "pxr", "omni", "carb"}


class TestFlatCase:
    SHAPE = TendroidShape(base=(10.0, 0.0, -5.0), radius=RADIUS, length=LENGTH)

    def test_centerline_is_cylinder_axis(self):
        for height in (0.0, 25.0, 100.0):
            assert centerline_point(self.SHAPE, height) == approx3((10.0, height, -5.0))

    def test_hit_beside_the_cylinder_measures_to_the_wall(self):
        hit = surface_hit(self.SHAPE, (30.0, 40.0, -5.0))
        assert hit.distance == pytest.approx(20.0 - RADIUS, abs=1e-4)
        assert hit.normal == approx3((1.0, 0.0, 0.0))
        assert hit.contact_point == approx3((10.0 + RADIUS, 40.0, -5.0))

    def test_point_inside_has_negative_distance(self):
        assert surface_hit(self.SHAPE, (12.0, 40.0, -5.0)).distance < 0.0


class TestTip:
    def test_query_above_tip_measures_against_the_tip(self):
        shape = TendroidShape(base=(0.0, 0.0, 0.0), radius=RADIUS, length=LENGTH)
        hit = surface_hit(shape, (0.0, LENGTH + 20.0, 0.0))
        assert hit.distance == pytest.approx(20.0 - RADIUS, abs=1e-3)
        assert closest_point(shape, (0.0, LENGTH + 20.0, 0.0)) == approx3((0.0, LENGTH, 0.0))

    def test_query_near_bent_tip_is_not_measured_against_the_base(self):
        shape = TendroidShape(
            base=(0.0, 0.0, 0.0), radius=RADIUS, length=LENGTH,
            deflection_angle=-0.5, deflection_axis=(1.0, 0.0),
        )
        tip = centerline_point(shape, LENGTH)
        probe = (tip[0] + 3.0, tip[1] + 3.0, tip[2])
        assert closest_point(shape, probe) == approx3(tip)


class TestBentAwayFromRestShape:
    def test_point_at_rest_axis_is_clear_once_tendroid_bends_away(self):
        bent = TendroidShape(
            base=(0.0, 0.0, 0.0), radius=RADIUS, length=LENGTH,
            deflection_angle=-0.6, deflection_axis=(1.0, 0.0),
        )
        assert surface_hit(bent, (0.0, 95.0, 0.0)).distance > 0.0


# =============================================================================
# KERNEL PARITY (real Warp, CPU)
# =============================================================================

@pytest.fixture(scope="module")
def kernel():
    """Load the real deflection kernel even if another test module put a mock in sys.modules['warp']."""
    saved = sys.modules.get("warp")
    if isinstance(saved, MagicMock):
        del sys.modules["warp"]
    try:
        try:
            import warp
        except ImportError:
            pytest.fail("Real Warp is required for the kernel parity test: pip install warp-lang")
        if isinstance(warp, MagicMock):
            pytest.fail("Real Warp is required for the kernel parity test, but a mock is installed")

        spec = importlib.util.spec_from_file_location("_parity_warp_deflection_deformer", KERNEL_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.wp_module = warp
        yield module
    finally:
        if saved is not None:
            sys.modules["warp"] = saved


def deform_ring_centers(kernel, heights, angle, axis, wave):
    """Run the real kernel on one ring of vertices per height and return each ring's mean."""
    wp = kernel.wp_module
    ring_size = 12
    points, factors = [], []
    for height in heights:
        ratio = height / LENGTH
        for k in range(ring_size):
            theta = 2.0 * math.pi * k / ring_size
            points.append((RADIUS * math.cos(theta), height, RADIUS * math.sin(theta)))
            factors.append(ratio * ratio * (3.0 - 2.0 * ratio))

    base = wp.array(points, dtype=wp.vec3, device="cpu")
    out = wp.zeros(len(points), dtype=wp.vec3, device="cpu")
    height_factors = wp.array(factors, dtype=float, device="cpu")
    kernel.launch_deflection_deform(
        base, out, height_factors,
        bubble_y=-1000.0, bubble_radius=RADIUS, cylinder_radius=RADIUS, cylinder_length=LENGTH,
        max_amplitude=0.5, bulge_width=1.0,
        wave_dx=wave[0], wave_dz=wave[1],
        deflection_angle=angle, deflection_axis=axis, device="cpu",
    )
    result = out.numpy()
    return [result[i * ring_size:(i + 1) * ring_size].mean(axis=0) for i in range(len(heights))]


@pytest.mark.parametrize("angle", [0.0, 0.3, -0.5, 1.1])
@pytest.mark.parametrize("axis", [(1.0, 0.0), (0.0, 1.0), (-0.6, 0.8)])
@pytest.mark.parametrize("wave", [(0.0, 0.0), (4.0, -2.5)])
def test_centerline_matches_warp_kernel(kernel, angle, axis, wave):
    heights = [0.0, 10.0, 35.0, 60.0, 85.0, 100.0]
    shape = TendroidShape(
        base=(0.0, 0.0, 0.0), radius=RADIUS, length=LENGTH,
        deflection_angle=angle, deflection_axis=axis, wave_offset=wave,
    )
    for height, kernel_center in zip(heights, deform_ring_centers(kernel, heights, angle, axis, wave)):
        assert centerline_point(shape, height) == approx3(tuple(float(c) for c in kernel_center), 1e-3)
