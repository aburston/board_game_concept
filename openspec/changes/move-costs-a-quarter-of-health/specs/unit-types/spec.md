## MODIFIED Requirements

### Requirement: Walls

The system SHALL allow a type with **no attack and no energy**, and SHALL
require the two to be zero together: a type with an attack of 0 and any energy
above 0 is refused, as is a type with energy 0 and any attack above 0. Such a
type is a **wall** — health standing on a square.

A wall SHALL never be able to move, because a move costs a quarter of its
health in energy and it has none, and regeneration gives nothing to a type
designed with none. It SHALL land no attacks: a round in which only walls could
act lands no attacks and ends the fight, rather than repeating for ever on an
attack that costs nothing and deals nothing. It SHALL block a square and be
destroyable like any other unit, and it SHALL cost its health and nothing else.

A wall SHALL be exempt from the rule that a type's energy is at least its
movement cost: 0 energy against a movement cost it can never pay is what makes
it a wall, and requiring otherwise would abolish the wall.

#### Scenario: A wall is defined

- **WHEN** a type is created with attack 0, health 10 and energy 0
- **THEN** the type is created
- **AND** it costs 10 points to deploy

#### Scenario: One zero without the other

- **WHEN** a type is created with attack 0 and energy above 0, or with energy 0 and attack above 0
- **THEN** creation fails

#### Scenario: A wall in a fight

- **WHEN** a unit steps onto a square held by a wall
- **THEN** the attacker pays for and lands its attacks
- **AND** the wall lands none and pays nothing
- **AND** the fight ends when the wall is destroyed or the attacker can no longer pay

#### Scenario: A wall is ordered to move

- **WHEN** a wall is ordered to move
- **THEN** the order is refused for want of energy
- **AND** the wall stays where it is

#### Scenario: A wall never recovers

- **WHEN** a turn resolves in which a wall took no action
- **THEN** its energy is still 0

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
