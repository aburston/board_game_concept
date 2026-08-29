# unit-types Specification

## Purpose

Unit types are the templates players design before a game starts. A type fixes a
unit's combat statistics and its single-character board symbol. Every unit placed
on the board is a copy of a type, so the constraints enforced here bound every
unit in play.

## Requirements

### Requirement: Unit Type Definition

The system SHALL define a unit type from a name, a display symbol, and three
integer statistics: attack, health, and energy.

#### Scenario: Defining a valid type

- **WHEN** a unit type is created with name `Attacker`, symbol `A`, attack 3, health 5, energy 100
- **THEN** the type is created with those values
- **AND** its state is `INITIAL` and its direction is `NONE`
- **AND** it is not destroyed and not on the board

### Requirement: Walls And Scouts

The system SHALL allow a type with **no attack**, with or without energy.

With **no energy** it is a **wall** — health standing on a square. A wall SHALL
never be able to move, because a move costs a quarter of its health in energy
and it has none, and regeneration gives nothing to a type designed with none.
It SHALL land no attacks: an exchange in which only walls stand lands no
attacks and destroys nobody. It SHALL block a square and be destroyable like
any other unit, and it SHALL cost its health and nothing else.

With **energy above 0** it is a **scout**: it moves like any other unit and
lands nothing when it arrives, taking whatever is dealt to it. A scout SHALL be
a unit like any other in every other respect - it blocks a square, it may carry
its player's flag, and because it has energy it can act, so it SHALL keep its
owner in the game where a wall does not.

What the system SHALL refuse is **energy 0 with an attack above 0**: an attack
the type could never pay for is a wall that was charged for a weapon.

A type with **no energy at all** SHALL be exempt from the rule that a type's
energy is at least its movement cost: 0 energy against a movement cost it can
never pay is what makes a wall, and requiring otherwise would abolish it. A
scout SHALL be held to that rule like anything else that means to move.

#### Scenario: A wall is defined

- **WHEN** a type is created with attack 0, health 10 and energy 0
- **THEN** the type is created
- **AND** it costs 10 points to deploy

#### Scenario: A scout is defined

- **WHEN** a type is created with attack 0, health 4 and energy 6
- **THEN** the type is created
- **AND** it costs 10 points to deploy, its attack adding nothing to the price

#### Scenario: An attack that could never be paid for

- **WHEN** a type is created with energy 0 and an attack above 0
- **THEN** creation fails

#### Scenario: A scout that could never afford a move

- **WHEN** a type is created with attack 0 and energy above 0 but below its movement cost
- **THEN** creation fails

#### Scenario: A wall in a fight

- **WHEN** a unit steps onto a square held by a wall
- **THEN** the attacker pays for and lands its attack
- **AND** the wall lands none and pays nothing

#### Scenario: A scout in a fight

- **WHEN** a scout steps onto a square an enemy holds
- **THEN** the scout lands no attack and pays nothing for one
- **AND** it takes the damage the enemy deals it
- **AND** it is destroyed if that damage exhausts its health

#### Scenario: A wall is ordered to move

- **WHEN** a wall is ordered to move
- **THEN** the order is refused for want of energy
- **AND** the wall stays where it is

#### Scenario: A scout is ordered to move

- **WHEN** a scout with energy for the fare is ordered to move
- **THEN** it moves, and pays the fare like any other unit

#### Scenario: A wall never recovers

- **WHEN** a turn resolves in which a wall took no action
- **THEN** its energy is still 0

#### Scenario: A scout keeps its owner in the game

- **WHEN** a player's only remaining unit is a scout
- **THEN** that player is not eliminated for having nothing that can act

### Requirement: Unit Type Validation

The system SHALL reject unit types whose fields fall outside their permitted
ranges, and SHALL do so at construction time rather than during play. Attack is
an integer from **0 to 10**, health an integer from **1 to 10**, and energy an
integer from **0 to 100**; attack and energy are zero only together, as the
Walls requirement states.

The system SHALL further require that a type that is not a wall is designed
with **energy at least equal to its movement cost** — a quarter of its health,
rounded up — and SHALL refuse it otherwise. A type with less energy than that
could never afford a single move at any point in its life; refusing it at
construction says so once, rather than leaving a player to discover it a turn
at a time from refused orders. The floor is the movement cost rather than the
health, so that it moves with the fare and cannot state a different rule from
the one movement charges.

#### Scenario: Name must be non-empty

- **WHEN** a type is created with an empty name
- **THEN** creation fails

#### Scenario: Symbol must be exactly one character

- **WHEN** a type is created with a symbol that is not exactly one character
- **THEN** creation fails

#### Scenario: Attack must be 0 to 10

- **WHEN** a type is created with a non-integer attack, or an attack below 0 or above 10
- **THEN** creation fails

#### Scenario: Health must be 1 to 10

- **WHEN** a type is created with a non-integer health, or a health below 1 or above 10
- **THEN** creation fails

#### Scenario: Energy must be 0 to 100

- **WHEN** a type is created with a non-integer energy, or an energy below 0 or above 100
- **THEN** creation fails

#### Scenario: Energy below the movement cost is refused

- **WHEN** a type with an attack above 0 is created with health 6 and energy 1
- **THEN** creation fails
- **AND** the failure names energy being below the movement cost as the reason

#### Scenario: Energy equal to the movement cost is allowed

- **WHEN** a type with an attack above 0 is created with health 6 and energy 2
- **THEN** the type is created
- **AND** a unit of that type can afford exactly one move before it must rest

#### Scenario: Energy that the old health floor would have refused is allowed

- **WHEN** a type with an attack above 0 is created with health 10 and energy 3
- **THEN** the type is created
- **AND** no type that was legal before this rule changed is refused by it

#### Scenario: A wall is not held to the rule

- **WHEN** a type is created with attack 0, health 7 and energy 0
- **THEN** the type is created, energy below its movement cost notwithstanding

### Requirement: Type Identity Survives Instantiation

The system SHALL preserve the originating type name on every unit instance
created from a type, so that a unit can be reported against the type it came
from even after it is renamed.

#### Scenario: Unit records its originating type

- **WHEN** a unit is created from type `Attacker` and renamed to `a1`
- **THEN** the unit's name is `a1`
- **AND** the unit still reports `Attacker` as its type name

### Requirement: Unit State And Direction Constants

The system SHALL expose a fixed vocabulary of movement directions and unit
lifecycle states shared by the engine, the clients, and the on-disk format.

#### Scenario: Direction constants

- **WHEN** direction constants are read
- **THEN** `NONE` is 0, `NORTH` is 1, `EAST` is 2, `SOUTH` is 3, and `WEST` is 4

#### Scenario: State constants

- **WHEN** state constants are read
- **THEN** `INITIAL` is 0, `MOVING` is 1, and `NOP` is 2

### Requirement: Statistic Semantics

The system SHALL interpret each unit statistic consistently across combat and
movement.

#### Scenario: Statistic meanings

- **WHEN** a unit type's statistics are interpreted
- **THEN** attack is the damage dealt per attack, and the energy that attack costs
- **AND** health is the total damage the unit absorbs before being destroyed,
  and a quarter of it, rounded up, is the energy each of its moves costs
- **AND** energy is the resource consumed by both moving and attacking

#### Scenario: Health is paid for twice over

- **WHEN** two types are compared that differ only in health
- **THEN** the heavier absorbs more damage before being destroyed
- **AND** the heavier pays at least as much energy for each square it moves
- **AND** the heavier therefore moves no more times than the lighter before it must rest

