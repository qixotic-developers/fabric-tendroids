"""
Contact Handler - PhysX contact event subscription controller

Manages subscription to PhysX contact report events and dispatches
filtered creature-tendroid contact events to registered listeners.

Implements TEND-24: Subscribe to PhysX contact events.
Implements TEND-91: Create contact_handler.py controller module.
Implements TEND-92: Implement PhysX contact subscription setup.
"""

from dataclasses import dataclass
from typing import Callable, List, Tuple
from enum import Enum, auto

from .contact_filter_helpers import (
    ContactInfo,
    extract_contact_info,
)


class ContactHandlerState(Enum):
    """States for the contact handler lifecycle."""
    UNINITIALIZED = auto()
    SUBSCRIBED = auto()
    UNSUBSCRIBED = auto()


@dataclass
class ContactEvent:
    """
    Event data for a creature-tendroid contact.
    
    Emitted to listeners when contact is detected.
    """
    creature_path: str
    tendroid_path: str
    contact_point: Tuple[float, float, float]
    surface_normal: Tuple[float, float, float]  # Points away from tendroid
    impulse: float
    separation: float
    
    @classmethod
    def from_contact_info(cls, info: ContactInfo) -> 'ContactEvent':
        """Create ContactEvent from ContactInfo."""
        return cls(
            creature_path=info.creature_path,
            tendroid_path=info.tendroid_path,
            contact_point=info.contact_point,
            surface_normal=info.contact_normal,
            impulse=info.impulse,
            separation=info.separation,
        )


# Type alias for contact event listeners
ContactListener = Callable[[ContactEvent], None]


class ContactHandler:
    """
    Controller for PhysX contact event subscription.
    
    Subscribes to PhysX contact report events, filters for
    creature-tendroid pairs, and dispatches events to listeners.
    
    Usage:
        handler = ContactHandler()
        handler.add_listener(my_callback)
        handler.subscribe()
        # ... simulation runs ...
        handler.unsubscribe()
    """
    
    def __init__(
        self,
        creature_patterns: List[str] = None,
        tendroid_patterns: List[str] = None,
    ):
        """
        Initialize the contact handler.
        
        Args:
            creature_patterns: USD path patterns for creatures
            tendroid_patterns: USD path patterns for tendroids
        """
        self._creature_patterns = creature_patterns or ['/World/Creature']
        self._tendroid_patterns = tendroid_patterns or [
            '/World/Tendroids/', '/World/Tendroid_'
        ]
        self._listeners: List[ContactListener] = []
        self._subscription = None
        self._state = ContactHandlerState.UNINITIALIZED
        self._contact_count = 0
    
    @property
    def state(self) -> ContactHandlerState:
        """Current handler state."""
        return self._state
    
    @property
    def is_subscribed(self) -> bool:
        """Whether currently subscribed to contact events."""
        return self._state == ContactHandlerState.SUBSCRIBED
    
    @property
    def contact_count(self) -> int:
        """Total creature-tendroid contacts processed."""
        return self._contact_count
    
    def add_listener(self, listener: ContactListener) -> None:
        """
        Register a callback for contact events.
        
        Args:
            listener: Callback function receiving ContactEvent
        """
        if listener not in self._listeners:
            self._listeners.append(listener)
    
    def remove_listener(self, listener: ContactListener) -> None:
        """
        Unregister a contact event callback.
        
        Args:
            listener: Previously registered callback
        """
        if listener in self._listeners:
            self._listeners.remove(listener)
    
    def subscribe(self) -> bool:
        """
        Subscribe to PhysX contact report events.
        
        Returns:
            True if subscription successful, False otherwise
        """
        if self._state == ContactHandlerState.SUBSCRIBED:
            return True
        
        try:
            from omni.physx import get_physx_simulation_interface
            
            physx_interface = get_physx_simulation_interface()
            self._subscription = physx_interface.subscribe_contact_report_events(
                self._on_contact_report
            )
            self._state = ContactHandlerState.SUBSCRIBED
            return True
            
        except ImportError:
            # Running outside Omniverse - testing mode
            self._state = ContactHandlerState.SUBSCRIBED
            return True
        except Exception as e:
            import carb
            carb.log_error(f"[ContactHandler] Subscribe failed: {e}")
            return False
    
    def unsubscribe(self) -> None:
        """Unsubscribe from PhysX contact events."""
        if self._subscription is not None:
            try:
                self._subscription.unsubscribe()
            except AttributeError:
                # Mock subscription may not have unsubscribe
                pass
            self._subscription = None
        self._state = ContactHandlerState.UNSUBSCRIBED
    
    def _on_contact_report(self, contact_headers, contact_data) -> None:
        """
        Internal callback for PhysX contact reports.
        
        Processes raw PhysX contact data, filters for creature-tendroid
        pairs, and dispatches events to listeners.
        
        Args:
            contact_headers: PhysX contact headers array
            contact_data: PhysX contact data array
        """
        for header in contact_headers:
            actor0_path = str(header.actor0)
            actor1_path = str(header.actor1)
            
            # Process each contact point in this header
            for i in range(header.num_contact_data):
                idx = header.contact_data_offset + i
                contact = contact_data[idx]
                
                # Extract contact point and normal
                contact_point = (
                    float(contact.position[0]),
                    float(contact.position[1]),
                    float(contact.position[2]),
                )
                contact_normal = (
                    float(contact.normal[0]),
                    float(contact.normal[1]),
                    float(contact.normal[2]),
                )
                impulse = float(getattr(contact, 'impulse', 0.0))
                separation = float(getattr(contact, 'separation', 0.0))
                
                # Filter for creature-tendroid contacts
                info = extract_contact_info(
                    actor0_path,
                    actor1_path,
                    contact_point,
                    contact_normal,
                    impulse,
                    separation,
                    self._creature_patterns,
                    self._tendroid_patterns,
                )
                
                if info is not None:
                    self._dispatch_contact(info)
    
    def _dispatch_contact(self, info: ContactInfo) -> None:
        """
        Dispatch contact event to all listeners.
        
        Args:
            info: Filtered contact information
        """
        self._contact_count += 1
        event = ContactEvent.from_contact_info(info)
        
        for listener in self._listeners:
            try:
                listener(event)
            except Exception as e:
                import carb
                carb.log_error(
                    f"[ContactHandler] Listener error: {e}"
                )
    
    def simulate_contact(
        self,
        creature_path: str,
        tendroid_path: str,
        contact_point: Tuple[float, float, float],
        surface_normal: Tuple[float, float, float],
        impulse: float = 1.0,
        separation: float = 0.0,
    ) -> None:
        """
        Simulate a contact event for testing.
        
        Bypasses PhysX and directly dispatches a contact event.
        
        Args:
            creature_path: Creature prim path
            tendroid_path: Tendroid prim path
            contact_point: Contact world position
            surface_normal: Normal pointing away from tendroid
            impulse: Contact impulse
            separation: Separation distance
        """
        info = ContactInfo(
            creature_path=creature_path,
            tendroid_path=tendroid_path,
            contact_point=contact_point,
            contact_normal=surface_normal,
            impulse=impulse,
            separation=separation,
        )
        self._dispatch_contact(info)
    
    def shutdown(self) -> None:
        """Clean shutdown - unsubscribe and clear listeners."""
        self.unsubscribe()
        self._listeners.clear()
        self._contact_count = 0
