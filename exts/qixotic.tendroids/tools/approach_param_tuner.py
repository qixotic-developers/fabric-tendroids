"""
Approach Parameter Tuning Tool

Runtime tool for tuning proximity detection parameters.
Provides both programmatic API and print-based inspection.

TEND-17: approach_epsilon and approach_minimum parameters

Usage:
    from tools.approach_param_tuner import ApproachParamTuner
    
    tuner = ApproachParamTuner()
    tuner.print_values()
    tuner.set_epsilon_cm(5.0)  # Set to 5cm
    tuner.save_to_file("my_params.json")
"""

import json
from dataclasses import dataclass
from typing import Optional

try:
  from qixotic.tendroids.proximity import ApproachParameters, DEFAULT_APPROACH_PARAMS
except ImportError:
  @dataclass
  class ApproachParameters:
    approach_epsilon: float = 0.04
    approach_minimum: float = 0.15
    warning_distance: float = 0.25
    detection_radius: float = 1.0

    def validate(self):
      if self.approach_epsilon <= 0:
        return False, "epsilon must be > 0"
      if self.approach_minimum <= self.approach_epsilon:
        return False, "minimum must be > epsilon"
      if self.warning_distance <= self.approach_minimum:
        return False, "warning must be > minimum"
      if self.detection_radius <= self.warning_distance:
        return False, "detection must be > warning"
      return True, "OK"

    def to_centimeters(self):
      return {
        "approach_epsilon_cm": self.approach_epsilon * 100,
        "approach_minimum_cm": self.approach_minimum * 100,
        "warning_distance_cm": self.warning_distance * 100,
        "detection_radius_cm": self.detection_radius * 100,
      }

    def get_zone(self, distance):
      if distance <= self.approach_epsilon:
        return "contact"
      elif distance <= self.approach_minimum:
        return "recovering"
      elif distance <= self.warning_distance:
        return "approaching"
      elif distance <= self.detection_radius:
        return "detected"
      return "idle"


  DEFAULT_APPROACH_PARAMS = ApproachParameters()


class ApproachParamTuner:
  """
  Interactive tuner for approach parameters.

  Provides methods to adjust parameters in centimeters
  and save/load configurations.
  """

  DEFAULT_CONFIG_FILE = "approach_params.json"

  def __init__(self, params: Optional[ApproachParameters] = None):
    """Initialize with optional starting parameters."""
    if params:
      self.params = params
    else:
      self.params = ApproachParameters(
        approach_epsilon=DEFAULT_APPROACH_PARAMS.approach_epsilon,
        approach_minimum=DEFAULT_APPROACH_PARAMS.approach_minimum,
        warning_distance=DEFAULT_APPROACH_PARAMS.warning_distance,
        detection_radius=DEFAULT_APPROACH_PARAMS.detection_radius,
      )

  def print_values(self):
    """Print current parameter values in cm."""
    cm = self.params.to_centimeters()
    valid, msg = self.params.validate()

    print("\n┌─────────────────────────────────────┐")
    print("│     APPROACH PARAMETERS             │")
    print("├─────────────────────────────────────┤")
    print(f"│  approach_epsilon:  {cm['approach_epsilon_cm']:6.1f} cm      │")
    print(f"│  approach_minimum:  {cm['approach_minimum_cm']:6.1f} cm      │")
    print(f"│  warning_distance:  {cm['warning_distance_cm']:6.1f} cm      │")
    print(f"│  detection_radius:  {cm['detection_radius_cm']:6.1f} cm      │")
    print("├─────────────────────────────────────┤")
    print(f"│  Valid: {'✓' if valid else '✗'} {msg:27s} │")
    print("└─────────────────────────────────────┘")

  def print_zones(self):
    """Print zone visualization."""
    cm = self.params.to_centimeters()
    e = cm['approach_epsilon_cm']
    m = cm['approach_minimum_cm']
    w = cm['warning_distance_cm']
    d = cm['detection_radius_cm']

    print("\nZone Visualization (distances from surface):")
    print(f"  0 ──┬── {e:.0f}cm ──┬── {m:.0f}cm ──┬── {w:.0f}cm ──┬── {d:.0f}cm ──>")
    print(f"      │  CONTACT  │ RECOVERING │ APPROACHING │ DETECTED  │ IDLE")

  # Setters (in centimeters for convenience)
  def set_epsilon_cm(self, value_cm: float):
    """Set approach_epsilon in centimeters."""
    self.params.approach_epsilon = value_cm / 100.0
    self._validate_and_report()

  def set_minimum_cm(self, value_cm: float):
    """Set approach_minimum in centimeters."""
    self.params.approach_minimum = value_cm / 100.0
    self._validate_and_report()

  def set_warning_cm(self, value_cm: float):
    """Set warning_distance in centimeters."""
    self.params.warning_distance = value_cm / 100.0
    self._validate_and_report()

  def set_detection_cm(self, value_cm: float):
    """Set detection_radius in centimeters."""
    self.params.detection_radius = value_cm / 100.0
    self._validate_and_report()

  def _validate_and_report(self):
    """Validate and print current values."""
    valid, msg = self.params.validate()
    if not valid:
      print(f"⚠️  Warning: {msg}")

  def reset_defaults(self):
    """Reset to default values."""
    self.params = ApproachParameters()
    print("Reset to defaults")
    self.print_values()

  def save_to_file(self, filepath: str = None):
    """Save parameters to JSON file."""
    filepath = filepath or self.DEFAULT_CONFIG_FILE
    data = {
      "approach_epsilon": self.params.approach_epsilon,
      "approach_minimum": self.params.approach_minimum,
      "warning_distance": self.params.warning_distance,
      "detection_radius": self.params.detection_radius,
    }
    with open(filepath, 'w') as f:
      json.dump(data, f, indent=2)
    print(f"✓ Saved to {filepath}")

  def load_from_file(self, filepath: str = None):
    """Load parameters from JSON file."""
    filepath = filepath or self.DEFAULT_CONFIG_FILE
    try:
      with open(filepath, 'r') as f:
        data = json.load(f)
      self.params = ApproachParameters(**data)
      print(f"✓ Loaded from {filepath}")
      self.print_values()
    except FileNotFoundError:
      print(f"✗ File not found: {filepath}")
    except Exception as e:
      print(f"✗ Load error: {e}")

  def test_distance(self, distance_cm: float):
    """Test which zone a distance falls into."""
    distance_m = distance_cm / 100.0
    zone = self.params.get_zone(distance_m)
    print(f"Distance {distance_cm:.1f}cm → Zone: {zone.upper()}")
    return zone


# Convenience function
def quick_tune():
  """Quick-start tuning session."""
  tuner = ApproachParamTuner()
  tuner.print_values()
  tuner.print_zones()
  print("\nUsage:")
  print("  tuner.set_epsilon_cm(5.0)")
  print("  tuner.set_minimum_cm(15.0)")
  print("  tuner.test_distance(10.0)")
  print("  tuner.save_to_file()")
  return tuner


if __name__ == "__main__":
  tuner = quick_tune()
