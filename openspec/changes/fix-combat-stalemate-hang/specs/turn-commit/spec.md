## MODIFIED Requirements

### Requirement: Deployment On First Resolution

The system SHALL place newly created units onto the board when the turn is
resolved. Deployment SHALL NOT require the target cell to be empty; a unit
deployed onto an occupied cell contests it.

#### Scenario: Deploying a new unit

- **WHEN** a turn is resolved and a unit is in the `INITIAL` state
- **THEN** the unit is placed at its assigned coordinates
- **AND** the unit moves to the `NOP` state

#### Scenario: Deploying onto an occupied cell

- **WHEN** a unit in the `INITIAL` state is resolved and its assigned cell already holds one or more units
- **THEN** the unit joins that cell
- **AND** the contest is resolved in the combat phase of the same turn
- **AND** the turn continues normally for all other units

#### Scenario: Deploying two units of the same player onto one cell

- **WHEN** a player deploys two of their own units at the same coordinates
- **THEN** the turn resolves without raising
- **AND** the two units contest the cell under friendly fire
