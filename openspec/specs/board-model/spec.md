# board-model Specification

## Purpose

The board is the shared playing surface and the authoritative record of where
every unit stands. It owns unit registration, coordinate lookup, and rendering.
All players act against one board instance held by the server.

## Requirements

### Requirement: Board Creation

The system SHALL create a rectangular board of configurable dimensions, with
every cell initially empty.

#### Scenario: Creating a board

- **WHEN** a board is created with size_x 4 and size_y 4
- **THEN** the board reports those dimensions
- **AND** every cell contains an empty marker

#### Scenario: Dimensions must be 2 to 10

- **WHEN** a board is created with a non-integer dimension, or a dimension below 2 or above 10
- **THEN** creation fails

### Requirement: Empty Cell Representation

The system SHALL represent an unoccupied cell with a distinct empty marker that
renders as `#`.

#### Scenario: Rendering an empty cell

- **WHEN** an empty cell is rendered
- **THEN** it displays as `#`

### Requirement: Unit Placement

The system SHALL place a unit on the board by copying a unit type, binding it to
a player, a name, and a coordinate pair.

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

### Requirement: Unit Name Uniqueness Per Player

The system SHALL allow different players to reuse the same unit name, while
requiring each unit name to be unique within a single player's forces.

#### Scenario: Two players use the same unit name

- **WHEN** player 1 and player 2 each place a unit named `scout`
- **THEN** both placements succeed

#### Scenario: One player reuses a unit name

- **WHEN** a player places a second unit with a name they already used
- **THEN** placement fails

### Requirement: Unit Lookup

The system SHALL support retrieving units by name, by identifier, and by
coordinate.

#### Scenario: Lookup by name across all players

- **WHEN** a unit is requested by name with no player given
- **THEN** every unit with that name is returned

#### Scenario: Lookup by name scoped to a player

- **WHEN** a unit is requested by name for a specific player
- **THEN** only that player's unit with that name is returned

#### Scenario: Lookup by unknown name

- **WHEN** a unit is requested by a name no unit holds
- **THEN** lookup fails with a does-not-exist error

#### Scenario: Lookup by identifier

- **WHEN** a unit is requested by an identifier outside the range of placed units
- **THEN** lookup fails with a does-not-exist error

#### Scenario: Lookup by coordinate

- **WHEN** a cell is requested by coordinate
- **THEN** the cell's current contents are returned, which may be an empty marker, a single unit, or a contested list of units

### Requirement: Board Rendering

The system SHALL render the board either in full or from a single player's
perspective.

#### Scenario: Full board rendering

- **WHEN** the board is rendered with no player given
- **THEN** every unit is drawn using its own symbol

#### Scenario: Player-perspective rendering

- **WHEN** the board is rendered for a given player
- **THEN** that player's units are drawn using their symbols
- **AND** all other cells are drawn as empty

### Requirement: Optional Board Backend

The system SHALL use the third-party `board` library for cell storage when it is
installed, and SHALL fall back to an equivalent built-in grid when it is not, so
that the game runs without that optional dependency.

#### Scenario: Running without the optional library

- **WHEN** the `board` library is not installed
- **THEN** the board still stores, retrieves, and draws cells identically
