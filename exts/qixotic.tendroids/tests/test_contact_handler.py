"""
Tests for Contact Handler System

Unit tests for PhysX contact subscription and filtering.
Implements TEND-94: Add unit tests for contact handler.
"""

from unittest.mock import MagicMock

from qixotic.tendroids.contact.contact_filter_helpers import (ContactInfo, extract_contact_info,
                                                              filter_creature_tendroid_contacts, is_creature_prim,
                                                              is_tendroid_prim)
from qixotic.tendroids.contact.contact_handler import (ContactEvent, ContactHandler, ContactHandlerState)


# =============================================================================
# FILTER HELPERS TESTS
# =============================================================================

class TestIsCreaturePrim:
  """Tests for is_creature_prim function."""

  def test_default_creature_path(self):
    """Default pattern matches /World/Creature."""
    assert is_creature_prim('/World/Creature') is True
    assert is_creature_prim('/World/Creature/Body') is True
    assert is_creature_prim('/World/Creature/Nose') is True

  def test_non_creature_path(self):
    """Non-creature paths return False."""
    assert is_creature_prim('/World/Tendroid_0') is False
    assert is_creature_prim('/World/Ground') is False
    assert is_creature_prim('/World/Other') is False

  def test_custom_patterns(self):
    """Custom patterns work correctly."""
    patterns = ['/Game/Player', '/Game/NPC']
    assert is_creature_prim('/Game/Player/Body', patterns) is True
    assert is_creature_prim('/Game/NPC/Head', patterns) is True
    assert is_creature_prim('/World/Creature', patterns) is False


class TestIsTendroidPrim:
  """Tests for is_tendroid_prim function."""

  def test_default_tendroid_paths(self):
    """Default patterns match tendroid paths."""
    assert is_tendroid_prim('/World/Tendroids/Tendroid_0') is True
    assert is_tendroid_prim('/World/Tendroid_5/Segment_2') is True

  def test_non_tendroid_path(self):
    """Non-tendroid paths return False."""
    assert is_tendroid_prim('/World/Creature') is False
    assert is_tendroid_prim('/World/Ground') is False

  def test_custom_patterns(self):
    """Custom patterns work correctly."""
    patterns = ['/Game/Obstacles/']
    assert is_tendroid_prim('/Game/Obstacles/Pole_1', patterns) is True
    assert is_tendroid_prim('/World/Tendroids/', patterns) is False


class TestExtractContactInfo:
  """Tests for extract_contact_info function."""

  def test_creature_tendroid_pair(self):
    """Extracts info when creature is actor0."""
    info = extract_contact_info(
      actor0_path='/World/Creature/Body',
      actor1_path='/World/Tendroids/Tendroid_0',
      contact_point=(10.0, 5.0, 20.0),
      contact_normal=(1.0, 0.0, 0.0),
      impulse=50.0,
      separation=-0.01,
    )

    assert info is not None
    assert info.creature_path == '/World/Creature/Body'
    assert info.tendroid_path == '/World/Tendroids/Tendroid_0'
    assert info.contact_point == (10.0, 5.0, 20.0)
    assert info.contact_normal == (1.0, 0.0, 0.0)
    assert info.impulse == 50.0
    assert info.separation == -0.01

  def test_tendroid_creature_pair_flips_normal(self):
    """When tendroid is actor0, normal is flipped."""
    info = extract_contact_info(
      actor0_path='/World/Tendroids/Tendroid_0',
      actor1_path='/World/Creature/Body',
      contact_point=(10.0, 5.0, 20.0),
      contact_normal=(1.0, 0.0, 0.0),
    )

    assert info is not None
    assert info.creature_path == '/World/Creature/Body'
    assert info.tendroid_path == '/World/Tendroids/Tendroid_0'
    # Normal should be flipped to point toward creature
    assert info.contact_normal == (-1.0, 0.0, 0.0)

  def test_non_matching_pair_returns_none(self):
    """Returns None for non creature-tendroid pairs."""
    # Creature-Creature
    info = extract_contact_info(
      '/World/Creature/Body',
      '/World/Creature/Nose',
      (0, 0, 0), (0, 1, 0),
    )
    assert info is None

    # Tendroid-Tendroid
    info = extract_contact_info(
      '/World/Tendroids/T0',
      '/World/Tendroids/T1',
      (0, 0, 0), (0, 1, 0),
    )
    assert info is None

    # Other-Other
    info = extract_contact_info(
      '/World/Ground',
      '/World/Wall',
      (0, 0, 0), (0, 1, 0),
    )
    assert info is None


class TestFilterCreatureTendroidContacts:
  """Tests for filter_creature_tendroid_contacts function."""

  def test_filters_mixed_contacts(self):
    """Filters only creature-tendroid pairs from mixed list."""
    contacts = [
      # Creature-Tendroid (should include)
      ('/World/Creature', '/World/Tendroids/T0',
       (0, 0, 0), (1, 0, 0), 10.0, 0.0),
      # Ground-Creature (should exclude)
      ('/World/Ground', '/World/Creature',
       (0, 0, 0), (0, 1, 0), 5.0, 0.0),
      # Tendroid-Creature (should include)
      ('/World/Tendroid_1', '/World/Creature/Body',
       (5, 0, 0), (0, 0, 1), 20.0, -0.01),
    ]

    results = filter_creature_tendroid_contacts(contacts)

    assert len(results) == 2
    assert results[0].tendroid_path == '/World/Tendroids/T0'
    assert results[1].tendroid_path == '/World/Tendroid_1'

  def test_empty_list(self):
    """Returns empty list for empty input."""
    assert filter_creature_tendroid_contacts([]) == []


# =============================================================================
# CONTACT HANDLER TESTS
# =============================================================================

class TestContactHandlerInit:
  """Tests for ContactHandler initialization."""

  def test_initial_state(self):
    """Handler starts uninitialized."""
    handler = ContactHandler()
    assert handler.state == ContactHandlerState.UNINITIALIZED
    assert handler.is_subscribed is False
    assert handler.contact_count == 0

  def test_custom_patterns(self):
    """Custom patterns are stored."""
    handler = ContactHandler(
      creature_patterns=['/Game/Player'],
      tendroid_patterns=['/Game/Poles/'],
    )
    assert handler._creature_patterns == ['/Game/Player']
    assert handler._tendroid_patterns == ['/Game/Poles/']


class TestContactHandlerListeners:
  """Tests for listener management."""

  def test_add_listener(self):
    """Listeners can be added."""
    handler = ContactHandler()
    callback = MagicMock()

    handler.add_listener(callback)

    assert callback in handler._listeners

  def test_add_listener_no_duplicates(self):
    """Same listener not added twice."""
    handler = ContactHandler()
    callback = MagicMock()

    handler.add_listener(callback)
    handler.add_listener(callback)

    assert len(handler._listeners) == 1

  def test_remove_listener(self):
    """Listeners can be removed."""
    handler = ContactHandler()
    callback = MagicMock()

    handler.add_listener(callback)
    handler.remove_listener(callback)

    assert callback not in handler._listeners

  def test_remove_nonexistent_listener(self):
    """Removing non-existent listener doesn't error."""
    handler = ContactHandler()
    callback = MagicMock()

    handler.remove_listener(callback)  # Should not raise


class TestContactHandlerSubscription:
  """Tests for subscription lifecycle."""

  def test_subscribe_changes_state(self):
    """Subscribe changes state to SUBSCRIBED."""
    handler = ContactHandler()

    result = handler.subscribe()

    assert result is True
    assert handler.state == ContactHandlerState.SUBSCRIBED
    assert handler.is_subscribed is True

  def test_subscribe_idempotent(self):
    """Multiple subscribes are safe."""
    handler = ContactHandler()

    handler.subscribe()
    result = handler.subscribe()

    assert result is True
    assert handler.is_subscribed is True

  def test_unsubscribe_changes_state(self):
    """Unsubscribe changes state."""
    handler = ContactHandler()
    handler.subscribe()

    handler.unsubscribe()

    assert handler.state == ContactHandlerState.UNSUBSCRIBED
    assert handler.is_subscribed is False

  def test_shutdown_cleans_up(self):
    """Shutdown clears listeners and unsubscribes."""
    handler = ContactHandler()
    handler.add_listener(MagicMock())
    handler.subscribe()
    handler._contact_count = 10

    handler.shutdown()

    assert handler.is_subscribed is False
    assert len(handler._listeners) == 0
    assert handler.contact_count == 0


class TestContactHandlerSimulation:
  """Tests for simulated contact events."""

  def test_simulate_contact_dispatches_event(self):
    """Simulated contacts dispatch to listeners."""
    handler = ContactHandler()
    received_events = []
    handler.add_listener(lambda e: received_events.append(e))

    handler.simulate_contact(
      creature_path='/World/Creature',
      tendroid_path='/World/Tendroids/T0',
      contact_point=(10.0, 5.0, 20.0),
      surface_normal=(1.0, 0.0, 0.0),
      impulse=50.0,
    )

    assert len(received_events) == 1
    event = received_events[0]
    assert event.creature_path == '/World/Creature'
    assert event.tendroid_path == '/World/Tendroids/T0'
    assert event.contact_point == (10.0, 5.0, 20.0)
    assert event.surface_normal == (1.0, 0.0, 0.0)
    assert event.impulse == 50.0

  def test_simulate_contact_increments_count(self):
    """Contact count increments with simulated contacts."""
    handler = ContactHandler()

    handler.simulate_contact(
      '/World/Creature', '/World/Tendroids/T0',
      (0, 0, 0), (1, 0, 0),
    )
    handler.simulate_contact(
      '/World/Creature', '/World/Tendroids/T1',
      (0, 0, 0), (0, 0, 1),
    )

    assert handler.contact_count == 2

  def test_listener_error_does_not_stop_others(self):
    """One listener error doesn't prevent others from receiving."""
    handler = ContactHandler()
    received = []

    def bad_listener():
      raise ValueError("Oops")

    def good_listener(e):
      received.append(e)

    handler.add_listener(bad_listener)
    handler.add_listener(good_listener)

    # Should not raise
    handler.simulate_contact(
      '/World/Creature', '/World/Tendroids/T0',
      (0, 0, 0), (1, 0, 0),
    )

    assert len(received) == 1


class TestContactEvent:
  """Tests for ContactEvent dataclass."""

  def test_from_contact_info(self):
    """Creates ContactEvent from ContactInfo."""
    info = ContactInfo(
      creature_path='/World/Creature',
      tendroid_path='/World/Tendroids/T0',
      contact_point=(1.0, 2.0, 3.0),
      contact_normal=(0.0, 1.0, 0.0),
      impulse=100.0,
      separation=-0.005,
    )

    event = ContactEvent.from_contact_info(info)

    assert event.creature_path == '/World/Creature'
    assert event.tendroid_path == '/World/Tendroids/T0'
    assert event.contact_point == (1.0, 2.0, 3.0)
    assert event.surface_normal == (0.0, 1.0, 0.0)
    assert event.impulse == 100.0
    assert event.separation == -0.005


# =============================================================================
# PHYSX CALLBACK TESTS - _on_contact_report
# =============================================================================

class MockContactData:
    """Mock PhysX contact data structure."""
    def __init__(self, position, normal, impulse=0.0, separation=0.0):
        self.position = position
        self.normal = normal
        self.impulse = impulse
        self.separation = separation


class MockContactHeader:
    """Mock PhysX contact header structure."""
    def __init__(self, actor0, actor1, num_contacts, data_offset=0):
        self.actor0 = actor0
        self.actor1 = actor1
        self.num_contact_data = num_contacts
        self.contact_data_offset = data_offset


class TestOnContactReport:
    """Tests for _on_contact_report PhysX callback."""

    def test_single_creature_tendroid_contact(self):
        """Processes single creature-tendroid contact correctly."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        headers = [
            MockContactHeader('/World/Creature', '/World/Tendroids/T0', 1, 0)
        ]
        contact_data = [
            MockContactData([10.0, 5.0, 20.0], [1.0, 0.0, 0.0], 50.0, -0.01)
        ]

        handler._on_contact_report(headers, contact_data)

        assert len(received) == 1
        assert received[0].creature_path == '/World/Creature'
        assert received[0].tendroid_path == '/World/Tendroids/T0'
        assert received[0].contact_point == (10.0, 5.0, 20.0)
        assert received[0].surface_normal == (1.0, 0.0, 0.0)

    def test_multiple_contacts_single_header(self):
        """Processes multiple contact points in single header."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        headers = [
            MockContactHeader('/World/Creature', '/World/Tendroids/T0', 3, 0)
        ]
        contact_data = [
            MockContactData([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
            MockContactData([2.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
            MockContactData([3.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
        ]

        handler._on_contact_report(headers, contact_data)

        assert len(received) == 3
        assert received[0].contact_point == (1.0, 0.0, 0.0)
        assert received[1].contact_point == (2.0, 0.0, 0.0)
        assert received[2].contact_point == (3.0, 0.0, 0.0)

    def test_multiple_headers(self):
        """Processes multiple contact headers."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        headers = [
            MockContactHeader('/World/Creature', '/World/Tendroids/T0', 1, 0),
            MockContactHeader('/World/Creature', '/World/Tendroids/T1', 1, 1),
        ]
        contact_data = [
            MockContactData([1.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
            MockContactData([2.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
        ]

        handler._on_contact_report(headers, contact_data)

        assert len(received) == 2
        assert received[0].tendroid_path == '/World/Tendroids/T0'
        assert received[1].tendroid_path == '/World/Tendroids/T1'

    def test_filters_non_creature_tendroid_contacts(self):
        """Ignores contacts not involving creature-tendroid pairs."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        headers = [
            # Should be ignored - ground contact
            MockContactHeader('/World/Ground', '/World/Creature', 1, 0),
            # Should be processed
            MockContactHeader('/World/Creature', '/World/Tendroids/T0', 1, 1),
            # Should be ignored - tendroid-tendroid
            MockContactHeader('/World/Tendroids/T0', '/World/Tendroids/T1', 1, 2),
        ]
        contact_data = [
            MockContactData([0.0, 0.0, 0.0], [0.0, 1.0, 0.0]),
            MockContactData([5.0, 0.0, 0.0], [1.0, 0.0, 0.0]),
            MockContactData([10.0, 0.0, 0.0], [0.0, 0.0, 1.0]),
        ]

        handler._on_contact_report(headers, contact_data)

        assert len(received) == 1
        assert received[0].tendroid_path == '/World/Tendroids/T0'

    def test_contact_data_offset_handling(self):
        """Correctly uses contact_data_offset for indexing."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        # Header starts at offset 5 with 2 contacts
        headers = [
            MockContactHeader('/World/Creature', '/World/Tendroids/T0', 2, 5)
        ]
        # Pad with dummy data, real data at indices 5 and 6
        contact_data = [
            MockContactData([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),  # 0 - ignored
            MockContactData([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),  # 1 - ignored
            MockContactData([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),  # 2 - ignored
            MockContactData([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),  # 3 - ignored
            MockContactData([0.0, 0.0, 0.0], [0.0, 0.0, 0.0]),  # 4 - ignored
            MockContactData([55.0, 0.0, 0.0], [1.0, 0.0, 0.0]),  # 5 - used
            MockContactData([66.0, 0.0, 0.0], [1.0, 0.0, 0.0]),  # 6 - used
        ]

        handler._on_contact_report(headers, contact_data)

        assert len(received) == 2
        assert received[0].contact_point == (55.0, 0.0, 0.0)
        assert received[1].contact_point == (66.0, 0.0, 0.0)


# =============================================================================
# EDGE CASES - Empty/Null paths
# =============================================================================

class TestEdgeCasesEmptyPaths:
    """Tests for empty and edge case prim paths."""

    def test_empty_string_path_creature(self):
        """Empty string is not a creature."""
        assert is_creature_prim('') is False

    def test_empty_string_path_tendroid(self):
        """Empty string is not a tendroid."""
        assert is_tendroid_prim('') is False

    def test_extract_with_empty_paths(self):
        """Extract returns None for empty paths."""
        info = extract_contact_info(
            '', '',
            (0.0, 0.0, 0.0), (1.0, 0.0, 0.0)
        )
        assert info is None

    def test_whitespace_only_path(self):
        """Whitespace-only paths don't match."""
        assert is_creature_prim('   ') is False
        assert is_tendroid_prim('   ') is False


# =============================================================================
# EDGE CASES - Numeric edge cases
# =============================================================================

class TestEdgeCasesNumeric:
    """Tests for numeric edge cases in contact data."""

    def test_zero_length_normal_vector(self):
        """Handles zero-length normal vector."""
        info = extract_contact_info(
            '/World/Creature',
            '/World/Tendroids/T0',
            contact_point=(10.0, 5.0, 20.0),
            contact_normal=(0.0, 0.0, 0.0),  # Zero vector
        )
        # Should still extract - normalization is caller's responsibility
        assert info is not None
        assert info.contact_normal == (0.0, 0.0, 0.0)

    def test_nan_in_coordinates(self):
        """Handles NaN in coordinates without crashing."""
        import math
        info = extract_contact_info(
            '/World/Creature',
            '/World/Tendroids/T0',
            contact_point=(float('nan'), 5.0, 20.0),
            contact_normal=(1.0, 0.0, 0.0),
        )
        # Should extract - validation is caller's responsibility
        assert info is not None
        assert math.isnan(info.contact_point[0])

    def test_infinity_in_coordinates(self):
        """Handles infinity in coordinates without crashing."""
        import math
        info = extract_contact_info(
            '/World/Creature',
            '/World/Tendroids/T0',
            contact_point=(float('inf'), 5.0, 20.0),
            contact_normal=(1.0, 0.0, 0.0),
        )
        assert info is not None
        assert math.isinf(info.contact_point[0])

    def test_very_large_impulse(self):
        """Handles very large impulse values."""
        info = extract_contact_info(
            '/World/Creature',
            '/World/Tendroids/T0',
            contact_point=(0.0, 0.0, 0.0),
            contact_normal=(1.0, 0.0, 0.0),
            impulse=1e38,  # Very large
        )
        assert info is not None
        assert info.impulse == 1e38

    def test_negative_impulse(self):
        """Handles negative impulse (edge case from physics)."""
        info = extract_contact_info(
            '/World/Creature',
            '/World/Tendroids/T0',
            contact_point=(0.0, 0.0, 0.0),
            contact_normal=(1.0, 0.0, 0.0),
            impulse=-50.0,
        )
        assert info is not None
        assert info.impulse == -50.0


# =============================================================================
# EDGE CASES - PhysX callback edge cases
# =============================================================================

class TestPhysXCallbackEdgeCases:
    """Edge cases for PhysX callback handling."""

    def test_empty_headers_list(self):
        """Handles empty headers list gracefully."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        handler._on_contact_report([], [])

        assert len(received) == 0
        assert handler.contact_count == 0

    def test_header_with_zero_contacts(self):
        """Handles header with zero contact count."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        headers = [
            MockContactHeader('/World/Creature', '/World/Tendroids/T0', 0, 0)
        ]

        handler._on_contact_report(headers, [])

        assert len(received) == 0

    def test_contact_without_impulse_attribute(self):
        """Handles contact data missing impulse attribute."""
        handler = ContactHandler()
        received = []
        handler.add_listener(lambda e: received.append(e))

        # Create contact without impulse attribute
        class MinimalContact:
            def __init__(self):
                self.position = [1.0, 2.0, 3.0]
                self.normal = [1.0, 0.0, 0.0]
                # No impulse or separation attributes

        headers = [
            MockContactHeader('/World/Creature', '/World/Tendroids/T0', 1, 0)
        ]
        contact_data = [MinimalContact()]

        handler._on_contact_report(headers, contact_data)

        assert len(received) == 1
        assert received[0].impulse == 0.0  # Default value
        assert received[0].separation == 0.0  # Default value
