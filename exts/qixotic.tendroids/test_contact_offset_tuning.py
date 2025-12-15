"""
Visual Verification Test for Contact Offsets

Run this script in Omniverse Script Editor to visually verify
and tune the creature collider contact offset parameters.

Implements TEND-60: Verify and tune offset values visually.

Usage:
    1. Open in Omniverse Script Editor
    2. Run the script
    3. Use keyboard controls to adjust offsets:
        - UP/DOWN: Adjust contact offset
        - LEFT/RIGHT: Adjust rest offset
        - V: Toggle collider visibility
        - R: Reset to default values
        - P: Print current values
"""

import omni.usd
import carb.input
from pxr import Gf

# Import our modules
from qixotic.tendroids.controllers.creature_collider_helper import (
    update_contact_offsets,
    get_contact_offsets,
    set_collider_visibility,
)
from qixotic.tendroids.controllers.envelope_constants import (
    CONTACT_OFFSET,
    REST_OFFSET,
)


# =============================================================================
# Configuration
# =============================================================================

CREATURE_PATH = "/World/Creature"
OFFSET_STEP = 0.01  # 1cm per keypress
MIN_OFFSET = 0.001  # 1mm minimum
MAX_OFFSET = 0.5    # 50cm maximum


# =============================================================================
# State
# =============================================================================

class TuningState:
    """Track current tuning state."""
    contact_offset = CONTACT_OFFSET
    rest_offset = REST_OFFSET
    collider_visible = True
    subscription = None


state = TuningState()


# =============================================================================
# Functions
# =============================================================================

def print_current_values():
    """Print current offset values to console."""
    stage = omni.usd.get_context().get_stage()
    values = get_contact_offsets(stage, CREATURE_PATH)
    
    if values:
        print(f"\n{'='*50}")
        print("CONTACT OFFSET TUNING")
        print(f"{'='*50}")
        print(f"  Contact Offset: {values['contact_offset']:.4f} m ({values['contact_offset']*100:.2f} cm)")
        print(f"  Rest Offset:    {values['rest_offset']:.4f} m ({values['rest_offset']*100:.2f} cm)")
        print(f"  Difference:     {(values['contact_offset'] - values['rest_offset']):.4f} m")
        print(f"{'='*50}")
        print("Controls:")
        print("  UP/DOWN    - Adjust contact offset")
        print("  LEFT/RIGHT - Adjust rest offset")
        print("  V          - Toggle visibility")
        print("  R          - Reset to defaults")
        print("  P          - Print values")
        print(f"{'='*50}\n")
    else:
        print("[ERROR] Could not get contact offset values")


def adjust_contact_offset(delta: float):
    """Adjust contact offset by delta."""
    stage = omni.usd.get_context().get_stage()
    
    new_value = state.contact_offset + delta
    new_value = max(MIN_OFFSET, min(MAX_OFFSET, new_value))
    
    # Ensure contact >= rest
    if new_value < state.rest_offset:
        print(f"[WARN] Contact offset cannot be less than rest offset ({state.rest_offset})")
        new_value = state.rest_offset
    
    if update_contact_offsets(stage, CREATURE_PATH, contact_offset=new_value):
        state.contact_offset = new_value
        print(f"Contact Offset: {new_value:.4f} m ({new_value*100:.2f} cm)")


def adjust_rest_offset(delta: float):
    """Adjust rest offset by delta."""
    stage = omni.usd.get_context().get_stage()
    
    new_value = state.rest_offset + delta
    new_value = max(MIN_OFFSET, min(MAX_OFFSET, new_value))
    
    # Ensure rest <= contact
    if new_value > state.contact_offset:
        print(f"[WARN] Rest offset cannot exceed contact offset ({state.contact_offset})")
        new_value = state.contact_offset
    
    if update_contact_offsets(stage, CREATURE_PATH, rest_offset=new_value):
        state.rest_offset = new_value
        print(f"Rest Offset: {new_value:.4f} m ({new_value*100:.2f} cm)")


def toggle_visibility():
    """Toggle collider visibility."""
    stage = omni.usd.get_context().get_stage()
    state.collider_visible = not state.collider_visible
    set_collider_visibility(stage, CREATURE_PATH, state.collider_visible)
    print(f"Collider visibility: {'ON' if state.collider_visible else 'OFF'}")


def reset_to_defaults():
    """Reset offsets to default values."""
    stage = omni.usd.get_context().get_stage()
    
    if update_contact_offsets(stage, CREATURE_PATH, 
                              contact_offset=CONTACT_OFFSET,
                              rest_offset=REST_OFFSET):
        state.contact_offset = CONTACT_OFFSET
        state.rest_offset = REST_OFFSET
        print(f"Reset to defaults: contact={CONTACT_OFFSET}, rest={REST_OFFSET}")


def on_key_event(event):
    """Handle keyboard input for tuning."""
    if event.type == carb.input.KeyboardEventType.KEY_PRESS:
        key = event.input
        
        if key == carb.input.KeyboardInput.UP:
            adjust_contact_offset(OFFSET_STEP)
        elif key == carb.input.KeyboardInput.DOWN:
            adjust_contact_offset(-OFFSET_STEP)
        elif key == carb.input.KeyboardInput.RIGHT:
            adjust_rest_offset(OFFSET_STEP)
        elif key == carb.input.KeyboardInput.LEFT:
            adjust_rest_offset(-OFFSET_STEP)
        elif key == carb.input.KeyboardInput.V:
            toggle_visibility()
        elif key == carb.input.KeyboardInput.R:
            reset_to_defaults()
        elif key == carb.input.KeyboardInput.P:
            print_current_values()


def start_tuning():
    """Start the contact offset tuning mode."""
    print("\n" + "="*60)
    print("CONTACT OFFSET VISUAL TUNING - STARTED")
    print("="*60)
    
    # Initialize state from current values
    stage = omni.usd.get_context().get_stage()
    values = get_contact_offsets(stage, CREATURE_PATH)
    if values:
        state.contact_offset = values['contact_offset']
        state.rest_offset = values['rest_offset']
    
    # Make collider visible for tuning
    set_collider_visibility(stage, CREATURE_PATH, True)
    state.collider_visible = True
    
    # Subscribe to keyboard input
    input_iface = carb.input.acquire_input_interface()
    keyboard = input_iface.get_keyboard()
    state.subscription = input_iface.subscribe_to_keyboard_events(
        keyboard, on_key_event
    )
    
    print_current_values()
    print("\nTuning mode active. Use arrow keys to adjust.")
    print("Run stop_tuning() to exit.\n")


def stop_tuning():
    """Stop the contact offset tuning mode."""
    if state.subscription:
        input_iface = carb.input.acquire_input_interface()
        input_iface.unsubscribe_to_keyboard_events(
            input_iface.get_keyboard(), 
            state.subscription
        )
        state.subscription = None
    
    print("\nTuning mode stopped.")
    print_current_values()


# =============================================================================
# Auto-run
# =============================================================================

if __name__ == "__main__":
    start_tuning()
