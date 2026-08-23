## MODIFIED Requirements

### Requirement: Movement Costs Energy

The system SHALL charge a unit energy to move, and SHALL refuse the move when
the unit cannot pay. This SHALL apply to every resolved move, including a move
onto a square held by a standing unit.

#### Scenario: Paying for a move

- **WHEN** a unit with energy E resolves a move
- **THEN** the cost charged is `E // 100 + 1`
- **AND** the unit's energy is reduced by that cost

#### Scenario: Insufficient energy

- **WHEN** a unit cannot pay the movement cost without its energy going negative
- **THEN** the unit does not move
- **AND** its energy is unchanged

#### Scenario: Paying to engage

- **WHEN** a unit moves onto a square held by a standing unit
- **THEN** it is charged the movement cost, as it would be for any other move
- **AND** two units that have made the same number of moves have paid the same
  for them, whatever they met on the way

### Requirement: Movement Into An Occupied Cell Starts Combat

The system SHALL treat a move into a cell held by a standing unit as an attack,
and SHALL require the mover to have enough energy to attack and to pay for the
move.

#### Scenario: Attacking a standing unit

- **WHEN** a unit with energy at least equal to its attack moves into an occupied cell
- **THEN** both units are placed in contention for that cell
- **AND** the attacker's previous cell becomes empty

#### Scenario: Too little energy to attack

- **WHEN** a unit with energy below its attack value moves into an occupied cell
- **THEN** no engagement is started

#### Scenario: Too little energy to arrive

- **WHEN** a unit cannot pay the movement cost onto an occupied cell
- **THEN** no engagement is started
- **AND** the unit does not move
