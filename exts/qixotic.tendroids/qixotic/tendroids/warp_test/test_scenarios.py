"""
Test Scenarios

Defines the test phases with increasing complexity.
Each phase tests specific aspects of Warp memory behavior.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TestPhase(Enum):
    """Test phase identifiers"""
    PHASE_1 = 1  # Single cylinder, sine wave
    PHASE_2 = 2  # Multiple cylinders, varied frequencies
    PHASE_3 = 3  # Materials, opacity, path tracing
    PHASE_6A = 6  # Static double-wall glass (no deformation)


@dataclass
class TestScenario:
    """Configuration for a test scenario"""
    phase: TestPhase
    name: str
    description: str
    cylinder_count: int
    segments: int
    radial_segments: int
    kernel_type: str
    max_frames: int
    use_materials: bool
    use_transparency: bool
    use_double_wall: bool = False
    static_test: bool = False
    target_fps: int = 60


# Phase 1: Baseline - Single cylinder with simple deformation
PHASE_1_SCENARIO = TestScenario(
    phase=TestPhase.PHASE_1,
    name="Baseline Single Cylinder",
    description="Single cylinder with sine wave deformation. Tests basic Warp kernel memory behavior.",
    cylinder_count=1,
    segments=16,
    radial_segments=12,
    kernel_type="sine_wave",
    max_frames=5000,
    use_materials=False,
    use_transparency=False,
    target_fps=60
)


# Phase 2: Scale Up - Multiple cylinders
PHASE_2_SCENARIO = TestScenario(
    phase=TestPhase.PHASE_2,
    name="Multiple Cylinders",
    description="5 cylinders with varied deformation frequencies. Tests scaling and buffer management.",
    cylinder_count=5,
    segments=16,
    radial_segments=12,
    kernel_type="radial_pulse",
    max_frames=3000,
    use_materials=False,
    use_transparency=False,
    target_fps=60
)


# Phase 3: Production-Like - Materials and complexity
PHASE_3_SCENARIO = TestScenario(
    phase=TestPhase.PHASE_3,
    name="Materials & Complexity",
    description="10 cylinders with breathing wave, opaque materials. Tests production conditions.",
    cylinder_count=10,
    segments=16,
    radial_segments=12,
    kernel_type="breathing_wave",
    max_frames=2000,
    use_materials=True,
    use_transparency=False,
    target_fps=60
)


# Phase 6a: Static Double-Wall Glass - Isolate geometry from dynamics
PHASE_6A_SCENARIO = TestScenario(
    phase=TestPhase.PHASE_6A,
    name="Static Double-Wall Glass",
    description="Double-wall cylinder with glass material, NO deformation. Tests if geometry itself is valid.",
    cylinder_count=1,
    segments=16,
    radial_segments=12,
    kernel_type="sine_wave",
    max_frames=2000,
    use_materials=True,
    use_transparency=True,
    use_double_wall=True,
    static_test=True,
    target_fps=60
)


class TestScenarioManager:
    """Manages test scenario selection and configuration"""
    
    def __init__(self):
        self.scenarios = {
            TestPhase.PHASE_1: PHASE_1_SCENARIO,
            TestPhase.PHASE_2: PHASE_2_SCENARIO,
            TestPhase.PHASE_3: PHASE_3_SCENARIO,
            TestPhase.PHASE_6A: PHASE_6A_SCENARIO
        }
        self.current_scenario: Optional[TestScenario] = None
        
    def get_scenario(self, phase: TestPhase) -> TestScenario:
        """Get scenario configuration for specified phase"""
        return self.scenarios[phase]
        
    def set_current(self, phase: TestPhase):
        """Set the currently active scenario"""
        self.current_scenario = self.scenarios[phase]
        
    def get_current(self) -> Optional[TestScenario]:
        """Get currently active scenario"""
        return self.current_scenario
        
    def list_scenarios(self) -> list:
        """Get list of all available scenarios"""
        return [
            {
                "phase": scenario.phase.value,
                "name": scenario.name,
                "description": scenario.description,
                "cylinders": scenario.cylinder_count,
                "max_frames": scenario.max_frames
            }
            for scenario in self.scenarios.values()
        ]
