## MODIFIED Requirements

### Requirement: Player And Type Persistence

The system SHALL persist each player's number, point budget and unit type
definitions in a per-player record, and SHALL restore all three when the game
is loaded.

A stored player record SHALL carry the budget that player was registered with.
A record read without one is malformed game data and SHALL be treated as
`Malformed Data Is Fatal` requires: the game is not opened, and the error names
the player whose record has no budget. A budget is a rule the game was set up
under, and defaulting a missing one would carry on playing a game by rules it
was not set up with.

This applies to a record a game has written. A player file offered to
`load player` is configuration rather than stored state, and `game-server`
states what a missing budget means there.

#### Scenario: Saving a player

- **WHEN** a player's data is saved
- **THEN** their number, budget and unit types are written to their record

#### Scenario: Loading players

- **WHEN** a game is loaded
- **THEN** every player record is read, its budget restored, and its types
  reconstructed as unit types

#### Scenario: A stored record with no budget

- **WHEN** a game is opened holding a player record that carries no budget
- **THEN** the error is reported, naming that player
- **AND** the game is not opened

#### Scenario: A budget survives a round trip

- **WHEN** a player registered with a budget of 150 is saved and the game is
  opened again
- **THEN** that player's budget is 150
