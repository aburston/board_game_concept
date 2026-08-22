## MODIFIED Requirements

### Requirement: Deploying Units

The system SHALL let a player deploy units during setup via
`add unit <type> <name> <x> <y>`, and SHALL refuse a deployment onto a square
the client already knows is taken, without ending the session.

#### Scenario: Deploying a unit

- **WHEN** the player runs `add unit` with a known type, a name, and coordinates
- **THEN** a unit of that type is placed at those coordinates for that player

#### Scenario: Wrong argument count

- **WHEN** `add unit` is given other than four arguments
- **THEN** the client reports that four arguments are required and takes no action

#### Scenario: No board loaded

- **WHEN** `add unit` is run before a board exists
- **THEN** the client reports that the board must be loaded first

#### Scenario: Deploying after setup

- **WHEN** `add unit` is run after the first turn has been resolved
- **THEN** the client refuses, reporting that units cannot be added after the first turn

#### Scenario: Invalid deployment

- **WHEN** `add unit` names an unknown type, or gives coordinates outside the board, or reuses one of the player's unit names
- **THEN** the client reports the error and takes no action

#### Scenario: Deploying onto a square the player already holds

- **WHEN** `add unit` names coordinates the player has already placed a unit on
- **THEN** the client reports that the square is occupied and takes no action
- **AND** the session continues and accepts further commands

## ADDED Requirements

### Requirement: Reporting Rejected Orders

The system SHALL show the player any order the server refused when it last
resolved a turn, before taking their next command.

#### Scenario: An order was rejected

- **WHEN** the client starts a session and the server refused one or more of that player's orders on the last resolved turn
- **THEN** the client reports how many were rejected
- **AND** names the unit, its coordinates, and the reason for each

#### Scenario: Nothing was rejected

- **WHEN** the client starts a session and none of that player's orders were refused
- **THEN** the client reports nothing and prompts as usual

#### Scenario: Rejections describe only the last resolved turn

- **WHEN** a turn is resolved in which none of a player's orders are refused
- **THEN** any rejection from an earlier turn is no longer reported to them
