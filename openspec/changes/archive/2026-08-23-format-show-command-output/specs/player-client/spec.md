## MODIFIED Requirements

### Requirement: Ordering Movement

The system SHALL let a player order their own units via
`move <unit> <north|south|east|west>`. An order SHALL be resolved against the
units that player owns, so that another player holding a unit of the same name
never affects it. The units listed back after an order SHALL be listed as
`show units` lists them, in the same table and by the same renderer.

#### Scenario: Ordering a move

- **WHEN** the player runs `move` naming one of their units and a valid direction
- **THEN** the order is recorded against that unit
- **AND** the player's units are listed back as a table showing the pending order
- **AND** no storage-internal field is shown

#### Scenario: A unit name another player also uses

- **WHEN** the player runs `move` naming one of their units, and another player holds a unit of the same name
- **THEN** the order is recorded against the player's own unit
- **AND** the order is not refused

#### Scenario: Wrong argument count

- **WHEN** `move` is given other than two arguments
- **THEN** the client reports that two arguments are required and takes no action

#### Scenario: Moving before the first turn resolves

- **WHEN** `move` is run during setup
- **THEN** the client refuses, reporting that units cannot move until the first turn is complete

#### Scenario: Moving another player's unit

- **WHEN** `move` names a unit the player does not own
- **THEN** the client refuses the order, reporting that no such unit of theirs exists

#### Scenario: Moving a unit not in play

- **WHEN** `move` names a unit of the player's that is not on the board, including one that has been destroyed
- **THEN** the client refuses the order

#### Scenario: Invalid direction

- **WHEN** `move` is given a direction other than north, south, east, or west
- **THEN** the client reports the direction as invalid

### Requirement: Client Display Commands

The system SHALL let a player inspect the game within the limits of their
visibility, showing nothing the player has not seen. Each subject SHALL be
shown as a table by default and as a JSON document when the command ends in
`json`, both as `cli-output` describes them, and the JSON form SHALL be held to
the same visibility limit as the table.

#### Scenario: Showing the board

- **WHEN** the player runs `show board`
- **THEN** the board is rendered from that player's perspective, with a legend
  of the symbols they can see
- **AND** squares holding units they have not seen are drawn as empty

#### Scenario: Showing the board before one exists

- **WHEN** `show board` is run before a board exists
- **THEN** the client reports that the board must be created first

#### Scenario: Showing types

- **WHEN** the player runs `show types`
- **THEN** the player's own types are listed as a table, together with the types of enemy units they have seen
- **AND** no type of a player they have made no contact with is listed

#### Scenario: Showing units

- **WHEN** the player runs `show units`
- **THEN** the player's own units are listed as a table, together with any enemy units they have seen
- **AND** the player's destroyed units are listed with their state reading destroyed and no position
- **AND** no storage-internal field is shown

#### Scenario: Showing players

- **WHEN** the player runs `show players`
- **THEN** the registered player numbers are listed as a table
- **AND** any player known to be eliminated is marked as such in their status

#### Scenario: Showing a subject as JSON

- **WHEN** the player enters any show subject the client accepts followed by `json`
- **THEN** that subject is written as a single JSON document
- **AND** it holds nothing the table form would have withheld

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, with an unrecognised one, or with
  a trailing word other than `json`
- **THEN** the client reports the command as invalid
