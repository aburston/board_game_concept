## ADDED Requirements

### Requirement: Coordinate System

The system SHALL address a cell as an `(x, y)` pair, with `x` increasing to the
east and `y` increasing to the south, both counted from zero, so that `(0, 0)`
is the north-west cell of the board.

#### Scenario: The origin

- **WHEN** a board of any size is created
- **THEN** the cell `(0, 0)` is its north-west corner
- **AND** the cell `(size_x - 1, size_y - 1)` is its south-east corner

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
unit in the board's unit list, no claim on the cell, and no type recorded
against the player on account of the refused unit.

#### Scenario: A placement refused for a duplicate name

- **WHEN** a placement is refused because the player already holds a unit of that name
- **THEN** no unit is added to the board's unit list
- **AND** no cell is claimed by the refused unit
- **AND** a later placement of that name at a free cell is judged as though the refusal had not happened

#### Scenario: A placement refused for an occupied cell

- **WHEN** a placement is refused because the cell is taken
- **THEN** no unit is added to the board's unit list
- **AND** the cell holds only the unit that already held it

#### Scenario: A refused placement does not block another cell

- **WHEN** a placement is refused and another unit is then placed on the cell the refused unit named
- **THEN** that placement succeeds

## MODIFIED Requirements

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

- **WHEN** a cell is requested by coordinate
- **THEN** the cell's current contents are returned, which may be an empty marker, a single unit, or a contested list of units
