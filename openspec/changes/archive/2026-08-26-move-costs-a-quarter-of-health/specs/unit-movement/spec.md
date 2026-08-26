## MODIFIED Requirements

### Requirement: Movement Costs Energy

The system SHALL charge a unit **a quarter of its maximum health, rounded up**,
in energy to move, and SHALL refuse the move when the unit cannot pay. Maximum
health is the health the unit's type was designed with, not the health the unit
has left, so the cost of a move never changes over a unit's life and two units
of the same type always pay the same to move. Health is an integer from 1 to
10, so the cost is 1 for health 1 to 4, 2 for health 5 to 8, and 3 for health 9
or 10.

Rounding SHALL be upward, so that every unit that can move pays at least 1 for
a move. A unit that moved for nothing would be outside the energy economy the
rest of the game is built on, and the lightest units are the ones that would
escape it.

This SHALL apply to every resolved move, whatever the unit finds at its
destination, so that two units of the same type that have made the same number
of moves have paid the same for them.

#### Scenario: Paying for a move

- **WHEN** a unit whose type was designed with health 4 resolves a move
- **THEN** the cost charged is 1
- **AND** the unit's energy is reduced by 1

#### Scenario: A heavier unit pays more

- **WHEN** a unit whose type was designed with health 5 resolves a move
- **THEN** the cost charged is 2

#### Scenario: The heaviest unit pays the most

- **WHEN** a unit whose type was designed with health 10 resolves a move
- **THEN** the cost charged is 3

#### Scenario: The lightest unit pays the least

- **WHEN** a unit whose type was designed with health 1 resolves a move
- **THEN** the cost charged is 1

#### Scenario: The fare is never zero

- **WHEN** a unit of any permitted health resolves a move
- **THEN** the cost charged is at least 1

#### Scenario: Damage does not change the fare

- **WHEN** a unit whose type was designed with health 8 has been damaged to 1 health and resolves a move
- **THEN** the cost charged is 2
- **AND** it is the same cost the unit paid for its moves while undamaged

#### Scenario: Insufficient energy

- **WHEN** a unit has less energy left than a quarter of its maximum health, rounded up
- **THEN** the unit does not move
- **AND** its energy is unchanged
- **AND** the order is reported to its owner as refused

#### Scenario: Paying to engage

- **WHEN** a unit moves onto a square held by a standing unit
- **THEN** it is charged a quarter of its maximum health, rounded up, as it would be for any other move
- **AND** two units of the same type that have made the same number of moves
  have paid the same for them, whatever they met on the way

#### Scenario: A unit with a single energy can still move

- **WHEN** a unit whose type was designed with health 1 has 1 energy and resolves a move
- **THEN** it moves
- **AND** its energy becomes 0

#### Scenario: A unit with exactly its fare can still move

- **WHEN** a unit whose energy is exactly equal to a quarter of its maximum health, rounded up, resolves a move
- **THEN** it moves
- **AND** its energy becomes 0

### Requirement: Movement Into An Occupied Square Starts Combat

The system SHALL treat a move into a square another unit finishes the turn in as
an attack. The mover SHALL need only the energy to pay for the move — a quarter
of its maximum health, rounded up — and nothing more; a mover that cannot afford
to attack still arrives, and is inert in the contest it has walked into.

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

- **WHEN** a unit has less energy than a quarter of its maximum health, rounded up
- **THEN** the unit does not move
- **AND** no contest is started on its account
- **AND** the order is reported to its owner as refused

### Requirement: Two Units Trading Squares Collide

The system SHALL treat two units ordered into each other's squares as a head-on
collision rather than letting them pass through each other. Neither unit
completes its move before the collision is resolved; each unit is charged its
own movement cost, which is a quarter of its own maximum health rounded up and
need not equal the other's; and they fight on the same terms as any other
contest.

#### Scenario: A head-on collision is fought

- **WHEN** two adjacent units are each ordered into the square the other holds, and both can pay their movement cost
- **THEN** each is charged a quarter of its own maximum health, rounded up
- **AND** they exchange attacks as contestants do
- **AND** each records the other as seen

#### Scenario: Colliding units of different weights pay differently

- **WHEN** a unit of maximum health 2 and a unit of maximum health 9 collide head-on and both can pay
- **THEN** the first is charged 1 and the second 3

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
