## ADDED Requirements

### Requirement: Walls

The system SHALL allow a type with **no attack and no energy**, and SHALL
require the two to be zero together: a type with an attack of 0 and any energy
above 0 is refused, as is a type with energy 0 and any attack above 0. Such a
type is a **wall** — health standing on a square.

A wall SHALL never be able to move, because a move costs energy it does not
have and regeneration gives nothing to a type designed with none. It SHALL land
no attacks: a round in which only walls could act lands no attacks and ends the
fight, rather than repeating for ever on an attack that costs nothing and deals
nothing. It SHALL block a square and be destroyable like any other unit, and it
SHALL cost its health and nothing else.

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

## MODIFIED Requirements

### Requirement: Unit Type Validation

The system SHALL reject unit types whose fields fall outside their permitted
ranges, and SHALL do so at construction time rather than during play. Attack is
an integer from **0 to 10**, health an integer from **1 to 10**, and energy an
integer from **0 to 100**; attack and energy are zero only together, as the
Walls requirement states.

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
