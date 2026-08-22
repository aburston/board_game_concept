## MODIFIED Requirements

### Requirement: Unit Placement

The system SHALL place a unit on the board by copying a unit type, binding it to
a player, a name, and a coordinate pair. Placement SHALL require the target
square to be free: neither held by a unit nor already claimed by a unit waiting
to be placed. Restoring a saved game is not a placement and SHALL NOT be subject
to that rule.

#### Scenario: Placing a unit

- **WHEN** a player places a unit of a given type at coordinates within the board
- **THEN** a new unit instance is created from that type
- **AND** the unit is bound to the placing player, the given name, and those coordinates
- **AND** the unit is registered in the board's unit list and returned an identifier

#### Scenario: Placement outside the board is rejected

- **WHEN** a unit is placed at coordinates outside the board bounds
- **THEN** placement fails with an out-of-bounds error

#### Scenario: Placement records the type against the player

- **WHEN** a unit of a previously unseen type is placed by a player
- **THEN** that type is recorded under that player's set of known types

#### Scenario: Placing onto an occupied square is rejected

- **WHEN** a unit is placed at coordinates already holding one or more units
- **THEN** placement fails with an error naming the unit and the square
- **AND** the unit is not registered in the board's unit list

#### Scenario: Placing onto a square another unit is waiting to occupy

- **WHEN** a unit is placed at coordinates another unit has been placed at but the turn has not yet been resolved
- **THEN** placement fails with the same error
- **AND** the unit placed first keeps its claim on the square

#### Scenario: Restoring a saved game onto occupied squares

- **WHEN** a saved game is restored and two of its units share a square
- **THEN** both are recreated on that square
- **AND** the occupancy rule does not refuse either of them

### Requirement: Board Rendering

The system SHALL render the board either in full or from a single player's
perspective, and SHALL render a square holding several units without failing.

#### Scenario: Full board rendering

- **WHEN** the board is rendered with no player given
- **THEN** every unit is drawn using its own symbol

#### Scenario: Player-perspective rendering

- **WHEN** the board is rendered for a given player
- **THEN** that player's units are drawn using their symbols
- **AND** all other cells are drawn as empty

#### Scenario: Rendering a shared square in full

- **WHEN** a square holding several units is rendered with no player given
- **THEN** the square is drawn using the symbol of one of the units it holds
- **AND** no raw object representation is emitted

#### Scenario: Rendering a shared square for a player

- **WHEN** a square holding several units is rendered for a given player
- **THEN** the square is drawn using that player's unit if one of the units is theirs
- **AND** otherwise the square is drawn as empty
- **AND** rendering does not fail

## ADDED Requirements

### Requirement: Leaving A Square

The system SHALL remove only the departing unit when a unit leaves a square, and
SHALL leave any other unit in that square where it is.

#### Scenario: Last unit leaves a square

- **WHEN** the only unit in a square moves away or is destroyed
- **THEN** the square becomes empty

#### Scenario: One of several units leaves a shared square

- **WHEN** a unit moves out of a square it shares with another unit
- **THEN** the unit that stays remains in that square
- **AND** it remains on the board
