## MODIFIED Requirements

### Requirement: A Unit's Ring Shows The Energy It Has Left

The system SHALL draw each unit's outer ring in proportion to the energy it
has left against the energy its type was designed with, so that a spent unit
can be told from a fresh one on the board itself rather than only in a table.

A unit that cannot pay for what it wants to do is the thing a player most
needs to see before ordering it, and the board is what they are looking at.

The proportion SHALL be drawn **outside** the ring rather than over it. The
ring is what says whose a unit is — its colour, and the dashed outline an
enemy is given — and an arc painted along the same line hid that, worst on a
unit with most of its energy left, which covers most of its own ring. The
ring SHALL be drawn whole and uncovered whatever the proportion, and the arc
SHALL stay within the unit's square.

The arc SHALL be coloured by **how much is left, not by whose the unit is**:

- above two thirds, green;
- from a third to two thirds, amber;
- at a third or below, red.

The colours SHALL be distinguishable in both the light and the dark scheme,
and level SHALL NOT be told by colour alone — the length of the arc says it
too, and the exact figures are given in the unit's own description and in the
orders tray.

#### Scenario: A unit with all its energy

- **WHEN** a unit has the energy its type was designed with
- **THEN** its ring is drawn complete

#### Scenario: A unit part spent

- **WHEN** a unit has some of its energy left
- **THEN** that share of its ring is drawn, and the rest is not

#### Scenario: A spent unit

- **WHEN** a unit has no energy left
- **THEN** none of the proportion is drawn, and the unit is still drawn on its
  square

#### Scenario: A unit whose energy is not known

- **WHEN** a unit's type is not known to this seat, so what it was designed
  with cannot be said
- **THEN** the ring is drawn plainly rather than as a proportion of nothing

#### Scenario: The ring is not covered by the arc

- **WHEN** a unit has most of its energy left
- **THEN** its ring is drawn whole, in the colour that says whose it is
- **AND** the arc is drawn outside the ring, covering none of it

#### Scenario: Energy read by colour

- **WHEN** a unit has most of its energy
- **THEN** the arc is green
- **AND** it is amber where a third to two thirds is left, and red at a third
  or below

#### Scenario: An enemy's energy is read the same way

- **WHEN** an enemy unit this seat can see is low on energy
- **THEN** its arc is red, as one of the seat's own would be
- **AND** the unit is still shown to be an enemy by its ring and its glyph

### Requirement: Every Unit's Health Is Shown Against What It Was Built With

The system SHALL show, for every unit it draws, the health that unit has left
and the health its type was designed with, and SHALL do so on the board and in
the orders tray rather than only where a pointer is held still.

A unit a blow from destruction and a unit nobody has touched SHALL NOT be
drawn alike.

The health drawn on the board SHALL be coloured by **how much is left, not by
whose the unit is**, in the same three bands and at the same boundaries as a
unit's energy — green above two thirds, amber from a third to two thirds, red
at a third or below — so that the two things drawn round a unit are read the
same way and a player learns one scale rather than two.

This SHALL hold for every unit drawn, an enemy's as well as the seat's own,
so that a player can see which enemy is nearly finished. Whose a unit is SHALL
still be said, by its ring and its glyph.

Level SHALL NOT be told by colour alone: the length of the bar says it too,
and the figures are given in the unit's description and in the tray.

#### Scenario: A unit that has been fought

- **WHEN** a unit has lost health
- **THEN** what it has left and what it was built with are both shown
- **AND** it is drawn differently from a unit at full health

#### Scenario: On a device with no pointer

- **WHEN** the interface is used on a touchscreen
- **THEN** health is readable without hovering anything

#### Scenario: Health read by colour

- **WHEN** a unit has most of its health
- **THEN** its health is drawn green
- **AND** amber where a third to two thirds is left, and red at a third or
  below

#### Scenario: The same scale for health and energy

- **WHEN** a unit's health and its energy are at the same share of what they
  were built with
- **THEN** both are drawn in the same colour

#### Scenario: An enemy nearly finished

- **WHEN** an enemy unit this seat can see is down to a third of its health
- **THEN** its health is drawn red
- **AND** the unit is still shown to be an enemy

#### Scenario: A watched board

- **WHEN** a watching session is drawing units coloured by player number
- **THEN** health and energy are still drawn by how much is left
- **AND** which player a unit belongs to is still said by its ring and its
  glyph
