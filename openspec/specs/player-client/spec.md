# player-client Specification

## Purpose

The player client is the interactive command-line interface a player uses to
design unit types, deploy units, order movement, and commit a turn. It is
launched per game and per player and shows only what that player is entitled to
see.

## Requirements

### Requirement: Client Invocation

The system SHALL launch a client session bound to one game and one player.

#### Scenario: Starting a client

- **WHEN** the client is started with a game number and a player number
- **THEN** it opens that game as that player

#### Scenario: Wrong arguments

- **WHEN** the client is started without both a game number and a player number
- **THEN** it prints usage and exits with a failure status

### Requirement: Client Command Loop

The system SHALL read commands interactively, ignore blank input, and report
unrecognised commands without ending the session.

#### Scenario: Blank input

- **WHEN** the player enters a blank line
- **THEN** the client prompts again and takes no action

#### Scenario: Unrecognised command

- **WHEN** the player enters an unrecognised command
- **THEN** the client reports the command as invalid and prompts again

#### Scenario: Help

- **WHEN** the player enters `help`
- **THEN** the client lists the available commands and their arguments

#### Scenario: Exit

- **WHEN** the player enters `exit`
- **THEN** the client session ends

### Requirement: Defining Unit Types

The system SHALL let a player define unit types during setup via
`add type <name> <symbol> <attack> <health> <energy>`.

#### Scenario: Defining a type

- **WHEN** the player runs `add type` with a name, symbol, attack, health, and energy
- **THEN** the type is recorded against that player

#### Scenario: Wrong argument count

- **WHEN** `add type` is given other than five arguments
- **THEN** the client reports that five arguments are required and takes no action

#### Scenario: Defining a type after setup

- **WHEN** `add type` is run after the first turn has been resolved
- **THEN** the client refuses, reporting that types cannot be added after the first turn

#### Scenario: Invalid statistics

- **WHEN** `add type` is given statistics outside their permitted ranges
- **THEN** the client reports the error and takes no action

### Requirement: Deploying Units

The system SHALL let a player deploy units during setup via
`add unit <type> <name> <x> <y>`.

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

### Requirement: Ordering Movement

The system SHALL let a player order their own units via
`move <unit> <north|south|east|west>`.

#### Scenario: Ordering a move

- **WHEN** the player runs `move` naming one of their units and a valid direction
- **THEN** the order is recorded against that unit
- **AND** the player's units are listed back showing the pending order

#### Scenario: Wrong argument count

- **WHEN** `move` is given other than two arguments
- **THEN** the client reports that two arguments are required and takes no action

#### Scenario: Moving before the first turn resolves

- **WHEN** `move` is run during setup
- **THEN** the client refuses, reporting that units cannot move until the first turn is complete

#### Scenario: Moving another player's unit

- **WHEN** `move` names a unit belonging to another player
- **THEN** the client refuses the order

#### Scenario: Moving a unit not in play

- **WHEN** `move` names a unit that is not on the board
- **THEN** the client refuses the order

#### Scenario: Invalid direction

- **WHEN** `move` is given a direction other than north, south, east, or west
- **THEN** the client reports the direction as invalid

### Requirement: Client Display Commands

The system SHALL let a player inspect the game within the limits of their
visibility.

#### Scenario: Showing the board

- **WHEN** the player runs `show board`
- **THEN** the board is rendered from that player's perspective

#### Scenario: Showing the board before one exists

- **WHEN** `show board` is run before a board exists
- **THEN** the client reports that the board must be created first

#### Scenario: Showing types

- **WHEN** the player runs `show types`
- **THEN** the player's own types are listed, together with any enemy types they have seen

#### Scenario: Showing units

- **WHEN** the player runs `show units`
- **THEN** the player's own units are listed, together with any enemy units they have seen

#### Scenario: Showing players

- **WHEN** the player runs `show players`
- **THEN** the registered player numbers are listed

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, or with an unrecognised one
- **THEN** the client reports the command as invalid

### Requirement: Committing A Turn

The system SHALL let a player finalise their turn via `commit`, after which the
client waits for the turn to be resolved.

#### Scenario: Committing

- **WHEN** the player runs `commit` and the save succeeds
- **THEN** the client confirms the commit
- **AND** the client waits for the server to resolve the turn before accepting further orders

#### Scenario: Commit refused

- **WHEN** `commit` is run and the game cannot be saved
- **THEN** the client reports the problem and returns to the prompt

#### Scenario: Reloading after resolution

- **WHEN** the server has resolved the turn
- **THEN** the client reloads the game and resumes accepting orders
