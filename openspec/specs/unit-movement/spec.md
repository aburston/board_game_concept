# unit-movement Specification

## Purpose

Movement is how a player acts on a turn. A player orders a unit in one of four
directions; the order is held until the turn is resolved, at which point every
ordered move is applied at once. Movement costs energy and is bounded by the
edges of the board.

## Requirements

### Requirement: Movement Orders

The system SHALL accept a movement order for a unit in one of four cardinal
directions, and SHALL hold that order until the turn is resolved.

#### Scenario: Ordering a move

- **WHEN** a unit is ordered to move in a direction
- **THEN** the unit enters the `MOVING` state
- **AND** the ordered direction is recorded
- **AND** the unit does not change position until the turn is resolved

### Requirement: Movement Is One Cell Per Turn

The system SHALL move a unit at most one cell per resolved turn, in the ordered
direction.

#### Scenario: Moving north

- **WHEN** a unit at (x, y) with a `NORTH` order is resolved
- **THEN** its destination is (x, y-1)

#### Scenario: Moving south

- **WHEN** a unit at (x, y) with a `SOUTH` order is resolved
- **THEN** its destination is (x, y+1)

#### Scenario: Moving east

- **WHEN** a unit at (x, y) with an `EAST` order is resolved
- **THEN** its destination is (x+1, y)

#### Scenario: Moving west

- **WHEN** a unit at (x, y) with a `WEST` order is resolved
- **THEN** its destination is (x-1, y)

### Requirement: Board Edges Block Movement

The system SHALL prevent a unit from leaving the board, holding it at the edge
rather than failing the turn.

#### Scenario: Move would leave the board

- **WHEN** a unit on an edge is ordered to move off the board
- **THEN** the unit remains within bounds at the edge coordinate
- **AND** the unit's order resolves to no operation
- **AND** the turn continues normally for all other units

### Requirement: Movement Costs Energy

The system SHALL charge a unit energy to move, and SHALL refuse the move when
the unit cannot pay.

#### Scenario: Paying for a move

- **WHEN** a unit with energy E resolves a move
- **THEN** the cost charged is `E // 100 + 1`
- **AND** the unit's energy is reduced by that cost

#### Scenario: Insufficient energy

- **WHEN** a unit cannot pay the movement cost without its energy going negative
- **THEN** the unit does not move
- **AND** its energy is unchanged

### Requirement: Movement Into An Empty Cell

The system SHALL move a unit into an empty destination cell and vacate the cell
it came from.

#### Scenario: Unopposed move

- **WHEN** a unit moves into an empty cell and can pay the cost
- **THEN** the unit's previous cell becomes empty
- **AND** the unit occupies the destination cell

### Requirement: Movement Into A Contested Cell

The system SHALL allow multiple units to enter the same destination cell in the
same turn, collecting them for combat resolution rather than rejecting the move.

#### Scenario: Second unit enters a contested cell

- **WHEN** a unit moves into a cell already claimed by another moving unit this turn
- **THEN** the unit joins the set of units contesting that cell
- **AND** the unit's previous cell becomes empty

### Requirement: Movement Into An Occupied Cell Starts Combat

The system SHALL treat a move into a cell held by a standing unit as an attack,
and SHALL require the mover to have enough energy to attack.

#### Scenario: Attacking a standing unit

- **WHEN** a unit with energy at least equal to its attack moves into an occupied cell
- **THEN** both units are placed in contention for that cell
- **AND** the attacker's previous cell becomes empty

#### Scenario: Too little energy to attack

- **WHEN** a unit with energy below its attack value moves into an occupied cell
- **THEN** no engagement is started

### Requirement: Orders Are Consumed

The system SHALL clear a unit's direction once its move has been resolved, so
that an order is never applied twice.

#### Scenario: Order does not repeat

- **WHEN** a unit's move has been resolved
- **THEN** its direction is reset
- **AND** its state is `NOP` until a new order is given
