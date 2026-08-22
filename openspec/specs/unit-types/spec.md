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

### Requirement: Unit Type Validation

The system SHALL reject unit types whose fields fall outside their permitted
ranges, and SHALL do so at construction time rather than during play.

#### Scenario: Name must be non-empty

- **WHEN** a type is created with an empty name
- **THEN** creation fails

#### Scenario: Symbol must be exactly one character

- **WHEN** a type is created with a symbol that is not exactly one character
- **THEN** creation fails

#### Scenario: Attack must be 1 to 10

- **WHEN** a type is created with a non-integer attack, or an attack below 1 or above 10
- **THEN** creation fails

#### Scenario: Health must be 1 to 10

- **WHEN** a type is created with a non-integer health, or a health below 1 or above 10
- **THEN** creation fails

#### Scenario: Energy must be 1 to 100

- **WHEN** a type is created with a non-integer energy, or an energy below 1 or above 100
- **THEN** creation fails

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
- **THEN** attack is the damage dealt per attack
- **AND** health is the total damage the unit absorbs before being destroyed
- **AND** energy is the resource consumed by both moving and attacking
