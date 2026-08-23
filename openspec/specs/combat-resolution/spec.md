# combat-resolution Specification

## Purpose

Combat happens wherever more than one unit ends up in the same square, whether by
attacking a standing unit or by two units moving into the same empty square at
once. Combat is simultaneous and runs to a decision within the turn: it repeats
until at most one unit is left standing in the square.

## Requirements

### Requirement: Contested Squares Trigger Combat

The system SHALL resolve combat in every square holding more than one unit at the
end of the movement phase.

#### Scenario: Attacker enters an occupied square

- **WHEN** a unit moves into a square held by an enemy unit
- **THEN** combat is resolved between them in that square

#### Scenario: Two units enter the same empty square

- **WHEN** two units move into the same empty square in the same turn
- **THEN** combat is resolved between them in that square

### Requirement: Simultaneous Attack Exchange

The system SHALL have every unit standing in a contested square at the start of a
round attack every other unit standing there, with all attacks in a round
applying regardless of the damage those attacks receive in the same round.

#### Scenario: Both units strike

- **WHEN** two units contest a square
- **THEN** each deals its attack value in damage to the other
- **AND** neither is spared by having been damaged in the same round

#### Scenario: A unit does not attack itself

- **WHEN** attacks are resolved in a contested square
- **THEN** no unit attacks itself

### Requirement: Attacking Costs Energy

The system SHALL charge a unit its attack value in energy once for each round of
a contest in which it attacks, however many opponents it strikes in that round,
and SHALL prevent the unit from attacking when it cannot pay. A round SHALL be
all or nothing: a unit that cannot pay makes no attack at all, so no opponent is
favoured by where it happens to sit in the square.

#### Scenario: Paying to attack

- **WHEN** a unit attacks
- **THEN** its energy is reduced by its attack value

#### Scenario: Paying once however many opponents there are

- **WHEN** a unit attacks in a round of a contest against two or more opponents
- **THEN** its energy is reduced by its attack value once
- **AND** it deals its attack value in damage to every one of those opponents

#### Scenario: Exhausted unit cannot attack

- **WHEN** a unit's energy is below its attack value
- **THEN** it deals no damage
- **AND** its energy is unchanged

#### Scenario: A round is all or nothing

- **WHEN** a unit that cannot pay for a round contests a square with two or more opponents
- **THEN** it strikes none of them
- **AND** which opponents it would have struck does not depend on the order the square holds them in

#### Scenario: Outlasting a crowd

- **WHEN** a unit with energy for N rounds contests a square against several opponents
- **THEN** it can still attack in N rounds
- **AND** the number of opponents does not shorten how long it can fight

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

### Requirement: Destroyed Units Leave The Board

The system SHALL remove destroyed units from play, marking them as no longer on
the board and taking them out of the square they held without disturbing any unit
still standing in it. A destroyed unit SHALL be kept as a record of what was
lost, and SHALL never again act, be acted on, or occupy a square.

#### Scenario: Removing a destroyed unit

- **WHEN** a unit is destroyed
- **THEN** it is marked as not on the board
- **AND** it no longer occupies a square
- **AND** it is not considered for movement or combat in later turns

#### Scenario: A destroyed unit sharing a square

- **WHEN** a unit is destroyed in a square another unit still holds
- **THEN** the destroyed unit is taken out of that square
- **AND** the unit still standing remains in that square and on the board

#### Scenario: A destroyed unit is kept as a record

- **WHEN** the units of a game are listed after one has been destroyed
- **THEN** the destroyed unit is listed, marked destroyed and off the board
- **AND** it is not drawn on any square of the board

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

### Requirement: A Destroyed Unit Never Returns To Play

The system SHALL treat destruction as final. A destroyed unit SHALL NOT be
deployed, restored to the board, or recreated under its own name for the rest of
the game, whatever a later order asks for, and no square falling empty SHALL bring
it back.

#### Scenario: An order would put a destroyed unit back on the board

- **WHEN** a turn is resolved and an order names a unit that has been destroyed
- **THEN** the order is not carried out
- **AND** no unit is created

#### Scenario: The square a unit died on falls empty

- **WHEN** the square a destroyed unit occupied when it died is empty at the start of a later turn
- **THEN** the destroyed unit does not reappear on it
- **AND** the square stays empty unless a living unit moves onto it

#### Scenario: Another unit takes the square a unit died on

- **WHEN** a living unit moves onto the square a destroyed unit died on
- **THEN** it holds that square alone
- **AND** the destroyed unit does not contest it

#### Scenario: A destroyed unit's name is not reusable

- **WHEN** a player attempts to create a new unit with the name of one of their destroyed units
- **THEN** the attempt is refused
- **AND** no unit is created

#### Scenario: A destroyed unit survives a reload as destroyed

- **WHEN** a game holding a destroyed unit is saved and loaded again
- **THEN** that unit is still destroyed and still off the board
- **AND** it takes no part in the next turn

### Requirement: An Undecided Contest Is Reported

The system SHALL tell every player whose unit was in a contest that ended
undecided that it did so, naming the unit and the square, so that a player can see
why two units that met achieved nothing and stop paying to repeat it.

#### Scenario: A contest neither side could decide

- **WHEN** a contest ends with more than one unit undestroyed
- **THEN** each contestant's owner is told that unit's contest ended undecided, and where

#### Scenario: A contest that was decided

- **WHEN** a contest ends with at most one unit undestroyed
- **THEN** nothing is reported as undecided
