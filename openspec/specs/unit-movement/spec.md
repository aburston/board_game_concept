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

### Requirement: Movement Is One Square Per Turn

The system SHALL move a unit at most one square per resolved turn, in the ordered
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

The system SHALL charge a unit its **maximum health** in energy to move, and
SHALL refuse the move when the unit cannot pay. Maximum health is the health
the unit's type was designed with, not the health the unit has left, so the
cost of a move never changes over a unit's life and two units of the same type
always pay the same to move. This SHALL apply to every resolved move, whatever
the unit finds at its destination, so that two units of the same type that have
made the same number of moves have paid the same for them.

#### Scenario: Paying for a move

- **WHEN** a unit whose type was designed with health 4 resolves a move
- **THEN** the cost charged is 4
- **AND** the unit's energy is reduced by 4

#### Scenario: The lightest unit pays the least

- **WHEN** a unit whose type was designed with health 1 resolves a move
- **THEN** the cost charged is 1

#### Scenario: The heaviest unit pays the most

- **WHEN** a unit whose type was designed with health 10 resolves a move
- **THEN** the cost charged is 10

#### Scenario: Damage does not change the fare

- **WHEN** a unit whose type was designed with health 6 has been reduced to 2 health and resolves a move
- **THEN** the cost charged is 6
- **AND** it is the same cost the unit paid for its moves while undamaged

#### Scenario: Insufficient energy

- **WHEN** a unit has less energy left than its maximum health
- **THEN** the unit does not move
- **AND** its energy is unchanged
- **AND** the order is reported to its owner as refused

#### Scenario: Paying to engage

- **WHEN** a unit moves onto a square held by a standing unit
- **THEN** it is charged its maximum health, as it would be for any other move
- **AND** two units of the same type that have made the same number of moves
  have paid the same for them, whatever they met on the way

#### Scenario: A unit with a single energy can still move

- **WHEN** a unit whose type was designed with health 1 has 1 energy and resolves a move
- **THEN** it moves
- **AND** its energy becomes 0

#### Scenario: A unit with exactly its fare can still move

- **WHEN** a unit whose energy is exactly equal to its maximum health resolves a move
- **THEN** it moves
- **AND** its energy becomes 0

### Requirement: Movement Into An Empty Square

The system SHALL move a unit into an empty destination square and vacate the square
it came from.

#### Scenario: Unopposed move

- **WHEN** a unit moves into an empty square and can pay the cost
- **THEN** the unit's previous square becomes empty
- **AND** the unit occupies the destination square

### Requirement: Movement Into A Contested Square

The system SHALL allow multiple units to enter the same destination square in the
same turn, collecting them for combat resolution rather than rejecting the move.

#### Scenario: Second unit enters a contested square

- **WHEN** two units are ordered into the same square in one turn and both can pay
- **THEN** both are in that square once the moves have been applied
- **AND** both of their previous squares become empty
- **AND** the square is contested

### Requirement: Movement Into An Occupied Square Starts Combat

The system SHALL treat a move into a square another unit finishes the turn in as
an attack. The mover SHALL need only the energy to pay for the move — its
maximum health — and nothing more; a mover that cannot afford to attack still
arrives, and is inert in the contest it has walked into.

#### Scenario: Attacking a standing unit

- **WHEN** a unit that can pay the movement cost moves into a square another unit holds
- **THEN** both units are in that square once the moves have been applied
- **AND** the square is contested
- **AND** the attacker's previous square becomes empty

#### Scenario: Too little energy to attack

- **WHEN** a unit that could pay to move has energy below its attack value once it has arrived in an occupied square
- **THEN** it still moves
- **AND** the square is contested
- **AND** it deals no damage in that contest, being unable to pay for an attack

#### Scenario: Too little energy to arrive

- **WHEN** a unit has less energy than its maximum health
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
- **THEN** every unit finishes the turn in the same square with the same health and energy
- **AND** the same squares are contested

#### Scenario: Following a unit that moves away

- **WHEN** a unit is ordered into a square whose occupant is ordered out of it in the same turn, and both moves are carried out
- **THEN** the mover occupies that square alone
- **AND** no contest is started

#### Scenario: A chain of units advancing together

- **WHEN** three units stand in a line and each is ordered one square in the same direction, the leading unit into an empty square
- **THEN** all three move
- **AND** no square is contested

#### Scenario: Moving into a square whose occupant stays

- **WHEN** a unit is ordered into a square whose occupant is given no order, or whose order is not carried out
- **THEN** both units are in that square once the moves have been applied
- **AND** the square is contested

### Requirement: Contention Is Decided By Where Units Finish

The system SHALL treat as contested every square holding more than one unit once
all of this turn's moves have been applied, however the units came to share it.

#### Scenario: Two movers and a stander

- **WHEN** two units move into a square a third unit is holding
- **THEN** all three contest that square

#### Scenario: A square nobody shares

- **WHEN** every unit finishes the turn in a square of its own
- **THEN** no square is contested
- **AND** no combat is resolved

### Requirement: Two Units Trading Squares Collide

The system SHALL treat two units ordered into each other's squares as a head-on
collision rather than letting them pass through each other. Neither unit
completes its move before the collision is resolved; each unit is charged its
own movement cost, which is its own maximum health and need not equal the
other's; and they fight on the same terms as any other contest.

#### Scenario: A head-on collision is fought

- **WHEN** two adjacent units are each ordered into the square the other holds, and both can pay their movement cost
- **THEN** each is charged its own maximum health
- **AND** they exchange attacks as contestants do
- **AND** each records the other as seen

#### Scenario: Colliding units of different weights pay differently

- **WHEN** a unit of maximum health 2 and a unit of maximum health 9 collide head-on and both can pay
- **THEN** the first is charged 2 and the second 9

#### Scenario: One unit survives the collision

- **WHEN** a head-on collision destroys exactly one of the two units
- **THEN** the survivor completes its move into the square the destroyed unit held
- **AND** the square the survivor came from is left empty

#### Scenario: Neither unit survives the collision

- **WHEN** a head-on collision destroys both units
- **THEN** both squares are left empty

#### Scenario: A collision neither unit can decide

- **WHEN** a head-on collision ends with both units undestroyed
- **THEN** each unit stays in the square it started the turn in
- **AND** neither is destroyed

#### Scenario: Units cannot pass through each other

- **WHEN** two units are ordered into each other's squares
- **THEN** neither finishes the turn in the square the other started it in unless the other was destroyed

#### Scenario: Only one of the two can pay

- **WHEN** two adjacent units are each ordered into the square the other holds and only one can pay its movement cost
- **THEN** the one that cannot pay does not move, keeps its energy, and is reported to its owner as refused
- **AND** no head-on collision is fought
- **AND** the payer moves into the square the other is holding and contests it

### Requirement: A Move That Is Not Carried Out Is Reported

The system SHALL report to the ordering player every movement order that does
not do what it said, naming the unit, its square, and the reason, rather than
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
