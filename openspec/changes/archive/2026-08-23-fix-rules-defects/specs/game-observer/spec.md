## ADDED Requirements

### Requirement: Observing A Decided Game

The system SHALL let the observer see how far a game has got and how it ended,
reporting the turn number it is showing and, once the game is decided, the
winner or the draw.

#### Scenario: Opening a decided game

- **WHEN** the observer opens a game whose outcome has been written
- **THEN** it reports the winner, or the draw, and the deciding turn number
- **AND** it can still display the final board and units

#### Scenario: Opening a game still being played

- **WHEN** the observer opens a game that is not yet decided
- **THEN** it reports no outcome
- **AND** reports the number of the last turn resolved

#### Scenario: Reloading onto a decided game

- **WHEN** `reload` is entered and the game has been decided since the session started
- **THEN** the observer reports the outcome after reloading

#### Scenario: The observer never orders

- **WHEN** a game is decided
- **THEN** the observer's read-only command surface is unchanged
