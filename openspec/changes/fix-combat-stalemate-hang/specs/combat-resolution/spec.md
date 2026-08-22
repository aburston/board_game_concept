## MODIFIED Requirements

### Requirement: Combat Runs To A Decision

The system SHALL repeat attack rounds in a contested square until either at most
one unit remains undestroyed or a round deals no damage, and SHALL terminate
within the turn in every case.

#### Scenario: Attrition over multiple rounds

- **WHEN** an attacker with attack 3 and health 5 engages a defender with attack 2 and health 4
- **THEN** rounds repeat until the defender is destroyed
- **AND** the attacker survives with health 1

#### Scenario: Stronger unit takes the square

- **WHEN** a unit with attack 4 and health 7 contests a square with a unit with attack 3 and health 5
- **THEN** the weaker unit is destroyed
- **AND** the stronger unit holds the square

#### Scenario: Undecided when no contestant can attack

- **WHEN** a round begins in which every surviving contestant has less energy than its attack value
- **THEN** no damage is dealt
- **AND** combat ends for that square
- **AND** no unit is destroyed

#### Scenario: Termination is guaranteed

- **WHEN** combat is resolved in any contested square
- **THEN** resolution completes in a bounded number of rounds
- **AND** the turn proceeds regardless of whether the contest was decided

### Requirement: Damage And Destruction

The system SHALL subtract incoming damage from a unit's health and SHALL destroy
the unit when its health is exhausted. Health is the only thing that destroys a
unit.

#### Scenario: Taking damage

- **WHEN** a unit takes damage
- **THEN** its health is reduced by the attack value

#### Scenario: Health exhausted

- **WHEN** a unit's health reaches zero or below
- **THEN** the unit is marked destroyed

#### Scenario: Running out of energy does not destroy a unit

- **WHEN** a unit's energy falls below what it needs to act
- **THEN** the unit is not destroyed
- **AND** it remains on the board holding its square

### Requirement: Square Ownership After Combat

The system SHALL leave the surviving unit in sole possession of the contested
square when the contest is decided, SHALL empty the square when no unit survives,
and SHALL return every survivor that moved into the square to the square it came
from when the contest is undecided.

#### Scenario: One survivor

- **WHEN** combat leaves exactly one undestroyed unit in a square
- **THEN** that unit alone occupies the square

#### Scenario: No survivors

- **WHEN** combat destroys every unit contesting a square
- **THEN** the square becomes empty

#### Scenario: Undecided contest between units that all moved in

- **WHEN** combat ends undecided and every survivor moved into the square this turn
- **THEN** each survivor is returned to the square it came from
- **AND** no survivor is destroyed
- **AND** the contested square is left empty

#### Scenario: Undecided contest against a unit that held the square

- **WHEN** combat ends undecided between a unit that moved in and a unit already holding the square
- **THEN** the unit that moved in is returned to the square it came from
- **AND** the unit that held the square keeps it

#### Scenario: Survivor with nowhere to fall back

- **WHEN** combat ends undecided and a survivor cannot return to the square it left, because another unit moved into that square during the same turn
- **THEN** that survivor remains in the contested square
- **AND** it remains on the board
- **AND** the square is treated as occupied by any unit attempting to enter it

## ADDED Requirements

### Requirement: Inert Units

The system SHALL treat a unit that can no longer pay for an action as inert
rather than removed: it stays on the board, holds its square, obstructs movement,
and can only be cleared by an opponent destroying it.

#### Scenario: Inert unit cannot attack

- **WHEN** a unit's energy is below its attack value
- **THEN** it cannot attack
- **AND** it is not destroyed
- **AND** it stays on the board

#### Scenario: Inert unit still blocks

- **WHEN** another unit attempts to enter the square an inert unit holds
- **THEN** the square is treated as occupied and entering it requires an attack

#### Scenario: Inert unit can still be destroyed

- **WHEN** an opponent with enough energy attacks an inert unit
- **THEN** the inert unit takes damage as normal
- **AND** it is destroyed once its health is exhausted

### Requirement: Friendly Fire

The system SHALL have every unit in a contested square attack every other unit in
that square, without regard to which player owns it.

#### Scenario: Units of the same player contest a square

- **WHEN** two units belonging to the same player contest a square
- **THEN** they attack each other on the same terms as units of opposing players
- **AND** either may be destroyed

#### Scenario: Attacks are not limited to opponents

- **WHEN** a square is contested by units of more than one player
- **THEN** each unit attacks every other unit in the square regardless of owner

### Requirement: Attackers Are The Units Standing At The Start Of A Round

The system SHALL draw both attackers and targets for a round from the units
undestroyed when that round begins, so that a unit destroyed during a round
still lands its own attack for that round and takes no part in later rounds.

#### Scenario: A unit destroyed mid-round still strikes

- **WHEN** a unit is destroyed by an attack during a round
- **THEN** its own attack for that round is still applied

#### Scenario: A destroyed unit takes no part in later rounds

- **WHEN** a round begins after a unit has been destroyed
- **THEN** that unit neither attacks nor is attacked
