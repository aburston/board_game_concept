# Spec Delta

## ADDED Requirements

### Requirement: The Observer Replays The Game

The system SHALL let the observer read any turn of a resolved game via
`show turn <n>`, `next` and `prev`, drawing the whole board as it stood after
that turn and listing what the turn did and every unit's controller trace,
since the observer sees everything. `show program <type>` SHALL show the
observer any seat's program. On a game not yet resolved these SHALL be
refused, saying so.

#### Scenario: Reading a turn

- **WHEN** the observer runs `show turn 9` on a resolved game
- **THEN** the board after turn 9 is drawn with every unit
- **AND** the turn's events and every controller's trace are listed

#### Scenario: Stepping

- **WHEN** the observer runs `next` and then `prev`
- **THEN** the turn after is shown, then the one before

#### Scenario: Reading a program

- **WHEN** the observer runs `show program` naming any seat's type
- **THEN** the program is listed with its tick costs

## MODIFIED Requirements

### Requirement: Observing A Decided Game

The system SHALL let the observer see how far a game has got and how it ended,
reporting the turn number it is showing and, once the game is resolved, the
winner, the draw, or that it stopped undecided and why.

#### Scenario: Opening a decided game

- **WHEN** the observer opens a game whose outcome has been written
- **THEN** it reports the winner, the draw, or the undecided stop, and the turn number
- **AND** it shows the final board and offers the replay

#### Scenario: Opening a game still being played

- **WHEN** the observer opens a game whose players have not all committed their setups
- **THEN** it reports no outcome
- **AND** reports that the game is being set up

#### Scenario: Reloading onto a decided game

- **WHEN** `reload` is entered and the game has been resolved since the session started
- **THEN** the observer reports the outcome after reloading

#### Scenario: The observer never orders

- **WHEN** a game is resolved
- **THEN** the observer's read-only command surface is unchanged
