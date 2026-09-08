## MODIFIED Requirements

### Requirement: Unit Type Validation

The system SHALL reject unit types whose fields fall outside their permitted
ranges, and SHALL do so at construction time rather than during play. Attack is
an integer from **0 to 10**, health an integer from **1 to 10**, and energy an
integer from **0 to 100**; attack and energy are zero only together, as the
Walls requirement states.

A symbol SHALL be exactly one character and that character SHALL NOT be
whitespace. A blank square is what the board draws where nothing stands, so a
unit drawn with a space would be a unit the board hid. Every other single
printable character is a symbol a player may choose, `#` among them: nothing
about the board's own drawing reserves one.

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
