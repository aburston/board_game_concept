# Spec Delta

## MODIFIED Requirements

### Requirement: A Player Is Registered With A Point Budget

The system SHALL give every player a point budget when they are registered,
and SHALL fix it for the life of the game. The budget SHALL be an integer from
1 to 1000. Where the administrator does not name one, the budget SHALL be 320.

The default is 320 because a player is given a default army that costs 304,
and a budget that only just covers it would leave nothing to edit with: every
change would have to begin by taking something back.

The budget SHALL be a property of the player rather than of the game, so two
players of one game may be registered with different budgets. Nothing in play
SHALL change a budget once it is set: there is no command that raises or
lowers it, and resolving a turn does not.

#### Scenario: Registering with the default budget

- **WHEN** a player is registered without a budget being named
- **THEN** that player's budget is 320

#### Scenario: Registering with a budget

- **WHEN** a player is registered with a budget of 150
- **THEN** that player's budget is 150

#### Scenario: Two players with different budgets

- **WHEN** one player is registered with a budget of 60 and another with 200
- **THEN** each holds the budget they were registered with
- **AND** neither budget is affected by the other

#### Scenario: A budget outside the permitted range

- **WHEN** a player is registered with a budget below 1 or above 1000, or with
  a budget that is not an integer
- **THEN** registration fails, naming the permitted range
- **AND** no player is registered

#### Scenario: A budget does not change

- **WHEN** a player's units are deployed, destroyed, or a turn is resolved
- **THEN** that player's budget is the same number it was registered with

### Requirement: A Unit Type Costs The Sum Of Its Statistics

The system SHALL price a unit type at `attack + health + energy + compute`,
taken from the type as it was designed. The cost SHALL be computed rather
than stored, so that a type and its price cannot disagree. A program SHALL
add nothing to the price: what a program costs is paid in energy, by the
meter, as it runs.

A unit's cost SHALL be its type's cost, read from the design the unit was made
from rather than from the values play has worn down. A unit that has lost
health or spent energy SHALL still cost what it cost when it was deployed.

Defining a type SHALL be free. A player may define a type they cannot afford
to deploy; what a budget refuses is the deployment.

#### Scenario: Costing a type

- **WHEN** a type is defined with attack 1, health 10, energy 10 and compute 4
- **THEN** that type costs 25 points

#### Scenario: The cheapest and the dearest type

- **WHEN** a type is defined with attack 1, health 1, energy 1 and compute 0
- **THEN** it costs 3 points
- **WHEN** a type is defined with attack 10, health 10, energy 100 and compute 10
- **THEN** it costs 130 points

#### Scenario: A program is free to define

- **WHEN** two types are defined with the same four statistics, one with a long program and one with none
- **THEN** they cost the same

#### Scenario: A worn unit costs what its type cost

- **WHEN** a unit deployed from a type costing 25 has lost health and spent
  energy in combat and in thinking
- **THEN** the unit still costs 25 points

#### Scenario: Defining a type is free

- **WHEN** a player defines a type costing more than their whole budget
- **THEN** the type is defined
- **AND** nothing is spent
- **AND** deploying a unit of that type is refused
