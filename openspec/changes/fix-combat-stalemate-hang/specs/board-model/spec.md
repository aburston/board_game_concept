## MODIFIED Requirements

### Requirement: Unit Placement

The system SHALL place a unit on the board by copying a unit type, binding it to
a player, a name, and a coordinate pair. Placement SHALL NOT require the target
cell to be unoccupied.

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

#### Scenario: Placing onto an occupied cell

- **WHEN** a unit is placed at coordinates already holding one or more units
- **THEN** placement succeeds
- **AND** the cell holds all of those units
- **AND** the contest between them is resolved when the turn is resolved

### Requirement: Board Rendering

The system SHALL render the board either in full or from a single player's
perspective, and SHALL render a cell holding several units without failing.

#### Scenario: Full board rendering

- **WHEN** the board is rendered with no player given
- **THEN** every unit is drawn using its own symbol

#### Scenario: Player-perspective rendering

- **WHEN** the board is rendered for a given player
- **THEN** that player's units are drawn using their symbols
- **AND** all other cells are drawn as empty

#### Scenario: Rendering a shared cell in full

- **WHEN** a cell holding several units is rendered with no player given
- **THEN** the cell is drawn using the symbol of one of the units it holds
- **AND** no raw object representation is emitted

#### Scenario: Rendering a shared cell for a player

- **WHEN** a cell holding several units is rendered for a given player
- **THEN** the cell is drawn using that player's unit if one of the units is theirs
- **AND** otherwise the cell is drawn as empty
- **AND** rendering does not fail

## ADDED Requirements

### Requirement: Leaving A Cell

The system SHALL remove only the departing unit when a unit leaves a cell, and
SHALL leave any other unit in that cell where it is.

#### Scenario: Last unit leaves a cell

- **WHEN** the only unit in a cell moves away or is destroyed
- **THEN** the cell becomes empty

#### Scenario: One of several units leaves a shared cell

- **WHEN** a unit moves out of a cell it shares with another unit
- **THEN** the unit that stays remains in that cell
- **AND** it remains on the board
