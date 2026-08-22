## ADDED Requirements

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

## MODIFIED Requirements

### Requirement: Unit Name Uniqueness Per Player

The system SHALL allow different players to reuse the same unit name, while
requiring each unit name to be unique within a single player's forces. When a
placement is refused for that reason, the error SHALL name the unit and the
player it belongs to.

#### Scenario: Two players use the same unit name

- **WHEN** player 1 and player 2 each place a unit named `scout`
- **THEN** both placements succeed

#### Scenario: One player reuses a unit name

- **WHEN** a player places a second unit with a name they already used
- **THEN** placement fails
- **AND** the error names the unit and that player, rather than failing while it is being reported
