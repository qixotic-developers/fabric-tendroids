"""
Batch Test Scenario

Test scenario for batch processing optimization.
Validates shared geometry + single kernel approach for multiple tubes.
"""

from dataclasses import dataclass
from enum import Enum


class BatchTestPhase(Enum):
  """Batch test phase identifiers"""
  BATCH_15_TUBES = 100  # 15 tubes, production target
  BATCH_30_TUBES = 101  # 30 tubes, stress test
  BATCH_50_TUBES = 102  # 50 tubes, maximum capacity test


@dataclass
class BatchTestScenario:
  """Configuration for batch processing test"""
  phase: BatchTestPhase
  name: str
  description: str
  tube_count: int
  tube_height: float
  tube_radius: float
  height_segments: int
  radial_segments: int
  spawn_area: tuple
  max_frames: int
  use_materials: bool
  vary_parameters: bool
  stagger_start: bool
  target_fps: int


# Batch Test 1: Production target (15 tubes)
BATCH_15_SCENARIO = BatchTestScenario(
  phase=BatchTestPhase.BATCH_15_TUBES,
  name="Batch Processing - 15 Tubes",
  description="Production target: 15 uniform-diameter tubes with batch GPU processing",
  tube_count=15,
  tube_height=100.0,
  tube_radius=10.0,
  height_segments=16,
  radial_segments=32,
  spawn_area=(200.0, 200.0),
  max_frames=600,  # Reduced for faster testing
  use_materials=False,
  vary_parameters=True,
  stagger_start=True,
  target_fps=60
)

# Batch Test 2: Stress test (30 tubes)
BATCH_30_SCENARIO = BatchTestScenario(
  phase=BatchTestPhase.BATCH_30_TUBES,
  name="Batch Processing - 30 Tubes",
  description="Stress test: 2x production load to validate scaling",
  tube_count=30,
  tube_height=100.0,
  tube_radius=10.0,
  height_segments=16,
  radial_segments=32,
  spawn_area=(300.0, 300.0),
  max_frames=2000,
  use_materials=False,
  vary_parameters=True,
  stagger_start=True,
  target_fps=60
)

# Batch Test 3: Maximum capacity (50 tubes)
BATCH_50_SCENARIO = BatchTestScenario(
  phase=BatchTestPhase.BATCH_50_TUBES,
  name="Batch Processing - 50 Tubes",
  description="Maximum capacity test: Find performance limits",
  tube_count=50,
  tube_height=100.0,
  tube_radius=10.0,
  height_segments=16,
  radial_segments=32,
  spawn_area=(400.0, 400.0),
  max_frames=1000,
  use_materials=False,
  vary_parameters=True,
  stagger_start=True,
  target_fps=60
)


class BatchScenarioManager:
  """Manages batch test scenario selection"""

  def __init__(self):
    self.scenarios = {
      BatchTestPhase.BATCH_15_TUBES: BATCH_15_SCENARIO,
      BatchTestPhase.BATCH_30_TUBES: BATCH_30_SCENARIO,
      BatchTestPhase.BATCH_50_TUBES: BATCH_50_SCENARIO
    }
    self.current_scenario = None

  def get_scenario(self, phase: BatchTestPhase) -> BatchTestScenario:
    """Get scenario configuration"""
    return self.scenarios[phase]

  def set_current(self, phase: BatchTestPhase):
    """Set active scenario"""
    self.current_scenario = self.scenarios[phase]

  def get_current(self) -> BatchTestScenario:
    """Get active scenario"""
    return self.current_scenario

  def list_scenarios(self) -> list:
    """List all batch scenarios"""
    return [
      {
        "phase": scenario.phase.value,
        "name": scenario.name,
        "description": scenario.description,
        "tube_count": scenario.tube_count,
        "max_frames": scenario.max_frames
      }
      for scenario in self.scenarios.values()
    ]
