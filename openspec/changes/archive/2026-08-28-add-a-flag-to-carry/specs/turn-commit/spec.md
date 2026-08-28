## MODIFIED Requirements

### Requirement: Only Units In Play Are Resolved

The system SHALL resolve movement and combat only for units currently on the
board, skipping units that have been destroyed or not yet deployed.

A unit belonging to an eliminated player SHALL be resolved as terrain: it
holds its square, takes no order and lands no attack, and is attacked and
destroyed like any other unit.

#### Scenario: Skipping units not in play

- **WHEN** a turn is resolved
- **THEN** units not on the board take no action

#### Scenario: An eliminated player's units hold their squares

- **WHEN** a turn is resolved and an eliminated player has units standing
- **THEN** those units stay where they are
- **AND** they land no attack in any contest they are part of

#### Scenario: Clearing them

- **WHEN** another player's unit attacks one of them
- **THEN** it takes damage and is destroyed if it runs out of health

### Requirement: Game Setup Precedes Play

The system SHALL treat the first commit as the end of setup, after which unit
types, unit placements and the flag are fixed and only movement orders are
accepted.

A player's setup commit SHALL be refused unless exactly one of their units
carries their flag, as `flag-carrier` requires.

#### Scenario: Adding types during setup

- **WHEN** the game has not yet had its first turn resolved
- **THEN** players may define unit types and place units
- **AND** players may not order movement

#### Scenario: Setup closed after the first turn

- **WHEN** the first turn has been resolved
- **THEN** players may order movement
- **AND** players may no longer define types or place units

#### Scenario: Setup closed by committing it

- **WHEN** a player has committed a setup and the first turn has not resolved
- **THEN** they may no longer define types or place units
- **AND** the refusal says their setup is committed rather than naming a turn
  that has not happened

#### Scenario: A setup with no flag

- **WHEN** a player commits a setup in which no unit of theirs carries the flag
- **THEN** the commit is refused
- **AND** setup remains open for that player
