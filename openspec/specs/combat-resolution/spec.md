# combat-resolution Specification

## Purpose

Combat happens wherever more than one unit ends up in the same cell, whether by
attacking a standing unit or by two units moving into the same empty cell at
once. Combat is simultaneous and runs to a decision within the turn: it repeats
until at most one unit is left standing in the cell.

## Requirements

### Requirement: Contested Cells Trigger Combat

The system SHALL resolve combat in every cell holding more than one unit at the
end of the movement phase.

#### Scenario: Attacker enters an occupied cell

- **WHEN** a unit moves into a cell held by an enemy unit
- **THEN** combat is resolved between them in that cell

#### Scenario: Two units enter the same empty cell

- **WHEN** two units move into the same empty cell in the same turn
- **THEN** combat is resolved between them in that cell

### Requirement: Simultaneous Attack Exchange

The system SHALL have every unit standing in a contested cell at the start of a
round attack every other unit standing there, with all attacks in a round
applying regardless of the damage those attacks receive in the same round.

#### Scenario: Both units strike

- **WHEN** two units contest a cell
- **THEN** each deals its attack value in damage to the other
- **AND** neither is spared by having been damaged in the same round

#### Scenario: A unit does not attack itself

- **WHEN** attacks are resolved in a contested cell
- **THEN** no unit attacks itself

### Requirement: Attacking Costs Energy

The system SHALL charge a unit its attack value in energy for each attack it
makes, and SHALL prevent the unit from attacking when it cannot pay.

#### Scenario: Paying to attack

- **WHEN** a unit attacks
- **THEN** its energy is reduced by its attack value

#### Scenario: Exhausted unit cannot attack

- **WHEN** a unit's energy is below its attack value
- **THEN** it deals no damage
- **AND** its energy is unchanged

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

#### Scenario: Undecided when no contestant can attack

- **WHEN** a round begins in which every surviving contestant has less energy than its attack value
- **THEN** no damage is dealt
- **AND** combat ends for that cell
- **AND** no unit is destroyed

#### Scenario: Termination is guaranteed

- **WHEN** combat is resolved in any contested cell
- **THEN** resolution completes in a bounded number of rounds
- **AND** the turn proceeds regardless of whether the contest was decided

### Requirement: Cell Ownership After Combat

The system SHALL leave the surviving unit in sole possession of the contested
cell when the contest is decided, SHALL empty the cell when no unit survives,
and SHALL return every survivor that moved into the cell to the cell it came
from when the contest is undecided.

#### Scenario: One survivor

- **WHEN** combat leaves exactly one undestroyed unit in a cell
- **THEN** that unit alone occupies the cell

#### Scenario: No survivors

- **WHEN** combat destroys every unit contesting a cell
- **THEN** the cell becomes empty

#### Scenario: Undecided contest between units that all moved in

- **WHEN** combat ends undecided and every survivor moved into the cell this turn
- **THEN** each survivor is returned to the cell it came from
- **AND** no survivor is destroyed
- **AND** the contested cell is left empty

#### Scenario: Undecided contest against a unit that held the cell

- **WHEN** combat ends undecided between a unit that moved in and a unit already holding the cell
- **THEN** the unit that moved in is returned to the cell it came from
- **AND** the unit that held the cell keeps it

#### Scenario: Survivor with nowhere to fall back

- **WHEN** combat ends undecided and a survivor cannot return to the cell it left, because another unit moved into that cell during the same turn
- **THEN** that survivor remains in the contested cell
- **AND** it remains on the board
- **AND** the cell is treated as occupied by any unit attempting to enter it

### Requirement: Destroyed Units Leave The Board

The system SHALL remove destroyed units from play, marking them as no longer on
the board and taking them out of the cell they held without disturbing any unit
still standing in it.

#### Scenario: Removing a destroyed unit

- **WHEN** a unit is destroyed
- **THEN** it is marked as not on the board
- **AND** it no longer occupies a cell
- **AND** it is not considered for movement or combat in later turns

#### Scenario: A destroyed unit sharing a cell

- **WHEN** a unit is destroyed in a cell another unit still holds
- **THEN** the destroyed unit is taken out of that cell
- **AND** the unit still standing remains in that cell and on the board

### Requirement: Inert Units

The system SHALL treat a unit that can no longer pay for an action as inert
rather than removed: it stays on the board, holds its cell, obstructs movement,
and can only be cleared by an opponent destroying it.

#### Scenario: Inert unit cannot attack

- **WHEN** a unit's energy is below its attack value
- **THEN** it cannot attack
- **AND** it is not destroyed
- **AND** it stays on the board

#### Scenario: Inert unit still blocks

- **WHEN** another unit attempts to enter the cell an inert unit holds
- **THEN** the cell is treated as occupied and entering it requires an attack

#### Scenario: Inert unit can still be destroyed

- **WHEN** an opponent with enough energy attacks an inert unit
- **THEN** the inert unit takes damage as normal
- **AND** it is destroyed once its health is exhausted

### Requirement: Friendly Fire

The system SHALL have every unit in a contested cell attack every other unit in
that cell, without regard to which player owns it.

#### Scenario: Units of the same player contest a cell

- **WHEN** two units belonging to the same player contest a cell
- **THEN** they attack each other on the same terms as units of opposing players
- **AND** either may be destroyed

#### Scenario: Attacks are not limited to opponents

- **WHEN** a cell is contested by units of more than one player
- **THEN** each unit attacks every other unit in the cell regardless of owner

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
