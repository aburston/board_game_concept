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

The system SHALL have every unit in a contested cell attack every other unit in
that cell, with all attacks in a round applying regardless of the damage those
attacks receive in the same round.

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
the unit when its health is exhausted.

#### Scenario: Taking damage

- **WHEN** a unit takes damage
- **THEN** its health is reduced by the attack value

#### Scenario: Health exhausted

- **WHEN** a unit's health reaches zero or below
- **THEN** the unit is marked destroyed

### Requirement: Combat Runs To A Decision

The system SHALL repeat attack rounds in a contested cell until at most one
unit remains undestroyed, resolving the contest within the same turn.

#### Scenario: Attrition over multiple rounds

- **WHEN** an attacker with attack 3 and health 5 engages a defender with attack 2 and health 4
- **THEN** rounds repeat until the defender is destroyed
- **AND** the attacker survives with health 1

#### Scenario: Stronger unit takes the cell

- **WHEN** a unit with attack 4 and health 7 contests a cell with a unit with attack 3 and health 5
- **THEN** the weaker unit is destroyed
- **AND** the stronger unit holds the cell

### Requirement: Cell Ownership After Combat

The system SHALL leave the surviving unit in sole possession of the contested
cell, and SHALL empty the cell when no unit survives.

#### Scenario: One survivor

- **WHEN** combat leaves exactly one undestroyed unit in a cell
- **THEN** that unit alone occupies the cell

#### Scenario: No survivors

- **WHEN** combat destroys every unit contesting a cell
- **THEN** the cell becomes empty

### Requirement: Destroyed Units Leave The Board

The system SHALL remove destroyed units from play, clearing the cell they held
and marking them as no longer on the board.

#### Scenario: Removing a destroyed unit

- **WHEN** a unit is destroyed
- **THEN** it is marked as not on the board
- **AND** it no longer occupies a cell
- **AND** it is not considered for movement or combat in later turns
