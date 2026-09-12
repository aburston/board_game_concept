## MODIFIED Requirements

### Requirement: An Order In Flight Is Drawn On The Board

The system SHALL draw, for each of the player's units under orders, the
direction it has been ordered in, out of the unit and towards the square it
would move to, and SHALL draw it distinctly enough to be read at a glance.

The arrow SHALL be drawn as an outline: a single hollow arrow shape, shaft and
head together, stroked in the order colour with no fill, so that what it
crosses - the edge of its own square, and whatever stands in the square it
points at - stays visible through it. It SHALL NOT be drawn as a solid bar or
a filled head.

The arrow SHALL start clear of the unit's own markings - outside its ring and
its energy arc - and its tip SHALL cross the edge of the unit's square into the
square it is headed for, so that the square it names is unambiguous. It SHALL
reach no further into that square than a quarter of the square's width, so
that a unit standing there is not drawn over.

An order SHALL stay drawn once the turn is committed, until the turn resolves.
Committing publishes the orders and locks them, but does not carry them out, so
the units still stand where they did; a board that stopped drawing them on
commit showed the player who had just committed a whole plan a board that
looked as though they had done nothing.

#### Scenario: A unit under orders

- **WHEN** a unit has been ordered to move
- **THEN** an arrow from that unit towards the square it is headed for is
  drawn on the board

#### Scenario: The arrow is hollow

- **WHEN** an order arrow is drawn
- **THEN** it is one outlined shape in the order colour, with no filled shaft
  and no filled head

#### Scenario: The arrow reaches into the next square, but only just

- **WHEN** an order arrow is drawn for a unit
- **THEN** its tip lies past the edge of the unit's square, inside the square
  it is headed for
- **AND** its tip lies no more than a quarter of a square's width past that
  edge

#### Scenario: The arrow does not cross the unit's own markings

- **WHEN** an order arrow is drawn for a unit
- **THEN** it begins outside the unit's ring and energy arc

#### Scenario: A unit holding

- **WHEN** a unit has no order
- **THEN** no arrow is drawn for it

#### Scenario: Orders stay drawn after the turn is committed

- **WHEN** the player commits a turn in which units were ordered to move, and the turn has not yet resolved
- **THEN** the arrows for those committed moves are still drawn on the board
- **AND** the screen still says the turn is committed and cannot be changed until it resolves

#### Scenario: The board is cleared of orders once the turn resolves

- **WHEN** the committed turn resolves
- **THEN** the board is drawn from the resolved positions, with no arrow left from the turn that resolved
