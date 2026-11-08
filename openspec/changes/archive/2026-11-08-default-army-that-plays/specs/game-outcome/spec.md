## ADDED Requirements

### Requirement: A Quiet Game Stops

The system SHALL stop resolving a game, recording it as undecided, when
nothing has happened for `QUIET_CAP` consecutive turns, which SHALL be 50:
no unit has changed square, no blow has been landed, no unit has been
destroyed and no flag has fallen. Thinking, sleeping and resting are not
things happening: a sleeping unit's countdown and a controller's meter keep
a static board from ever repeating its whole state, and a board on which
nothing has moved or struck for fifty turns is one nobody is watching.

A quiet stop SHALL say that it is one and SHALL name the last turn on which
anything happened. The repeated-state stop and the turn cap SHALL stand as
they are, and whichever of the three comes first SHALL end the game.

#### Scenario: Two Keeps alone

- **WHEN** the last blow of a game is landed on turn 24 and the two units left stand sleeping at opposite edges
- **THEN** the game stops after turn 74, undecided, saying nothing has happened since turn 24

#### Scenario: A sleeper that wakes resets the count

- **WHEN** nothing happens from turn 10 to turn 40 and a unit moves on turn 41
- **THEN** the game goes on, and the fifty turns are counted again from turn 41

#### Scenario: A blow that destroys nothing counts

- **WHEN** a unit strikes another every tenth turn and neither moves
- **THEN** the game does not stop for quiet

#### Scenario: Whichever stop comes first

- **WHEN** a game's whole state repeats on turn 30 and nothing has happened since turn 5
- **THEN** the game stops after turn 30, saying its state repeated

#### Scenario: The outcome says why

- **WHEN** a game stops for quiet
- **THEN** every role reports it undecided, that nothing happened for fifty turns, and the turn anything last did
