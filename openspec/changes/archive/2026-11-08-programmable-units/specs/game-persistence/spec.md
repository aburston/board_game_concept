# Spec Delta

## ADDED Requirements

### Requirement: The Record Of Every Turn Is Persisted

The system SHALL persist, for every turn resolved, the board and every unit
as the turn left them, the flags, the turn's events and each seat's share of
them, each player's map as it stood after the turn, and every controller's
trace, against the turn's number, and SHALL keep every turn's record for the
life of the game. A session SHALL be able to read any turn's record by its
number, and the record SHALL be the same whichever backend holds it.

#### Scenario: A turn's record is written

- **WHEN** a turn is resolved
- **THEN** its board, units, flags, events, maps and traces are written against its number

#### Scenario: Any turn can be read back

- **WHEN** a session asks for turn 7 of a game resolved to turn 40
- **THEN** the board, units, flags, events and the traces that session is entitled to are read as they were after turn 7

#### Scenario: The record survives both backends alike

- **WHEN** the same game is resolved under each backend
- **THEN** each turn's record reads the same from either

### Requirement: A Game Set Up Before Controllers Cannot Be Opened

The system SHALL refuse to open a game whose stored types carry no compute or
whose turns were resolved from orders given by hand, as it refuses a game
whose players have no budget: such a game was played by rules the game no
longer has. The refusal SHALL name the game and say why.

#### Scenario: Opening an old game

- **WHEN** a game is opened whose stored types have no compute
- **THEN** the error is reported, naming the game
- **AND** the game is not opened

## MODIFIED Requirements

### Requirement: Player And Type Persistence

The system SHALL persist each player's number, point budget and unit type
definitions - each type's name, symbol, four statistics and program - in a
per-player record, and SHALL restore all of them when the game is loaded.

A stored player record SHALL carry the budget that player was registered with.
A record read without one is malformed game data and SHALL be treated as
`Malformed Data Is Fatal` requires: the game is not opened, and the error names
the player whose record has no budget. A budget is a rule the game was set up
under, and defaulting a missing one would carry on playing a game by rules it
was not set up with. A stored type without compute SHALL be treated the same
way.

This applies to a record a game has written. A player file offered to
`load player` is configuration rather than stored state, and `game-server`
states what a missing budget means there.

#### Scenario: Saving a player

- **WHEN** a player's data is saved
- **THEN** their number, budget and unit types, with each type's compute and program, are written to their record

#### Scenario: Loading players

- **WHEN** a game is loaded
- **THEN** every player record is read, its budget restored, and its types
  reconstructed as unit types carrying their programs

#### Scenario: A stored record with no budget

- **WHEN** a game is opened holding a player record that carries no budget
- **THEN** the error is reported, naming that player
- **AND** the game is not opened

#### Scenario: A program survives a round trip

- **WHEN** a type with a program is saved and the game is opened again
- **THEN** the type carries the same program, line for line

#### Scenario: A budget survives a round trip

- **WHEN** a player registered with a budget of 150 is saved and the game is
  opened again
- **THEN** that player's budget is 150
