## MODIFIED Requirements

### Requirement: Combat Runs To A Decision

The system SHALL repeat attack rounds in a contested cell until either at most
one unit remains undestroyed or a round deals no damage, and SHALL terminate
within the turn in every case.

#### Scenario: Attrition over multiple rounds

- **WHEN** an attacker with attack 3 and health 5 engages a defender with attack 2 and health 4
- **THEN** rounds repeat until the defender is destroyed
- **AND** the attacker survives with health 1

#### Scenario: Stronger unit takes the cell

- **WHEN** a unit with attack 4 and health 7 contests a cell with a unit with attack 3 and health 5
- **THEN** the weaker unit is destroyed
- **AND** the stronger unit holds the cell

#### Scenario: Stalemate when no contestant can attack

- **WHEN** a round begins in which every surviving contestant has less energy than its attack value
- **THEN** no damage is dealt
- **AND** combat ends for that cell
- **AND** no unit is destroyed

#### Scenario: Termination is guaranteed

- **WHEN** combat is resolved in any contested cell
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
- **AND** it remains on the board holding its cell

### Requirement: Cell Ownership After Combat

The system SHALL leave the surviving unit in sole possession of the contested
cell when the contest is decided, SHALL empty the cell when no unit survives,
and SHALL leave the survivors stacked in the cell when the contest is undecided.

#### Scenario: One survivor

- **WHEN** combat leaves exactly one undestroyed unit in a cell
- **THEN** that unit alone occupies the cell

#### Scenario: No survivors

- **WHEN** combat destroys every unit contesting a cell
- **THEN** the cell becomes empty

#### Scenario: Undecided contest leaves units stacked

- **WHEN** combat ends in stalemate with more than one unit surviving
- **THEN** every survivor remains in that cell
- **AND** each survivor remains on the board
- **AND** the cell is treated as occupied by any unit attempting to enter it

## ADDED Requirements

### Requirement: Inert Units

The system SHALL treat a unit that can no longer pay for any action as inert
rather than removed: it holds its cell, obstructs movement, and can only be
cleared by an opponent destroying it.

#### Scenario: Inert unit cannot act

- **WHEN** a unit's energy is below both its attack value and the cost of moving
- **THEN** it cannot attack and cannot move

#### Scenario: Inert unit still blocks

- **WHEN** another unit attempts to enter the cell an inert unit holds
- **THEN** the cell is treated as occupied and entering it requires an attack

#### Scenario: Inert unit can still be destroyed

- **WHEN** an opponent with enough energy attacks an inert unit
- **THEN** the inert unit takes damage as normal
- **AND** it is destroyed once its health is exhausted
