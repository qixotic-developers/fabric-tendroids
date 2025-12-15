"""
Pytest Configuration and Fixtures

Provides shared fixtures for all tests in the suite.
Mocks Omniverse modules to allow testing outside the runtime.
"""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest


# =============================================================================
# MOCK OMNIVERSE MODULES BEFORE ANY IMPORTS
# =============================================================================
# This must happen before importing any qixotic.tendroids modules


class MockModule(ModuleType):
  """A module that returns MagicMock for any attribute access."""

  def __init__(self, name):
    super().__init__(name)
    # Make it look like a package so submodules can be imported
    self.__path__ = []
    self.__package__ = name
    self.__file__ = f"<mock:{name}>"

  def __getattr__(self, name):
    if name.startswith('__'):
      raise AttributeError(name)
    # Return a MagicMock for any attribute
    mock = MagicMock()
    object.__setattr__(self, name, mock)
    return mock


def install_mock_module(name: str) -> MockModule:
  """Install a mock module and all its parent packages."""
  parts = name.split('.')

  # Install all parent packages first
  for i in range(len(parts)):
    partial_name = '.'.join(parts[:i + 1])
    if partial_name not in sys.modules:
      mock = MockModule(partial_name)
      sys.modules[partial_name] = mock

      # Link child to parent
      if i > 0:
        parent_name = '.'.join(parts[:i])
        parent = sys.modules[parent_name]
        setattr(parent, parts[i], mock)

  return sys.modules[name]


# Comprehensive list of omni modules used in the extension
omni_modules = [
  'omni',
  'omni.ext',
  'omni.ui',
  'omni.usd',
  'omni.timeline',
  'omni.physx',
  'omni.client',
  'omni.appwindow',
  # omni.kit hierarchy
  'omni.kit',
  'omni.kit.app',
  'omni.kit.commands',
  'omni.kit.ui',
  'omni.kit.usd',
  'omni.kit.menu',
  # omni.kit.window hierarchy
  'omni.kit.window',
  'omni.kit.window.extensions',
  'omni.kit.window.file',
  'omni.kit.window.property',
  'omni.kit.window.property.templates',
  # Additional modules
  'omni.kit.viewport',
  'omni.kit.viewport.utility',
  'omni.kit.widget',
  'omni.kit.widget.stage',
  'omni.physx.scripts',
  'omni.physx.bindings',
  'omni.usd.libs',
]

# Install all omni modules
for name in omni_modules:
  install_mock_module(name)

# Set up omni.ext.IExt as a proper base class
sys.modules['omni.ext'].IExt = type('IExt', (), {
  'on_startup': lambda self, ext_id: None,
  'on_shutdown': lambda self: None,
})

# Mock carb (Carbonite logging)
carb_modules = [
  'carb',
  'carb.settings',
  'carb.log',
  'carb.input',
  'carb.events',
]
for name in carb_modules:
  install_mock_module(name)

# Set up carb logging functions
sys.modules['carb'].log_info = MagicMock()
sys.modules['carb'].log_warn = MagicMock()
sys.modules['carb'].log_error = MagicMock()

# Mock pxr (Pixar USD)
pxr_modules = [
  'pxr',
  'pxr.Usd',
  'pxr.UsdGeom',
  'pxr.UsdPhysics',
  'pxr.UsdShade',
  'pxr.UsdLux',
  'pxr.Gf',
  'pxr.Sdf',
  'pxr.Vt',
  'pxr.Tf',
]
for name in pxr_modules:
  install_mock_module(name)

# Mock PhysxSchema
install_mock_module('PhysxSchema')
install_mock_module('physxSchema')

# Add extension source to path for imports
ext_root = Path(__file__).parent.parent
if str(ext_root) not in sys.path:
  sys.path.insert(0, str(ext_root))

# Now safe to import test mocks
from tests.test_mocks import MockStage, MockVec3f, MockPrim


# =============================================================================
# MARKERS
# =============================================================================

def pytest_configure(config):
  """Register custom markers."""
  config.addinivalue_line(
    "markers", "integration: marks tests requiring Omniverse runtime"
  )
  config.addinivalue_line(
    "markers", "unit: marks pure unit tests (no Omniverse required)"
  )
  config.addinivalue_line(
    "markers", "gpu: marks tests requiring GPU/CUDA"
  )


# =============================================================================
# FIXTURES - Mock Objects
# =============================================================================

@pytest.fixture
def mock_stage():
  """Provide a fresh mock USD stage."""
  return MockStage()


@pytest.fixture
def mock_stage_with_creature(mock_stage):
  """Provide a mock stage with creature prim already present."""
  mock_stage.add_prim("/World/Creature", "Xform")
  mock_stage.add_prim("/World/Creature/Body", "Cylinder")
  mock_stage.add_prim("/World/Creature/Nose", "Cone")
  return mock_stage


@pytest.fixture
def mock_vec3f():
  """Factory fixture for creating MockVec3f instances."""

  def _create(x=0.0, y=0.0, z=0.0):
    return MockVec3f(x, y, z)

  return _create


# =============================================================================
# FIXTURES - Mocked Modules (for explicit injection)
# =============================================================================

@pytest.fixture
def carb_mock():
  """Mock carb module for logging."""
  return sys.modules['carb']


@pytest.fixture
def pxr_mock():
  """Mock pxr module with common USD types."""
  return sys.modules['pxr']


# =============================================================================
# FIXTURES - Test Data
# =============================================================================

@pytest.fixture
def creature_position():
  """Default creature test position."""
  return MockVec3f(0, 50, 0)


@pytest.fixture
def tendroid_positions():
  """Sample tendroid positions for interaction tests."""
  return [
    MockVec3f(20, 0, 0),  # Right of origin
    MockVec3f(-20, 0, 0),  # Left of origin
    MockVec3f(0, 0, 20),  # In front
    MockVec3f(0, 0, -20),  # Behind
  ]


@pytest.fixture
def envelope_params():
  """Expected envelope parameters from TEND-11 design."""
  return {
    'radius': 6.0,
    'half_height': 6.0,
    'total_length': 24.0,
    'axis': 'Z',
    'contact_offset': 0.04,
    'rest_offset': 0.01,
  }
