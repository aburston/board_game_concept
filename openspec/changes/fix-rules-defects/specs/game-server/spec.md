## MODIFIED Requirements

### Requirement: Unattended Turn Cycle

The system SHALL run continuously once setup is complete, resolving each turn as
soon as every player still in the game has committed, and SHALL stop once the
game is decided rather than waiting for commits that will never come.

#### Scenario: The turn loop

- **WHEN** the server is running unattended
- **THEN** it waits for every player still in the game to commit
- **AND** resolves the turn
- **AND** writes the resulting board, units, turn number, and per-player views to disk
- **AND** logs the board and units before waiting again

#### Scenario: A turn decides the game

- **WHEN** the server resolves a turn that leaves at most one player not eliminated
- **THEN** it writes the outcome with the game
- **AND** reports the winner, or the draw, and the deciding turn number
- **AND** ends its turn cycle without waiting for further commits
- **AND** exits with a success status

#### Scenario: Starting against a game already decided

- **WHEN** the server is started against a game whose outcome has already been written
- **THEN** it reports the outcome and exits without resolving a turn

#### Scenario: Save failure during the cycle

- **WHEN** the server cannot save game state while resolving a turn
- **THEN** it reports an internal error and exits with a failure status
