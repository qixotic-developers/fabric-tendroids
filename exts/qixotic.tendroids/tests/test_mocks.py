"""
Mock Objects for Unit Testing

Provides lightweight mocks for USD/Omniverse types to enable
testing without the full Omniverse runtime.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class MockVec3f:
  """Mock for pxr.Gf.Vec3f"""
  x: float = 0.0
  y: float = 0.0
  z: float = 0.0

  def __init__(self, x=0.0, y=0.0, z=0.0):
    if isinstance(x, (list, tuple)):
      self.x, self.y, self.z = x[0], x[1], x[2]
    else:
      self.x, self.y, self.z = x, y, z

  def __getitem__(self, idx):
    return [self.x, self.y, self.z][idx]

  def __setitem__(self, idx, value):
    if idx == 0:
      self.x = value
    elif idx == 1:
      self.y = value
    elif idx == 2:
      self.z = value

  def __add__(self, other):
    return MockVec3f(self.x + other.x, self.y + other.y, self.z + other.z)

  def __sub__(self, other):
    return MockVec3f(self.x - other.x, self.y - other.y, self.z - other.z)

  def __mul__(self, scalar):
    return MockVec3f(self.x * scalar, self.y * scalar, self.z * scalar)

  def __truediv__(self, scalar):
    return MockVec3f(self.x / scalar, self.y / scalar, self.z / scalar)

  def GetLength(self):
    import math
    return math.sqrt(self.x ** 2 + self.y ** 2 + self.z ** 2)

  def GetNormalized(self):
    length = self.GetLength()
    if length < 0.0001:
      return MockVec3f(0, 0, 0)
    return self / length

  def GetDot(self, other):
    return self.x * other.x + self.y * other.y + self.z * other.z


@dataclass
class MockPrim:
  """Mock for USD Prim"""
  path: str
  prim_type: str = "Xform"
  valid: bool = True
  children: Dict[str, 'MockPrim'] = field(default_factory=dict)
  attributes: Dict[str, Any] = field(default_factory=dict)
  apis_applied: List[str] = field(default_factory=list)

  def IsValid(self):
    return self.valid

  def GetPath(self):
    return self.path

  def GetTypeName(self):
    return self.prim_type


class MockAttribute:
  """Mock for USD Attribute"""

  def __init__(self, value=None):
    self._value = value

  def Set(self, value):
    self._value = value

  def Get(self):
    return self._value


class MockStage:
  """Mock for USD Stage"""

  def __init__(self):
    self.prims: Dict[str, MockPrim] = { }
    self.removed_prims: List[str] = []

  def GetPrimAtPath(self, path: str) -> MockPrim:
    if path in self.prims:
      return self.prims[path]
    # Return invalid prim
    return MockPrim(path=path, valid=False)

  def RemovePrim(self, path: str):
    if path in self.prims:
      del self.prims[path]
    self.removed_prims.append(path)

  def DefinePrim(self, path: str, prim_type: str = "Xform") -> MockPrim:
    prim = MockPrim(path=path, prim_type=prim_type)
    self.prims[path] = prim
    return prim

  def add_prim(self, path: str, prim_type: str = "Xform") -> MockPrim:
    """Helper to add a prim to the stage"""
    return self.DefinePrim(path, prim_type)


class MockCapsule:
  """Mock for UsdGeom.Capsule"""

  def __init__(self, prim: MockPrim):
    self._prim = prim
    self._radius = MockAttribute()
    self._height = MockAttribute()
    self._axis = MockAttribute()

  @classmethod
  def Define(cls, stage: MockStage, path: str) -> 'MockCapsule':
    prim = stage.DefinePrim(path, "Capsule")
    return cls(prim)

  def CreateRadiusAttr(self):
    return self._radius

  def CreateHeightAttr(self):
    return self._height

  def CreateAxisAttr(self):
    return self._axis

  def GetPrim(self):
    return self._prim


class MockCollisionAPI:
  """Mock for UsdPhysics.CollisionAPI"""

  @classmethod
  def Apply(cls, prim: MockPrim):
    prim.apis_applied.append("CollisionAPI")
    return cls()


class MockPhysxCollisionAPI:
  """Mock for PhysxSchema.PhysxCollisionAPI"""

  def __init__(self):
    self._contact_offset = MockAttribute()
    self._rest_offset = MockAttribute()

  @classmethod
  def Apply(cls, prim: MockPrim):
    prim.apis_applied.append("PhysxCollisionAPI")
    return cls()

  def CreateContactOffsetAttr(self):
    return self._contact_offset

  def CreateRestOffsetAttr(self):
    return self._rest_offset
