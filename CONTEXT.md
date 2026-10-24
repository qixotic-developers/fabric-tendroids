# Tendroids

An Omniverse simulation in which a creature moves among tendroids that bend and sway, and reacts when they touch.

## Language

**Contact**:
The creature overlapping the visible (bent and waved) surface of a tendroid. A tendroid that bends away in time causes no contact.
_Avoid_: Collision, hit, touch

**Deflection**:
A tendroid bending away in anticipation of the creature's approach. It is triggered by the creature approaching the tendroid's rest shape, not by contact.
_Avoid_: Dodge, bend (for the trigger)

**Shock**:
The creature's immediate reaction to a contact: shock color, repulsion away from the surface, and loss of keyboard control.
_Avoid_: Hit reaction, stun

**Recovery**:
The period after a shock until the creature has moved clear and regains keyboard control. A new contact during recovery starts a new shock.
_Avoid_: Cooldown

**Contact proxy**:
The set of spheres that stands in for the creature's body when testing for contact. Currently a single sphere; the creature's shape is expected to evolve.
_Avoid_: Creature radius, hitbox, collider
