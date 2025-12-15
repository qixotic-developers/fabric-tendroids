"""
Unit Tests for Approach Parameters

TEND-17: Define approach_epsilon and approach_minimum parameters
TEND-68: Define approach_epsilon parameter with default value
TEND-69: Define approach_minimum parameter with default value
TEND-70: Add parameters to config file

Run with: python -m pytest tests/test_approach_params.py -v
"""

import unittest
import sys
from unittest.mock import MagicMock

# Mock warp before imports
sys.modules['warp'] = MagicMock()
sys.modules['carb'] = MagicMock()


class TestApproachParameters(unittest.TestCase):
    """Test ApproachParameters dataclass."""
    
    def test_default_values(self):
        """TEND-68, TEND-69: Test default parameter values."""
        from qixotic.tendroids.proximity import ApproachParameters
        
        params = ApproachParameters()
        
        # TEND-68: approach_epsilon default
        self.assertEqual(params.approach_epsilon, 0.04)  # 4cm
        
        # TEND-69: approach_minimum default
        self.assertEqual(params.approach_minimum, 0.15)  # 15cm
        
        # Other defaults
        self.assertEqual(params.warning_distance, 0.25)  # 25cm
        self.assertEqual(params.detection_radius, 1.0)   # 1m
    
    def test_validation_valid(self):
        """Test valid configuration passes validation."""
        from qixotic.tendroids.proximity import ApproachParameters
        
        params = ApproachParameters()
        valid, msg = params.validate()
        
        self.assertTrue(valid)
        self.assertEqual(msg, "OK")
    
    def test_validation_epsilon_zero(self):
        """Test epsilon=0 fails validation."""
        from qixotic.tendroids.proximity import ApproachParameters
        
        params = ApproachParameters(approach_epsilon=0)
        valid, msg = params.validate()
        
        self.assertFalse(valid)
        self.assertIn("epsilon", msg.lower())
    
    def test_validation_minimum_less_than_epsilon(self):
        """Test minimum < epsilon fails validation."""
        from qixotic.tendroids.proximity import ApproachParameters
        
        params = ApproachParameters(
            approach_epsilon=0.10,
            approach_minimum=0.05
        )
        valid, msg = params.validate()
        
        self.assertFalse(valid)
        self.assertIn("minimum", msg.lower())
    
    def test_validation_warning_less_than_minimum(self):
        """Test warning < minimum fails validation."""
        from qixotic.tendroids.proximity import ApproachParameters
        
        params = ApproachParameters(
            approach_minimum=0.30,
            warning_distance=0.20
        )
        valid, msg = params.validate()
        
        self.assertFalse(valid)
    
    def test_to_centimeters(self):
        """Test conversion to centimeters."""
        from qixotic.tendroids.proximity import ApproachParameters
        
        params = ApproachParameters(
            approach_epsilon=0.05,
            approach_minimum=0.10,
            warning_distance=0.20,
            detection_radius=0.50
        )
        
        cm = params.to_centimeters()
        
        self.assertEqual(cm["approach_epsilon_cm"], 5.0)
        self.assertEqual(cm["approach_minimum_cm"], 10.0)
        self.assertEqual(cm["warning_distance_cm"], 20.0)
        self.assertEqual(cm["detection_radius_cm"], 50.0)


class TestZoneClassification(unittest.TestCase):
    """Test zone classification based on distance."""
    
    def setUp(self):
        from qixotic.tendroids.proximity import ApproachParameters
        self.params = ApproachParameters(
            approach_epsilon=0.04,
            approach_minimum=0.15,
            warning_distance=0.25,
            detection_radius=1.0
        )
    
    def test_zone_contact(self):
        """Test contact zone (distance <= epsilon)."""
        self.assertEqual(self.params.get_zone(0.02), "contact")
        self.assertEqual(self.params.get_zone(0.04), "contact")
    
    def test_zone_recovering(self):
        """Test recovering zone (epsilon < distance <= minimum)."""
        self.assertEqual(self.params.get_zone(0.05), "recovering")
        self.assertEqual(self.params.get_zone(0.10), "recovering")
        self.assertEqual(self.params.get_zone(0.15), "recovering")
    
    def test_zone_approaching(self):
        """Test approaching zone (minimum < distance <= warning)."""
        self.assertEqual(self.params.get_zone(0.16), "approaching")
        self.assertEqual(self.params.get_zone(0.20), "approaching")
        self.assertEqual(self.params.get_zone(0.25), "approaching")
    
    def test_zone_detected(self):
        """Test detected zone (warning < distance <= detection)."""
        self.assertEqual(self.params.get_zone(0.30), "detected")
        self.assertEqual(self.params.get_zone(0.50), "detected")
        self.assertEqual(self.params.get_zone(1.0), "detected")
    
    def test_zone_idle(self):
        """Test idle zone (distance > detection)."""
        self.assertEqual(self.params.get_zone(1.01), "idle")
        self.assertEqual(self.params.get_zone(5.0), "idle")
        self.assertEqual(self.params.get_zone(100.0), "idle")


class TestApproachPresets(unittest.TestCase):
    """Test preset configurations."""
    
    def test_preset_default(self):
        """Test default preset."""
        from qixotic.tendroids.proximity import get_approach_params
        
        params = get_approach_params("default")
        self.assertEqual(params.approach_epsilon, 0.04)
    
    def test_preset_small_creature(self):
        """Test small creature preset has tighter tolerances."""
        from qixotic.tendroids.proximity import get_approach_params
        
        params = get_approach_params("small_creature")
        default = get_approach_params("default")
        
        self.assertLess(params.approach_epsilon, default.approach_epsilon)
        self.assertLess(params.detection_radius, default.detection_radius)
    
    def test_preset_large_creature(self):
        """Test large creature preset has larger tolerances."""
        from qixotic.tendroids.proximity import get_approach_params
        
        params = get_approach_params("large_creature")
        default = get_approach_params("default")
        
        self.assertGreater(params.approach_epsilon, default.approach_epsilon)
        self.assertGreater(params.detection_radius, default.detection_radius)
    
    def test_preset_none_returns_default(self):
        """Test None returns default config."""
        from qixotic.tendroids.proximity import get_approach_params, DEFAULT_APPROACH_PARAMS
        
        params = get_approach_params(None)
        self.assertEqual(params.approach_epsilon, DEFAULT_APPROACH_PARAMS.approach_epsilon)
    
    def test_preset_unknown_returns_default(self):
        """Test unknown preset returns default."""
        from qixotic.tendroids.proximity import get_approach_params, DEFAULT_APPROACH_PARAMS
        
        params = get_approach_params("nonexistent")
        self.assertEqual(params.approach_epsilon, DEFAULT_APPROACH_PARAMS.approach_epsilon)


class TestCustomParams(unittest.TestCase):
    """Test custom parameter creation."""
    
    def test_create_from_centimeters(self):
        """Test creating params from centimeter values."""
        from qixotic.tendroids.proximity import create_custom_approach_params
        
        params = create_custom_approach_params(
            epsilon_cm=5.0,
            minimum_cm=15.0,
            warning_cm=30.0,
            detection_cm=100.0
        )
        
        self.assertEqual(params.approach_epsilon, 0.05)
        self.assertEqual(params.approach_minimum, 0.15)
        self.assertEqual(params.warning_distance, 0.30)
        self.assertEqual(params.detection_radius, 1.0)
    
    def test_create_invalid_raises(self):
        """Test invalid params raise ValueError."""
        from qixotic.tendroids.proximity import create_custom_approach_params
        
        with self.assertRaises(ValueError):
            create_custom_approach_params(
                epsilon_cm=20.0,  # Larger than minimum!
                minimum_cm=10.0,
                warning_cm=30.0,
                detection_cm=100.0
            )


class TestPhysXAlignment(unittest.TestCase):
    """Test alignment with PhysX contact offset parameters."""
    
    def test_epsilon_matches_physx_contact_offset(self):
        """Verify approach_epsilon matches PhysX contactOffset."""
        from qixotic.tendroids.proximity import DEFAULT_APPROACH_PARAMS
        
        # PhysX contactOffset is 4cm (set in TEND-13)
        PHYSX_CONTACT_OFFSET = 0.04
        
        self.assertEqual(
            DEFAULT_APPROACH_PARAMS.approach_epsilon, 
            PHYSX_CONTACT_OFFSET,
            "approach_epsilon should match PhysX contactOffset"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
