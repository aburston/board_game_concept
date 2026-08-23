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
rather than failing the turn, and SHALL report the refused order to its owner.

#### Scenario: Move would leave the board

- **WHEN** a unit on an edge is ordered to move off the board
- **THEN** the unit remains within bounds at the edge coordinate
- **AND** the unit's order resolves to no operation
- **AND** its energy is unchanged
- **AND** the order is reported to its owner as refused
- **AND** the turn continues normally for all other units

### Requirement: Movement Costs Energy

The system SHALL charge a unit one energy to move, and SHALL refuse the move
when the unit cannot pay. This SHALL apply to every resolved move, whatever the
unit finds at its destination, so that two units that have made the same number
of moves have paid the same for them.

#### Scenario: Paying for a move

- **WHEN** a unit resolves a move
- **THEN** the cost charged is 1
- **AND** the unit's energy is reduced by 1

#### Scenario: Insufficient energy

- **WHEN** a unit has no energy left to pay the movement cost
- **THEN** the unit does not move
- **AND** its energy is unchanged
- **AND** the order is reported to its owner as refused

#### Scenario: Paying to engage

- **WHEN** a unit moves onto a cell held by a standing unit
- **THEN** it is charged 1, as it would be for any other move
- **AND** two units that have made the same number of moves have paid the same
  for them, whatever they met on the way

#### Scenario: A unit with a single energy can still move

- **WHEN** a unit with 1 energy resolves a move
- **THEN** it moves
- **AND** its energy becomes 0

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

- **WHEN** two units are ordered into the same cell in one turn and both can pay
- **THEN** both are in that cell once the moves have been applied
- **AND** both of their previous cells become empty
- **AND** the cell is contested

### Requirement: Movement Into An Occupied Cell Starts Combat

The system SHALL treat a move into a cell another unit finishes the turn in as
an attack. The mover SHALL need only the energy to pay for the move; a mover
that cannot afford to attack still arrives, and is inert in the contest it has
walked into.

#### Scenario: Attacking a standing unit

- **WHEN** a unit that can pay the movement cost moves into a cell another unit holds
- **THEN** both units are in that cell once the moves have been applied
- **AND** the cell is contested
- **AND** the attacker's previous cell becomes empty

#### Scenario: Too little energy to attack

- **WHEN** a unit with energy below its attack value moves into an occupied cell
- **THEN** it still moves
- **AND** the cell is contested
- **AND** it deals no damage in that contest, being unable to pay for an attack

#### Scenario: Too little energy to arrive

- **WHEN** a unit cannot pay the movement cost
- **THEN** the unit does not move
- **AND** no contest is started on its account
- **AND** the order is reported to its owner as refused

### Requirement: Orders Are Consumed

The system SHALL clear a unit's direction once its move has been resolved, so
that an order is never applied twice.

#### Scenario: Order does not repeat

- **WHEN** a unit's move has been resolved
- **THEN** its direction is reset
- **AND** its state is `NOP` until a new order is given

### Requirement: Movement Resolves Simultaneously

The system SHALL decide every moving unit's destination from the board as it
stood before any of this turn's moves were applied, and SHALL then apply all
those moves together. The outcome of a turn SHALL NOT depend on the order in
which units are held, registered or read.

#### Scenario: The order units are held in does not change the outcome

- **WHEN** the same orders are resolved on the same board with the units registered in a different order
- **THEN** every unit finishes the turn in the same cell with the same health and energy
- **AND** the same cells are contested

#### Scenario: Following a unit that moves away

- **WHEN** a unit is ordered into a cell whose occupant is ordered out of it in the same turn, and both moves are carried out
- **THEN** the mover occupies that cell alone
- **AND** no contest is started

#### Scenario: A chain of units advancing together

- **WHEN** three units stand in a line and each is ordered one cell in the same direction, the leading unit into an empty cell
- **THEN** all three move
- **AND** no cell is contested

#### Scenario: Moving into a cell whose occupant stays

- **WHEN** a unit is ordered into a cell whose occupant is given no order, or whose order is not carried out
- **THEN** both units are in that cell once the moves have been applied
- **AND** the cell is contested

### Requirement: Contention Is Decided By Where Units Finish

The system SHALL treat as contested every cell holding more than one unit once
all of this turn's moves have been applied, however the units came to share it.

#### Scenario: Two movers and a stander

- **WHEN** two units move into a cell a third unit is holding
- **THEN** all three contest that cell

#### Scenario: A cell nobody shares

- **WHEN** every unit finishes the turn in a cell of its own
- **THEN** no cell is contested
- **AND** no combat is resolved

### Requirement: Two Units Trading Cells Collide

The system SHALL treat two units ordered into each other's cells as a head-on
collision rather than letting them pass through each other. Neither unit
completes its move before the collision is resolved; both are charged the
movement cost; and they fight on the same terms as any other contest.

#### Scenario: A head-on collision is fought

- **WHEN** two adjacent units are each ordered into the cell the other holds, and both can pay the movement cost
- **THEN** both are charged the movement cost
- **AND** they exchange attacks as contestants do
- **AND** each records the other as seen

#### Scenario: One unit survives the collision

- **WHEN** a head-on collision destroys exactly one of the two units
- **THEN** the survivor completes its move into the cell the destroyed unit held
- **AND** the cell the survivor came from is left empty

#### Scenario: Neither unit survives the collision

- **WHEN** a head-on collision destroys both units
- **THEN** both cells are left empty

#### Scenario: A collision neither unit can decide

- **WHEN** a head-on collision ends with both units undestroyed
- **THEN** each unit stays in the cell it started the turn in
- **AND** neither is destroyed

#### Scenario: Units cannot pass through each other

- **WHEN** two units are ordered into each other's cells
- **THEN** neither finishes the turn in the cell the other started it in unless the other was destroyed

### Requirement: A Move That Is Not Carried Out Is Reported

The system SHALL report to the ordering player every movement order that does
not do what it said, naming the unit, its cell, and the reason, rather than
dropping it in silence.

#### Scenario: A move nobody can pay for

- **WHEN** a unit's move is not carried out because it cannot pay the movement cost
- **THEN** the order is reported to that unit's owner as refused for want of energy

#### Scenario: A move off the board

- **WHEN** a unit's move is not carried out because it would leave the board
- **THEN** the order is reported to that unit's owner as refused for leaving the board

#### Scenario: A move that was carried out

- **WHEN** a unit's move is carried out
- **THEN** nothing is reported for that order
