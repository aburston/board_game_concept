## MODIFIED Requirements

### Requirement: Deployment On First Resolution

The system SHALL place newly created units onto the board when the turn is
resolved. Deploying a brand new unit onto a cell that is already taken is
illegal: the system SHALL refuse the deployment and SHALL resolve the turn
without it, rather than failing the turn.

#### Scenario: Deploying a new unit

- **WHEN** a turn is resolved and a unit is in the `INITIAL` state
- **THEN** the unit is placed at its assigned coordinates
- **AND** the unit moves to the `NOP` state

#### Scenario: Deploying onto an occupied cell

- **WHEN** a unit is deployed at coordinates that already hold a unit
- **THEN** the deployment is refused with an error naming the unit and the cell
- **AND** no unit is created
- **AND** the unit already holding the cell is unaffected

#### Scenario: Deploying two units onto one cell in the same turn

- **WHEN** two units are deployed at the same coordinates before the turn is resolved
- **THEN** the first is accepted and the second is refused
- **AND** the turn resolves with only the first on that cell

#### Scenario: Two players deploying onto one cell in the same turn

- **WHEN** two players each deploy a unit onto the same cell on the same turn, neither able to see the other's units
- **THEN** the server refuses one of the two deployments
- **AND** publishes the rejection to the player whose order was refused
- **AND** the turn is resolved for every other unit

#### Scenario: Deployment is not movement

- **WHEN** a unit already on the board is ordered to move into a cell another unit holds
- **THEN** the order is allowed
- **AND** the two units contest the cell
