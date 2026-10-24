"""
Test Registry - All automated test case definitions

Contains 16 predefined tests for creature-tendroid interactions.

Key distances (tendroid at origin, radius=10, creature radius=6):
- Detection range: 31 units from surface (41 from center)
- Contact distance: 18 units from center (10 + 6 + 2 buffer)
- HIGH approach: Y=140 (tendroid can loop around)
- LOW approach: Y=40 (tendroid limited bend)
"""

from .test_case import TestCase, TestWaypoint

# Height constants
Y_HIGH = 140.0  # Near top of tendroid (length=160)
Y_LOW = 40.0    # Near bottom of tendroid

# Distance constants  
START_DIST = 80.0      # Starting distance (well outside detection)
STOP_SHORT_DIST = 25.0 # Inside detection, outside contact
PASS_CLOSE = 20.0      # Close pass-by distance
PASS_EDGE = 40.0       # Edge of detection pass
PASS_TANGENT = 18.0    # Just at contact threshold

# ============================================================================
# HEAD-ON TESTS (creature approaches along Z axis toward tendroid at origin)
# ============================================================================

HEAD_ON_STOP_HIGH = TestCase(
    id="head_on_stop_high",
    name="1. Head-on Stop Short (HIGH)",
    category="head_on",
    description="Approach head-on at high Y, stop before contact. "
                "Deflection should engage, no repulsion.",
    waypoints=[
        TestWaypoint(position=(0, Y_HIGH, START_DIST), fraction=0.0),
        TestWaypoint(position=(0, Y_HIGH, STOP_SHORT_DIST), fraction=0.7),
        TestWaypoint(position=(0, Y_HIGH, STOP_SHORT_DIST), fraction=1.0),  # Hold
    ]
)

HEAD_ON_STOP_LOW = TestCase(
    id="head_on_stop_low",
    name="2. Head-on Stop Short (LOW)",
    category="head_on",
    description="Approach head-on at low Y, stop before contact. "
                "Limited deflection due to height.",
    waypoints=[
        TestWaypoint(position=(0, Y_LOW, START_DIST), fraction=0.0),
        TestWaypoint(position=(0, Y_LOW, STOP_SHORT_DIST), fraction=0.7),
        TestWaypoint(position=(0, Y_LOW, STOP_SHORT_DIST), fraction=1.0),
    ]
)

HEAD_ON_CONTACT_HIGH = TestCase(
    id="head_on_contact_high",
    name="3. Head-on Contact (HIGH)",
    category="head_on",
    description="Approach head-on at high Y, pass through center. "
                "Tendroid should loop around, minimal/no repulsion.",
    waypoints=[
        TestWaypoint(position=(0, Y_HIGH, START_DIST), fraction=0.0),
        TestWaypoint(position=(0, Y_HIGH, 0), fraction=0.5),
        TestWaypoint(position=(0, Y_HIGH, -START_DIST), fraction=1.0),
    ]
)

HEAD_ON_CONTACT_LOW = TestCase(
    id="head_on_contact_low",
    name="4. Head-on Contact (LOW)",
    category="head_on",
    description="Approach head-on at low Y, attempt contact. "
                "Should trigger repulsion, color effect, input lock.",
    waypoints=[
        TestWaypoint(position=(0, Y_LOW, START_DIST), fraction=0.0),
        TestWaypoint(position=(0, Y_LOW, 0), fraction=0.5),
        TestWaypoint(position=(0, Y_LOW, -START_DIST), fraction=1.0),
    ]
)

# ============================================================================
# OFF-CENTER TESTS (approach with X offset)
# ============================================================================

OFF_CENTER_HIGH = TestCase(
    id="off_center_high",
    name="5. Off-center Approach (HIGH)",
    category="off_center",
    description="Approach at high Y with X offset. "
                "Asymmetric deflection pattern.",
    waypoints=[
        TestWaypoint(position=(15, Y_HIGH, START_DIST), fraction=0.0),
        TestWaypoint(position=(15, Y_HIGH, 0), fraction=0.5),
        TestWaypoint(position=(15, Y_HIGH, -START_DIST), fraction=1.0),
    ]
)

OFF_CENTER_LOW = TestCase(
    id="off_center_low",
    name="6. Off-center Approach (LOW)",
    category="off_center",
    description="Approach at low Y with X offset. "
                "Asymmetric deflection, possible contact.",
    waypoints=[
        TestWaypoint(position=(15, Y_LOW, START_DIST), fraction=0.0),
        TestWaypoint(position=(15, Y_LOW, 0), fraction=0.5),
        TestWaypoint(position=(15, Y_LOW, -START_DIST), fraction=1.0),
    ]
)

# ============================================================================
# PASS-BY TESTS (creature passes along X axis)
# ============================================================================

PASS_CLOSE_HIGH = TestCase(
    id="pass_close_high",
    name="7. Close Pass (HIGH)",
    category="pass_by",
    description="Pass close to tendroid at high Y. "
                "Deflection engages and recovers as creature passes.",
    waypoints=[
        TestWaypoint(position=(-START_DIST, Y_HIGH, PASS_CLOSE), fraction=0.0),
        TestWaypoint(position=(0, Y_HIGH, PASS_CLOSE), fraction=0.5),
        TestWaypoint(position=(START_DIST, Y_HIGH, PASS_CLOSE), fraction=1.0),
    ]
)

PASS_CLOSE_LOW = TestCase(
    id="pass_close_low",
    name="8. Close Pass (LOW)",
    category="pass_by",
    description="Pass close to tendroid at low Y. "
                "Limited deflection during pass.",
    waypoints=[
        TestWaypoint(position=(-START_DIST, Y_LOW, PASS_CLOSE), fraction=0.0),
        TestWaypoint(position=(0, Y_LOW, PASS_CLOSE), fraction=0.5),
        TestWaypoint(position=(START_DIST, Y_LOW, PASS_CLOSE), fraction=1.0),
    ]
)

PASS_EDGE_HIGH = TestCase(
    id="pass_edge_high",
    name="9. Edge Pass (HIGH)",
    category="pass_by",
    description="Pass at edge of detection range at high Y. "
                "Minimal deflection response.",
    waypoints=[
        TestWaypoint(position=(-START_DIST, Y_HIGH, PASS_EDGE), fraction=0.0),
        TestWaypoint(position=(0, Y_HIGH, PASS_EDGE), fraction=0.5),
        TestWaypoint(position=(START_DIST, Y_HIGH, PASS_EDGE), fraction=1.0),
    ]
)

PASS_EDGE_LOW = TestCase(
    id="pass_edge_low",
    name="10. Edge Pass (LOW)",
    category="pass_by",
    description="Pass at edge of detection range at low Y.",
    waypoints=[
        TestWaypoint(position=(-START_DIST, Y_LOW, PASS_EDGE), fraction=0.0),
        TestWaypoint(position=(0, Y_LOW, PASS_EDGE), fraction=0.5),
        TestWaypoint(position=(START_DIST, Y_LOW, PASS_EDGE), fraction=1.0),
    ]
)

PASS_TANGENT_HIGH = TestCase(
    id="pass_tangent_high",
    name="11. Tangential Graze (HIGH)",
    category="pass_by",
    description="Pass at contact threshold at high Y. "
                "Tests edge of contact detection.",
    waypoints=[
        TestWaypoint(position=(-START_DIST, Y_HIGH, PASS_TANGENT), fraction=0.0),
        TestWaypoint(position=(0, Y_HIGH, PASS_TANGENT), fraction=0.5),
        TestWaypoint(position=(START_DIST, Y_HIGH, PASS_TANGENT), fraction=1.0),
    ]
)

PASS_TANGENT_LOW = TestCase(
    id="pass_tangent_low",
    name="12. Tangential Graze (LOW)",
    category="pass_by",
    description="Pass at contact threshold at low Y. "
                "Most likely to trigger contact.",
    waypoints=[
        TestWaypoint(position=(-START_DIST, Y_LOW, PASS_TANGENT), fraction=0.0),
        TestWaypoint(position=(0, Y_LOW, PASS_TANGENT), fraction=0.5),
        TestWaypoint(position=(START_DIST, Y_LOW, PASS_TANGENT), fraction=1.0),
    ]
)

# ============================================================================
# RECOVERY TESTS
# ============================================================================

APPROACH_RETREAT = TestCase(
    id="approach_retreat",
    name="13. Approach & Retreat",
    category="recovery",
    description="Approach tendroid, pause in detection zone, retreat. "
                "Tests tendroid straightening recovery.",
    waypoints=[
        TestWaypoint(position=(0, Y_HIGH, START_DIST), fraction=0.0),
        TestWaypoint(position=(0, Y_HIGH, STOP_SHORT_DIST), fraction=0.3),
        TestWaypoint(position=(0, Y_HIGH, STOP_SHORT_DIST), fraction=0.5),  # Hold
        TestWaypoint(position=(0, Y_HIGH, START_DIST), fraction=1.0),  # Retreat
    ]
)

RAPID_OSCILLATE = TestCase(
    id="rapid_oscillate",
    name="14. Rapid Oscillation",
    category="recovery",
    description="Quick in-out-in-out motion. "
                "Stress test for recovery system.",
    waypoints=[
        TestWaypoint(position=(0, Y_HIGH, START_DIST), fraction=0.0),
        TestWaypoint(position=(0, Y_HIGH, STOP_SHORT_DIST), fraction=0.2),
        TestWaypoint(position=(0, Y_HIGH, START_DIST), fraction=0.4),
        TestWaypoint(position=(0, Y_HIGH, STOP_SHORT_DIST), fraction=0.6),
        TestWaypoint(position=(0, Y_HIGH, START_DIST), fraction=0.8),
        TestWaypoint(position=(0, Y_HIGH, STOP_SHORT_DIST), fraction=1.0),
    ]
)

# ============================================================================
# SPECIAL TESTS
# ============================================================================

VERTICAL_DESCENT = TestCase(
    id="vertical_descent",
    name="15. Vertical Descent",
    category="special",
    description="Drop from above onto tendroid. "
                "Tests vertical approach handling.",
    waypoints=[
        TestWaypoint(position=(15, 200, 15), fraction=0.0),  # Above and offset
        TestWaypoint(position=(15, Y_LOW, 15), fraction=0.7),  # Descend
        TestWaypoint(position=(15, Y_LOW, 15), fraction=1.0),  # Hold
    ]
)

HIGH_SPEED_FLYBY = TestCase(
    id="high_speed_flyby",
    name="16. High-speed Flyby",
    category="special",
    description="Fast pass to test response timing. "
                "Run with short duration (1-2s).",
    waypoints=[
        TestWaypoint(position=(-120, Y_HIGH, PASS_CLOSE), fraction=0.0),
        TestWaypoint(position=(120, Y_HIGH, PASS_CLOSE), fraction=1.0),
    ]
)

# ============================================================================
# REGISTRY
# ============================================================================

ALL_TESTS = [
    # Head-on
    HEAD_ON_STOP_HIGH,
    HEAD_ON_STOP_LOW,
    HEAD_ON_CONTACT_HIGH,
    HEAD_ON_CONTACT_LOW,
    # Off-center
    OFF_CENTER_HIGH,
    OFF_CENTER_LOW,
    # Pass-by
    PASS_CLOSE_HIGH,
    PASS_CLOSE_LOW,
    PASS_EDGE_HIGH,
    PASS_EDGE_LOW,
    PASS_TANGENT_HIGH,
    PASS_TANGENT_LOW,
    # Recovery
    APPROACH_RETREAT,
    RAPID_OSCILLATE,
    # Special
    VERTICAL_DESCENT,
    HIGH_SPEED_FLYBY,
]

TESTS_BY_ID = {test.id: test for test in ALL_TESTS}

TESTS_BY_CATEGORY = {}
for test in ALL_TESTS:
    if test.category not in TESTS_BY_CATEGORY:
        TESTS_BY_CATEGORY[test.category] = []
    TESTS_BY_CATEGORY[test.category].append(test)


def get_test_by_id(test_id: str) -> TestCase | None:
    """Look up test case by ID."""
    return TESTS_BY_ID.get(test_id)


def get_all_test_ids() -> list[str]:
    """Get list of all test IDs."""
    return [test.id for test in ALL_TESTS]


def get_all_test_names() -> list[str]:
    """Get list of all test display names."""
    return [test.name for test in ALL_TESTS]
