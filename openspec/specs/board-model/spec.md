# board-model Specification

## Purpose

The board is the shared playing surface and the authoritative record of where
every unit stands. It owns unit registration, coordinate lookup, and rendering.
All players act against one board instance held by the server.

## Requirements

### Requirement: Board Creation

The system SHALL create a rectangular board of configurable dimensions, with
every square initially empty.

#### Scenario: Creating a board

- **WHEN** a board is created with size_x 4 and size_y 4
- **THEN** the board reports those dimensions
- **AND** every square contains an empty marker

#### Scenario: Dimensions must be 2 to 10

- **WHEN** a board is created with a non-integer dimension, or a dimension below 2 or above 10
- **THEN** creation fails

### Requirement: Empty Square Representation

The system SHALL represent an unoccupied square with a distinct empty marker that
renders as `#`.

#### Scenario: Rendering an empty square

- **WHEN** an empty square is rendered
- **THEN** it displays as `#`

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

### Requirement: Restoring A Unit The Board Already Holds

Restoring a saved game SHALL recognise a unit the board already holds for that
player and put the saved state back into it, rather than creating a second unit
with the same name or failing. A saved view that names the same unit more than
once SHALL therefore load, and SHALL leave the board holding one unit for that
name and player.

#### Scenario: A saved view names the same unit twice

- **WHEN** a saved game or per-player view is restored and it names the same unit twice for the same player
- **THEN** the board holds one unit with that name for that player
- **AND** restoring does not fail

#### Scenario: The last saved state is the one restored

- **WHEN** a unit already restored for a player is restored again with coordinates, health, energy, destroyed and on-board state
- **THEN** the unit the board holds carries that state
- **AND** no second unit is registered in the board's unit list

#### Scenario: Restoring is not placement

- **WHEN** a unit is placed rather than restored and that player already holds a unit with that name
- **THEN** placement fails

### Requirement: Unit Name Uniqueness Per Player

The system SHALL allow different players to reuse the same unit name, while
requiring each unit name to be unique within a single player's forces. When a
placement is refused for that reason, the error SHALL name the unit and the
player it belongs to, and the board SHALL be left holding no trace of the
refused unit.

#### Scenario: Two players use the same unit name

- **WHEN** player 1 and player 2 each place a unit named `scout`
- **THEN** both placements succeed

#### Scenario: One player reuses a unit name

- **WHEN** a player places a second unit with a name they already used
- **THEN** placement fails
- **AND** the error names the unit and that player, rather than failing while it is being reported
- **AND** the board's unit list is unchanged

### Requirement: Unit Lookup

The system SHALL support retrieving units by name, by identifier, and by
coordinate. A lookup scoped to a player SHALL return that player's unit whatever
order the units were registered in, and SHALL never return another player's
unit.

#### Scenario: Lookup by name across all players

- **WHEN** a unit is requested by name with no player given
- **THEN** every unit with that name is returned

#### Scenario: Lookup by name scoped to a player

- **WHEN** a unit is requested by name for a specific player
- **THEN** only that player's unit with that name is returned

#### Scenario: Another player registered the name first

- **WHEN** a unit is requested by name for a player, and another player registered a unit of the same name before them
- **THEN** the requesting player's own unit is returned
- **AND** the other player's unit is not returned

#### Scenario: Lookup by unknown name

- **WHEN** a unit is requested by a name no unit holds
- **THEN** lookup fails with a does-not-exist error

#### Scenario: Lookup by identifier

- **WHEN** a unit is requested by an identifier outside the range of placed units
- **THEN** lookup fails with a does-not-exist error

#### Scenario: Lookup by coordinate

- **WHEN** a square is requested by coordinate
- **THEN** the square's current contents are returned, which may be an empty marker, a single unit, or a contested list of units

### Requirement: Board Rendering

The system SHALL render the board either in full or from a single player's
perspective, and SHALL render a square holding several units without failing.

#### Scenario: Full board rendering

- **WHEN** the board is rendered with no player given
- **THEN** every unit is drawn using its own symbol

#### Scenario: Player-perspective rendering

- **WHEN** the board is rendered for a given player
- **THEN** that player's units are drawn using their symbols
- **AND** all other squares are drawn as empty

#### Scenario: Rendering a shared square in full

- **WHEN** a square holding several units is rendered with no player given
- **THEN** the square is drawn using the symbol of one of the units it holds
- **AND** no raw object representation is emitted

#### Scenario: Rendering a shared square for a player

- **WHEN** a square holding several units is rendered for a given player
- **THEN** the square is drawn using that player's unit if one of the units is theirs
- **AND** otherwise the square is drawn as empty
- **AND** rendering does not fail

### Requirement: Optional Board Backend

The system SHALL use the third-party `board` library for square storage when it is
installed, and SHALL fall back to an equivalent built-in grid when it is not, so
that the game runs without that optional dependency.

#### Scenario: Running without the optional library

- **WHEN** the `board` library is not installed
- **THEN** the board still stores, retrieves, and draws squares identically

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

### Requirement: Coordinate System

The system SHALL address a square as an `(x, y)` pair, with `x` increasing to the
east and `y` increasing to the south, both counted from zero, so that `(0, 0)`
is the north-west square of the board.

#### Scenario: The origin

- **WHEN** a board of any size is created
- **THEN** the square `(0, 0)` is its north-west corner
- **AND** the square `(size_x - 1, size_y - 1)` is its south-east corner

#### Scenario: Rendering order follows the coordinates

- **WHEN** the board is rendered
- **THEN** the row with `y` 0 is drawn first
- **AND** within a row, `x` increases from left to right

#### Scenario: Directions agree with the coordinates

- **WHEN** the direction a unit may be ordered in is interpreted
- **THEN** north decreases `y`, south increases `y`, east increases `x`, and west decreases `x`

### Requirement: A Refused Placement Registers Nothing

The system SHALL validate a placement completely before it registers a unit, so
that a placement refused for any reason leaves the board exactly as it was: no
unit in the board's unit list, no claim on the square, and no type recorded
against the player on account of the refused unit.

#### Scenario: A placement refused for a duplicate name

- **WHEN** a placement is refused because the player already holds a unit of that name
- **THEN** no unit is added to the board's unit list
- **AND** no square is claimed by the refused unit
- **AND** a later placement of that name at a free square is judged as though the refusal had not happened

#### Scenario: A placement refused for an occupied square

- **WHEN** a placement is refused because the square is taken
- **THEN** no unit is added to the board's unit list
- **AND** the square holds only the unit that already held it

#### Scenario: A refused placement does not block another square

- **WHEN** a placement is refused and another unit is then placed on the square the refused unit named
- **THEN** that placement succeeds
