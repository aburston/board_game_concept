## ADDED Requirements

### Requirement: A Destroyed Unit Never Returns To Play

The system SHALL treat destruction as final. A destroyed unit SHALL NOT be
deployed, restored to the board, or recreated under its own name for the rest of
the game, whatever a later order asks for, and no cell falling empty SHALL bring
it back.

#### Scenario: An order would put a destroyed unit back on the board

- **WHEN** a turn is resolved and an order names a unit that has been destroyed
- **THEN** the order is not carried out
- **AND** no unit is created

#### Scenario: The cell a unit died on falls empty

- **WHEN** the cell a destroyed unit occupied when it died is empty at the start of a later turn
- **THEN** the destroyed unit does not reappear on it
- **AND** the cell stays empty unless a living unit moves onto it

#### Scenario: Another unit takes the cell a unit died on

- **WHEN** a living unit moves onto the cell a destroyed unit died on
- **THEN** it holds that cell alone
- **AND** the destroyed unit does not contest it

#### Scenario: A destroyed unit's name is not reusable

- **WHEN** a player attempts to create a new unit with the name of one of their destroyed units
- **THEN** the attempt is refused
- **AND** no unit is created

#### Scenario: A destroyed unit survives a reload as destroyed

- **WHEN** a game holding a destroyed unit is saved and loaded again
- **THEN** that unit is still destroyed and still off the board
- **AND** it takes no part in the next turn

### Requirement: An Undecided Contest Is Reported

The system SHALL tell every player whose unit was in a contest that ended
undecided that it did so, naming the unit and the cell, so that a player can see
why two units that met achieved nothing and stop paying to repeat it.

#### Scenario: A contest neither side could decide

- **WHEN** a contest ends with more than one unit undestroyed
- **THEN** each contestant's owner is told that unit's contest ended undecided, and where

#### Scenario: A contest that was decided

- **WHEN** a contest ends with at most one unit undestroyed
- **THEN** nothing is reported as undecided

## MODIFIED Requirements

### Requirement: Destroyed Units Leave The Board

The system SHALL remove destroyed units from play, marking them as no longer on
the board and taking them out of the cell they held without disturbing any unit
still standing in it. A destroyed unit SHALL be kept as a record of what was
lost, and SHALL never again act, be acted on, or occupy a cell.

#### Scenario: Removing a destroyed unit

- **WHEN** a unit is destroyed
- **THEN** it is marked as not on the board
- **AND** it no longer occupies a cell
- **AND** it is not considered for movement or combat in later turns

#### Scenario: A destroyed unit sharing a cell

- **WHEN** a unit is destroyed in a cell another unit still holds
- **THEN** the destroyed unit is taken out of that cell
- **AND** the unit still standing remains in that cell and on the board

#### Scenario: A destroyed unit is kept as a record

- **WHEN** the units of a game are listed after one has been destroyed
- **THEN** the destroyed unit is listed, marked destroyed and off the board
- **AND** it is not drawn on any cell of the board
