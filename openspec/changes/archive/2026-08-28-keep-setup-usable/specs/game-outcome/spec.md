## RENAMED Requirements

- FROM: `### Requirement: The Game Begins When The First Unit Reaches The Board`
- TO: `### Requirement: The Game Begins When The Players' Setups Are Resolved`

## MODIFIED Requirements

### Requirement: The Game Begins When The Players' Setups Are Resolved

The system SHALL judge elimination and victory from the first resolution that
carries out the players' committed setups, and SHALL NOT judge them before
one. The administrator's commit that ends setup is resolved like a turn, and
at that point no player has committed a setup of their own; it SHALL NOT be
numbered as a turn, and no player SHALL be eliminated by it.

What survived that resolution SHALL NOT decide whether the game has begun. A
first turn in which every deployment is refused — two players deploying onto
one square, or a budget that will not pay — leaves its players with nothing
standing, and they SHALL be eliminated by it like any other player holding
nothing that can act. Otherwise the game is left where it cannot be played:
setup is over, so nothing more can be deployed, and no unit ever reached the
board, so nothing is ever decided.

#### Scenario: The commit that ends setup

- **WHEN** the administrator commits to end setup and the turn is resolved before any player has committed one
- **THEN** the game records no turn as resolved
- **AND** no player is eliminated
- **AND** the game is not decided

#### Scenario: The first turn with units on the board

- **WHEN** a turn is resolved in which units are on the board
- **THEN** it is recorded as turn 1
- **AND** elimination is judged from it

#### Scenario: A first turn that leaves nothing standing

- **WHEN** the first turn is resolved and every deployment in it is refused
- **THEN** it is recorded as turn 1
- **AND** every player left with nothing standing is eliminated
- **AND** the game is decided rather than left to be played on an empty board

### Requirement: Turns Are Numbered

The system SHALL number resolved turns from 1, SHALL increase the number by one
for each turn it resolves, and SHALL persist it with the game, so that anything
published for a turn can be attributed to the turn it describes.

#### Scenario: The first resolved turn

- **WHEN** the first turn resolved from the players' committed setups is resolved
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
