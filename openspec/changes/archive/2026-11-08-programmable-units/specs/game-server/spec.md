# Spec Delta

## ADDED Requirements

### Requirement: The Administrator Reads The Record

The system SHALL let the administrator read the record of a resolved game
via `show turn <n>`, `next` and `prev`, as `player-client` states for a
player, showing the whole board and every seat's traces, since the
administrator is entitled to the whole game.

#### Scenario: The administrator reads a turn

- **WHEN** the administrator starts `bgcserver` with `--replay` against a resolved game and runs `show turn 5`
- **THEN** the board after turn 5 is drawn with every unit
- **AND** every seat's controller traces for turn 5 are listed

#### Scenario: Reading the record is asked for

- **WHEN** the administrator starts `bgcserver` against a resolved game without `--replay`
- **THEN** it reports the outcome and exits, as the unattended cycle does

## MODIFIED Requirements

### Requirement: Unattended Turn Cycle

The system SHALL, once the administrator has committed setup, wait for every
registered player's setup commit, and SHALL then resolve the whole game in one
held act - every turn, one after another, until the game is decided, its
state repeats, or the turn cap - writing each turn's record as it goes,
reporting the result, and exiting with a success status. Where the last setup
commit arrives over HTTP and resolves the game during that request, the server
SHALL find the game resolved when it is woken and SHALL report the result and
exit without resolving anything.

#### Scenario: The turn loop

- **WHEN** the server is running unattended and the last player commits their setup
- **THEN** it resolves every turn to the game's end, one after another, waiting for nobody
- **AND** writes each turn's record

#### Scenario: A turn decides the game

- **WHEN** a turn leaves at most one player not eliminated, or the game's state repeats, or the cap is reached
- **THEN** the server writes the outcome with the game
- **AND** reports the winner, the draw, or the undecided stop and why, with the turn number
- **AND** exits with a success status

#### Scenario: Starting against a game already decided

- **WHEN** the server is started against a game whose outcome has already been written
- **THEN** it reports the outcome and exits without resolving a turn

#### Scenario: Save failure during the cycle

- **WHEN** the server cannot save game state while resolving
- **THEN** it reports an internal error and exits with a failure status

#### Scenario: Woken for a turn another caller has already resolved

- **WHEN** the server is woken and finds the game resolved
- **THEN** it does not resolve anything
- **AND** it reports the result and exits

#### Scenario: Ending setup is not held to the barrier

- **WHEN** the administrator commits to end setup
- **THEN** the board and the seats are fixed without waiting for any player
- **AND** the game is not resolved until every player's setup is committed
