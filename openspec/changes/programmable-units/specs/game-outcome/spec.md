# Spec Delta

## ADDED Requirements

### Requirement: An Unchanging Game Stops

The system SHALL stop resolving a game, recording it as undecided, when the
whole state of the game at the end of a turn is identical to its state at the
end of an earlier turn - every unit's square, health, energy, memory, meter,
sleep and inbox, and every army's map - because controllers are deterministic
and such a game can never change again. The system SHALL also stop, recording
the game as undecided, when `TURN_CAP` turns have been resolved without a
decision; `TURN_CAP` SHALL be 500. An undecided game SHALL report the turn it
stopped on and why.

#### Scenario: Two armies that never move

- **WHEN** every controller in the game gives no order and nothing is in contact on turn 2
- **THEN** the state after turn 2 equals the state after turn 1
- **AND** the game stops after turn 2, undecided, saying its state repeated

#### Scenario: A cycle

- **WHEN** the state after turn 40 equals the state after turn 34
- **THEN** the game stops after turn 40, undecided

#### Scenario: The cap

- **WHEN** 500 turns have been resolved and the game is neither decided nor repeating
- **THEN** the game stops, undecided, saying the cap was reached

#### Scenario: A decided game is not undecided

- **WHEN** a turn decides the game
- **THEN** it is recorded as decided on that turn, whatever its state

## MODIFIED Requirements

### Requirement: Eliminated Players Do Not Hold The Turn Open

The system SHALL resolve the game without regard to an eliminated player: their
units are left standing and inert, their controllers do not run, and nothing
of theirs is waited for.

#### Scenario: An eliminated player's controllers

- **WHEN** a turn is resolved after a player has been eliminated
- **THEN** none of that player's controllers runs
- **AND** none of their units is given an order

#### Scenario: An eliminated player's session

- **WHEN** a player opens a session for a game in which they are eliminated
- **THEN** the session reports that they are out of the game and on which turn
- **AND** shows them the record

### Requirement: A Decided Game Accepts No Further Turns

Once the game is decided or stopped undecided the system SHALL resolve no
further turns, and every session SHALL report the result and offer the record.

#### Scenario: Resolution stops

- **WHEN** a turn decides the game, or the game stops undecided
- **THEN** the result is recorded
- **AND** no further turn is resolved

#### Scenario: A client opens a finished game

- **WHEN** a player opens a session for a game that has been resolved to its end
- **THEN** the client reports the result
- **AND** offers the replay

#### Scenario: An observer opens a finished game

- **WHEN** the observer opens a game that has been resolved to its end
- **THEN** it reports the result alongside the final board
- **AND** offers the replay
