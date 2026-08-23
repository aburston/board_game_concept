## Purpose

Decides when a game is over, who won it, and how a decided game stops being
played, so that a finished game can be left rather than looping forever. Also
owns the turn number every other record is attributed to.

## ADDED Requirements

### Requirement: The Game Begins When The First Unit Reaches The Board

The system SHALL judge elimination and victory only once a unit has reached the
board. The administrator's commit that ends setup is resolved like a turn, and
at that point nobody has deployed anything; it SHALL NOT be numbered as a turn,
and no player SHALL be eliminated by it.

#### Scenario: The commit that ends setup

- **WHEN** the administrator commits to end setup and the turn is resolved with no unit on the board
- **THEN** the game records no turn as resolved
- **AND** no player is eliminated
- **AND** the game is not decided

#### Scenario: The first turn with units on the board

- **WHEN** a turn is resolved in which units are on the board
- **THEN** it is recorded as turn 1
- **AND** elimination is judged from it

### Requirement: Player Elimination

The system SHALL treat a player as eliminated once every unit they own has been
destroyed. A unit that is on the board and not destroyed SHALL keep its owner in
the game whatever its energy: a unit too spent to act is inert, not lost.

#### Scenario: The last unit is destroyed

- **WHEN** a turn is resolved in which a player's last undestroyed unit is destroyed
- **THEN** that player is eliminated

#### Scenario: An inert unit keeps its owner in the game

- **WHEN** a player's only remaining unit has energy below its attack value
- **THEN** that player is not eliminated
- **AND** the game continues

#### Scenario: A player who never deployed a unit

- **WHEN** the first turn with units on the board is resolved and a registered player holds none of them
- **THEN** that player is eliminated

#### Scenario: Elimination is not reversible

- **WHEN** a later turn is resolved after a player has been eliminated
- **THEN** that player remains eliminated
- **AND** no unit is created for them

### Requirement: Victory

The system SHALL decide the game in favour of the last player who is not
eliminated, at the end of the turn in which every other player becomes
eliminated. A game registered with fewer than two players SHALL never be
decided: there is nobody to be the last player standing against, and a solo
game is a sandbox rather than a contest.

#### Scenario: One player left

- **WHEN** a turn is resolved that leaves exactly one player not eliminated
- **THEN** the game is decided
- **AND** that player is recorded as the winner
- **AND** the turn on which it was decided is recorded

#### Scenario: More than one player left

- **WHEN** a turn is resolved and two or more players still hold an undestroyed unit
- **THEN** the game is not decided
- **AND** play continues

#### Scenario: A game with a single registered player

- **WHEN** turns are resolved in a game registered with one player
- **THEN** the game is never decided
- **AND** that player is never eliminated

### Requirement: Draw

The system SHALL record a draw when the last players still in the game are all
eliminated on the same turn, so that a mutual wipe-out ends the game rather than
leaving it unwinnable.

#### Scenario: The last two units destroy each other

- **WHEN** a turn is resolved in which the last unit of each remaining player is destroyed
- **THEN** the game is decided
- **AND** no winner is recorded
- **AND** the result is recorded as a draw

#### Scenario: Every player is eliminated

- **WHEN** a turn is resolved that leaves no player holding an undestroyed unit
- **THEN** the game is decided as a draw

### Requirement: Eliminated Players Do Not Hold The Turn Open

The system SHALL stop waiting on an eliminated player's commit, so that a
player who has been wiped out or has left cannot freeze the game for everyone
else.

#### Scenario: The barrier ignores an eliminated player

- **WHEN** every player who is not eliminated has committed
- **THEN** the turn is resolved without waiting for any eliminated player

#### Scenario: An eliminated player's session

- **WHEN** a player opens a session for a game in which they are eliminated
- **THEN** the session reports that they are out of the game
- **AND** takes no orders from them

### Requirement: A Decided Game Accepts No Further Turns

Once the game is decided the system SHALL resolve no further turns and accept no
further orders, and every session SHALL report the result rather than prompting
for play.

#### Scenario: The server stops

- **WHEN** the server resolves a turn that decides the game
- **THEN** it publishes the result
- **AND** it stops waiting for commits and ends its turn cycle reporting the result

#### Scenario: A client opens a decided game

- **WHEN** a player opens a session for a decided game
- **THEN** the client reports the result
- **AND** refuses movement orders and commits

#### Scenario: An observer opens a decided game

- **WHEN** the observer opens a decided game
- **THEN** it reports the result alongside the final board

### Requirement: The Outcome Is Published

The system SHALL record the result of a decided game where every session can
read it, naming the winner or recording the draw, and the turn on which it was
decided.

#### Scenario: Publishing a win

- **WHEN** the game is decided in favour of one player
- **THEN** the result is persisted naming that player and the deciding turn

#### Scenario: Publishing a draw

- **WHEN** the game is decided as a draw
- **THEN** the result is persisted recording a draw and the deciding turn

#### Scenario: An undecided game has no result

- **WHEN** a game that is still being played is read
- **THEN** no result is reported

#### Scenario: Reading the result back

- **WHEN** any session is opened on a decided game
- **THEN** it reports the same winner or draw and the same deciding turn

### Requirement: Turns Are Numbered

The system SHALL number resolved turns from 1, SHALL increase the number by one
for each turn it resolves, and SHALL persist it with the game, so that anything
published for a turn can be attributed to the turn it describes.

#### Scenario: The first resolved turn

- **WHEN** the first turn with units on the board is resolved
- **THEN** the game records turn number 1

#### Scenario: Numbering advances

- **WHEN** a further turn is resolved
- **THEN** the recorded turn number is one greater than the previous turn's

#### Scenario: Published records name their turn

- **WHEN** the server publishes the board, a per-player view, or a player's refused orders
- **THEN** each names the turn number it describes

#### Scenario: The number survives a reload

- **WHEN** a game is loaded
- **THEN** it reports the number of the last turn resolved
