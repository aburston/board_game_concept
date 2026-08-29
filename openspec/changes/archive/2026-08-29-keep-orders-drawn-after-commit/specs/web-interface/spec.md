## MODIFIED Requirements

### Requirement: An Order In Flight Is Drawn On The Board

The system SHALL draw, for each of the player's units under orders, the
direction it has been ordered in, out of the unit and towards the square it
would move to, and SHALL draw it distinctly enough to be read at a glance.

An order SHALL stay drawn once the turn is committed, until the turn resolves.
Committing publishes the orders and locks them, but does not carry them out, so
the units still stand where they did; a board that stopped drawing them on
commit showed the player who had just committed a whole plan a board that
looked as though they had done nothing.

#### Scenario: A unit under orders

- **WHEN** a unit has been ordered to move
- **THEN** an arrow from that unit towards the square it is headed for is
  drawn on the board

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
