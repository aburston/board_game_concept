# turn-commit Specification

## Purpose

The game advances in simultaneous turns. Players issue orders independently and
commit them; the server waits until every player has committed, then resolves
all orders at once. No player's orders are applied before another's, so no
player gains an advantage from committing early or late.

## Requirements

### Requirement: Two-Phase Turn Resolution

The system SHALL resolve a turn in two phases: a movement phase that computes
destinations and gathers contested cells, followed by a combat phase that
resolves those cells.

#### Scenario: Resolving a turn

- **WHEN** a turn is resolved
- **THEN** every unit on the board first resolves its movement order
- **AND** only then is combat resolved in every contested cell

#### Scenario: No unit is left mid-move

- **WHEN** the combat phase begins
- **THEN** no unit remains in the `MOVING` state

### Requirement: Deployment On First Resolution

The system SHALL place newly created units onto the board when the turn is
resolved, and SHALL reject a placement whose cell is no longer empty.

#### Scenario: Deploying a new unit

- **WHEN** a turn is resolved and a unit is in the `INITIAL` state
- **THEN** the unit is placed at its assigned coordinates
- **AND** the unit moves to the `NOP` state

#### Scenario: Deploying onto an occupied cell

- **WHEN** a unit in the `INITIAL` state is resolved and its assigned cell is not empty
- **THEN** the placement fails

### Requirement: Only Units In Play Are Resolved

The system SHALL resolve movement and combat only for units currently on the
board, skipping units that have been destroyed or not yet deployed.

#### Scenario: Skipping units not in play

- **WHEN** a turn is resolved
- **THEN** units not on the board take no action

### Requirement: Commit Barrier

The system SHALL apply a turn only once every registered player has committed,
holding the turn open until then.

#### Scenario: Waiting for all players

- **WHEN** some but not all players have committed their orders
- **THEN** the server waits and does not resolve the turn

#### Scenario: All players committed

- **WHEN** every registered player has committed
- **THEN** the server resolves the turn and applies all orders together

### Requirement: Players Wait For Turn Completion

The system SHALL prevent a player from issuing new orders while their previous
commit is still awaiting resolution.

#### Scenario: Player blocked after committing

- **WHEN** a player has committed and the turn has not yet been resolved
- **THEN** the client reports that it is waiting for the turn to complete
- **AND** the client reloads game data and retries rather than accepting new orders

### Requirement: Commits Are Final

The system SHALL treat a commit as irreversible; a player cannot withdraw or
amend orders once committed.

#### Scenario: Committing orders

- **WHEN** a player commits
- **THEN** their orders are written for the server to consume
- **AND** the player cannot undo them

### Requirement: Orders Are Consumed Once

The system SHALL discard players' pending order files after the turn has been
resolved, so no order is applied in a later turn.

#### Scenario: Clearing pending orders

- **WHEN** the server has resolved a turn
- **THEN** every player's pending order file is removed

### Requirement: Game Setup Precedes Play

The system SHALL treat the first commit as the end of setup, after which unit
types and unit placements are fixed and only movement orders are accepted.

#### Scenario: Adding types during setup

- **WHEN** the game has not yet had its first turn resolved
- **THEN** players may define unit types and place units
- **AND** players may not order movement

#### Scenario: Setup closed after the first turn

- **WHEN** the first turn has been resolved
- **THEN** players may order movement
- **AND** players may no longer define types or place units
