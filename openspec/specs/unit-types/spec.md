# unit-types Specification

## Purpose

Unit types are the templates players design before a game starts. A type fixes a
unit's combat statistics and its single-character board symbol. Every unit placed
on the board is a copy of a type, so the constraints enforced here bound every
unit in play.

## Requirements

### Requirement: Unit Type Definition

The system SHALL define a unit type from a name, a display symbol, four
integer statistics - attack, health, energy and compute - and a program,
which MAY be empty. Compute SHALL be an integer from 0 to 10. A type with
compute 0 SHALL have no controller and SHALL carry no program.

#### Scenario: Defining a valid type

- **WHEN** a unit type is created with name `Attacker`, symbol `A`, attack 3, health 5, energy 100, compute 4
- **THEN** the type is created with those values
- **AND** its state is `INITIAL` and its direction is `NONE`
- **AND** it is not destroyed and not on the board

#### Scenario: Defining a type with a program

- **WHEN** a unit type is created with compute above 0 and a program
- **THEN** the type is created and every unit of it runs that program

#### Scenario: Defining a type without a controller

- **WHEN** a unit type is created with compute 0
- **THEN** the type is created
- **AND** setting a program on it is refused

### Requirement: Walls And Scouts

The system SHALL allow a type with **no attack**, with or without energy, and
SHALL allow a type with **no compute**, with or without attack and energy.

With **no energy** and no attack it is a **wall** - health standing on a
square. A wall SHALL never be able to move, because a move costs a quarter of
its health in energy and it has none, and regeneration gives nothing to a type
designed with none. It SHALL land no attacks: an exchange in which only walls
stand lands no attacks and destroys nobody. It SHALL block a square and be
destroyable like any other unit, and it SHALL cost its health and nothing
else. A wall SHALL have no compute: there is nothing for a controller to do
with a unit that cannot act.

With **energy above 0** and no attack it is a **scout**: it moves like any
other unit and lands nothing when it arrives, taking whatever is dealt to it.
A scout SHALL be a unit like any other in every other respect - it blocks a
square, it may carry its player's flag, and because it has energy it can act,
so it SHALL keep its owner in the game where a wall does not.

With **no compute** but attack and energy above 0 it is a **turret**: it has
no controller, so it is never ordered and never moves, but it strikes back at
whatever contests its square if it can pay its attack, and it rests like any
unit that did nothing. A turret SHALL keep its owner in the game, because it
can act. A type with no compute SHALL be exempt from the rule that a type's
energy is at least its movement cost, since it can never be ordered to move.

What the system SHALL refuse is **energy 0 with an attack above 0**: an attack
the type could never pay for is a wall that was charged for a weapon.

A type with **no energy at all** SHALL be exempt from the rule that a type's
energy is at least its movement cost: 0 energy against a movement cost it can
never pay is what makes a wall, and requiring otherwise would abolish it. A
scout with compute SHALL be held to that rule like anything else that means
to move.

#### Scenario: A wall is defined

- **WHEN** a type is created with attack 0, health 10, energy 0 and compute 0
- **THEN** the type is created
- **AND** it costs 10 points to deploy

#### Scenario: A scout is defined

- **WHEN** a type is created with attack 0, health 4, energy 6 and compute 2
- **THEN** the type is created
- **AND** it costs 12 points to deploy, its attack adding nothing to the price

#### Scenario: A turret is defined

- **WHEN** a type is created with attack 3, health 6, energy 6 and compute 0
- **THEN** the type is created
- **AND** it costs 15 points to deploy
- **AND** units of it are never ordered to move

#### Scenario: A turret in a fight

- **WHEN** a unit steps onto a square held by a turret that can pay its attack
- **THEN** both pay for and land their attacks
- **AND** the turret rests on turns in which nothing contests its square

#### Scenario: A turret need not afford a move

- **WHEN** a type is created with attack 5, health 10, energy 1 and compute 0
- **THEN** the type is created, energy below its movement cost notwithstanding

#### Scenario: A wall with compute

- **WHEN** a type is created with attack 0, energy 0 and compute above 0
- **THEN** creation fails

#### Scenario: An attack that could never be paid for

- **WHEN** a type is created with energy 0 and an attack above 0
- **THEN** creation fails

#### Scenario: A scout that could never afford a move

- **WHEN** a type is created with attack 0, compute above 0 and energy above 0 but below its movement cost
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

- **WHEN** a turn resolves
- **THEN** no wall has been ordered to move, having no controller to order it
- **AND** every wall is where it was

#### Scenario: A scout is ordered to move

- **WHEN** a scout's program orders a move it has the energy for
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
an integer from **0 to 10**, health an integer from **1 to 10**, energy an
integer from **0 to 100**, and compute an integer from **0 to 10**; attack and
energy are zero only together, as the Walls requirement states, and a type
with energy 0 has compute 0.

A symbol SHALL be exactly one character and that character SHALL NOT be
whitespace. A blank square is what the board draws where nothing stands, so a
unit drawn with a space would be a unit the board hid. Every other single
printable character is a symbol a player may choose, `#` among them: nothing
about the board's own drawing reserves one.

The system SHALL further require that a type with compute above 0 and energy
above 0 is designed with **energy at least equal to its movement cost** - a
quarter of its health, rounded up - and SHALL refuse it otherwise. A type with
less energy than that could never afford a single move at any point in its
life; refusing it at construction says so once, rather than leaving a player
to discover it a turn at a time from refused orders. The floor is the movement
cost rather than the health, so that it moves with the fare and cannot state a
different rule from the one movement charges. A type with no compute is not
held to it, since nothing can order it to move.

A program SHALL be checked when it is set, as `unit-program` requires, and a
type SHALL NOT be created with a program on compute 0.

#### Scenario: Name must be non-empty

- **WHEN** a type is created with an empty name
- **THEN** creation fails

#### Scenario: Symbol must be exactly one character

- **WHEN** a type is created with a symbol that is not exactly one character
- **THEN** creation fails

#### Scenario: Symbol must not be whitespace

- **WHEN** a type is created with a symbol that is a space, a tab, or any other
  whitespace character
- **THEN** creation fails, whether the definition arrives from a command line
  or over HTTP

#### Scenario: A hash is an ordinary symbol

- **WHEN** a type is created with the symbol `#`
- **THEN** the type is created, and units of it are placed, drawn and named in
  the legend like units of any other type

#### Scenario: Attack must be 0 to 10

- **WHEN** a type is created with a non-integer attack, or an attack below 0 or above 10
- **THEN** creation fails

#### Scenario: Health must be 1 to 10

- **WHEN** a type is created with a non-integer health, or a health below 1 or above 10
- **THEN** creation fails

#### Scenario: Energy must be 0 to 100

- **WHEN** a type is created with a non-integer energy, or an energy below 0 or above 100
- **THEN** creation fails

#### Scenario: Compute must be 0 to 10

- **WHEN** a type is created with a non-integer compute, or a compute below 0 or above 10
- **THEN** creation fails

#### Scenario: Energy below the movement cost is refused

- **WHEN** a type with an attack above 0 and compute above 0 is created with health 6 and energy 1
- **THEN** creation fails
- **AND** the failure names energy being below the movement cost as the reason

#### Scenario: Energy equal to the movement cost is allowed

- **WHEN** a type with an attack above 0 and compute above 0 is created with health 6 and energy 2
- **THEN** the type is created
- **AND** a unit of that type can afford exactly one move before it must rest

#### Scenario: Energy that the old health floor would have refused is allowed

- **WHEN** a type with an attack above 0 and compute above 0 is created with health 10 and energy 3
- **THEN** the type is created
- **AND** no type that was legal before this rule changed is refused by it

#### Scenario: A wall is not held to the rule

- **WHEN** a type is created with attack 0, health 7, energy 0 and compute 0
- **THEN** the type is created, energy below its movement cost notwithstanding

#### Scenario: A type with no controller is not held to the rule

- **WHEN** a type is created with attack 2, health 8, energy 1 and compute 0
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

The system SHALL interpret each unit statistic consistently across combat,
movement and thinking.

#### Scenario: Statistic meanings

- **WHEN** a unit type's statistics are interpreted
- **THEN** attack is the damage dealt per attack, and the energy that attack costs
- **AND** health is the total damage the unit absorbs before being destroyed,
  and a quarter of it, rounded up, is the energy each of its moves costs
- **AND** energy is the resource consumed by moving, attacking and thinking
- **AND** compute is the number of ticks of thinking, times ten, that one
  energy buys, and the cap on ticks in one turn, times ten

#### Scenario: Health is paid for twice over

- **WHEN** two types are compared that differ only in health
- **THEN** the heavier absorbs more damage before being destroyed
- **AND** the heavier pays at least as much energy for each square it moves
- **AND** the heavier therefore moves no more times than the lighter before it must rest

#### Scenario: Compute is paid for once and saves for ever

- **WHEN** two types are compared that differ only in compute, running the same program
- **THEN** the one with more compute costs more points
- **AND** it pays energy to its meter less often for the same thinking
