## MODIFIED Requirements

### Requirement: Two-Phase Turn Resolution

The system SHALL resolve a turn in two phases: a movement phase that decides
every unit's destination from the board as the turn began, applies all those
moves together, and gathers the cells more than one unit finishes in; followed
by a combat phase that resolves those cells. No unit's move SHALL be applied
before another's destination has been decided.

#### Scenario: Resolving a turn

- **WHEN** a turn is resolved
- **THEN** every unit on the board first has its destination decided against the board as the turn began
- **AND** all of those moves are then applied together
- **AND** only then is combat resolved in every contested cell

#### Scenario: No unit is left mid-move

- **WHEN** the combat phase begins
- **THEN** no unit remains in the `MOVING` state

#### Scenario: No unit sees another's move before its own is decided

- **WHEN** two units are ordered such that one's destination would differ according to whether the other had already moved
- **THEN** both destinations are decided from the board as the turn began
- **AND** the outcome is the same whichever unit is processed first

### Requirement: Deployment On First Resolution

The system SHALL place newly created units onto the board when the turn is
resolved. Deploying a brand new unit onto a cell that is already taken is
illegal: the system SHALL refuse the deployment and SHALL resolve the turn
without it, rather than failing the turn. When two deployments contend for one
cell in the same turn, the system SHALL refuse both, so that no player gains
from the order their orders happen to be read in.

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
- **THEN** both are refused
- **AND** the turn resolves with neither on that cell
- **AND** the cell is left empty

#### Scenario: Two players deploying onto one cell in the same turn

- **WHEN** two players each deploy a unit onto the same cell on the same turn, neither able to see the other's units
- **THEN** the server refuses both deployments
- **AND** publishes the rejection to each of them
- **AND** the turn is resolved for every other unit
- **AND** neither player is favoured by their player number or by the order their orders were read

#### Scenario: Deployment is not movement

- **WHEN** a unit already on the board is ordered to move into a cell another unit holds
- **THEN** the order is allowed
- **AND** the two units contest the cell

### Requirement: Commit Barrier

The system SHALL apply a turn only once every player still in the game has
committed, holding the turn open until then. A player who has been eliminated
SHALL NOT be waited for.

#### Scenario: Waiting for all players

- **WHEN** some but not all players still in the game have committed their orders
- **THEN** the server waits and does not resolve the turn

#### Scenario: All players committed

- **WHEN** every player still in the game has committed
- **THEN** the server resolves the turn and applies all orders together

#### Scenario: An eliminated player is not waited for

- **WHEN** every player still in the game has committed and an eliminated player has not
- **THEN** the server resolves the turn without waiting for them

#### Scenario: The last player standing

- **WHEN** every player but one has been eliminated
- **THEN** the game is decided rather than the turn being held open for the eliminated players
