## MODIFIED Requirements

### Requirement: Registering Players

The system SHALL let the administrator register players before the game starts
via `add player <number>`. The number SHALL be one `player-numbering` permits a
player, and one that is not SHALL be refused at the prompt — reported, with the
session continuing — rather than ending the session.

#### Scenario: Adding a player

- **WHEN** `add player` is given a player number and the game is new
- **THEN** that player is registered with no unit types

#### Scenario: Adding a player with a reserved number

- **WHEN** `add player` is given 0 or 1000
- **THEN** the server refuses, reporting that the number is reserved
- **AND** no player is registered
- **AND** the server takes further commands

#### Scenario: Adding a player with a number out of range

- **WHEN** `add player` is given a number below 1 or above 999
- **THEN** the server refuses, naming the permitted range
- **AND** no player is registered
- **AND** the server takes further commands

#### Scenario: Adding a player to an established game

- **WHEN** `add player` is run after the game has started
- **THEN** the server refuses, reporting that players cannot be added to an existing game

#### Scenario: Wrong argument count

- **WHEN** `add player` is given other than one argument
- **THEN** the server reports that one argument is required

### Requirement: Loading Configuration From Files

The system SHALL let the administrator import board and player configuration
from files via `load board <file>` and `load player <file>`. A player file
naming a number `player-numbering` does not permit a player SHALL be refused at
the prompt, with the session continuing.

#### Scenario: Loading a board

- **WHEN** `load board` names a file containing board dimensions
- **THEN** a board of those dimensions is created

#### Scenario: Loading a player

- **WHEN** `load player` names a file containing a player number, types, and units
- **THEN** that player is registered with those types and units

#### Scenario: Loading a player whose number is not a player's

- **WHEN** `load player` names a file whose player number is outside 1 to 999
- **THEN** the server refuses, naming the permitted range
- **AND** no player is registered
- **AND** the server returns to the prompt

#### Scenario: Loading a player into an established game

- **WHEN** `load player` is run after the game has started
- **THEN** the server refuses, reporting that players cannot be added to an existing game

#### Scenario: Unreadable file

- **WHEN** `load board` or `load player` names a file that cannot be read or parsed
- **THEN** the server reports the error and returns to the prompt

#### Scenario: Wrong argument count

- **WHEN** `load board` or `load player` is given other than one argument
- **THEN** the server reports that one argument is required
