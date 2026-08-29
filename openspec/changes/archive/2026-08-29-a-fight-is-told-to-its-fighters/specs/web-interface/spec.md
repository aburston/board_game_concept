## ADDED Requirements

### Requirement: The Controls For Ordering Are In The Board's Pane

The system SHALL put the controls that order the selected unit in the same
pane as the board, beneath it, so that choosing a unit, ordering it and seeing
the order drawn all happen in one place. They SHALL NOT be in a separate card
across the screen from the board they act on.

The controls SHALL be laid out as a **compass**: the four headings placed
where the squares they point at are, around a fifth in the centre that means
"stay where you are". Each SHALL be drawn as the arrow for its heading rather
than as its name, and the centre as a mark of its own; each SHALL carry the
words for a reader that cannot see the arrow.

The centre SHALL be offered whether or not the unit is under orders. Holding
is a choice a player makes — a unit given no order recovers a point — and it
is the same control whether it is choosing to stay or taking back an order
given a moment ago. Where there is an order to take back, the centre SHALL say
so and be drawn as the thing that undoes it.

#### Scenario: Ordering a unit

- **WHEN** a unit is selected
- **THEN** the controls for it are shown under the board
- **AND** pressing one draws the order on the board above them

#### Scenario: Laid out as a compass

- **WHEN** the controls are shown
- **THEN** north is above the centre and south below it
- **AND** west is left of the centre and east right of it

#### Scenario: The centre with no order to take back

- **WHEN** the selected unit has no order
- **THEN** the centre is still offered, as holding

#### Scenario: The centre with an order to take back

- **WHEN** the selected unit is under orders
- **THEN** the centre says it takes the order back
- **AND** pressing it leaves the unit with no order

#### Scenario: Read without seeing the arrows

- **WHEN** the controls are read by something that cannot see a glyph
- **THEN** each is named by what it does

#### Scenario: Nothing selected

- **WHEN** no unit is selected
- **THEN** the board pane says to choose one rather than showing controls
  that would do nothing

### Requirement: A Unit's Ring Shows The Energy It Has Left

The system SHALL draw each unit's outer ring in proportion to the energy it
has left against the energy its type was designed with, so that a spent unit
can be told from a fresh one on the board itself rather than only in a table.

A unit that cannot pay for what it wants to do is the thing a player most
needs to see before ordering it, and the board is what they are looking at.

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
