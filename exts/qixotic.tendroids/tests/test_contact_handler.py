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
