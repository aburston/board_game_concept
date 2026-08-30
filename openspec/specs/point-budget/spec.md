# point-budget Specification

## Purpose

The currency an army is bought with.

Nothing bounded an army before this: a player defined types during setup and
deployed as many units of them as there were free squares, so the player who
typed fastest won before a turn was resolved. Designing well cost nothing
either - `attack 10 health 10 energy 100` was strictly better than anything
cheaper and cost the same, which is to say nothing, so there was exactly one
type worth defining and every game converged on it.

The three statistics are meant to be a trade - a fast cheap scout against a
slow expensive brawler - and a trade needs a currency. Each player is given a
pool of points when they are registered, a type costs the sum of its
statistics, deploying spends that cost out of the pool, and a deployment the
pool cannot pay for is refused. The interesting decision - many cheap units or
few strong ones - becomes the decision setup is about.

## Requirements

### Requirement: A Player Is Registered With A Point Budget

The system SHALL give every player a point budget when they are registered,
and SHALL fix it for the life of the game. The budget SHALL be an integer from
1 to 1000. Where the administrator does not name one, the budget SHALL be 250.

The default is 250 because a player is given a default army that costs 232,
and a budget that only just covers it would leave nothing to edit with: every
change would have to begin by taking something back.

The budget SHALL be a property of the player rather than of the game, so two
players of one game may be registered with different budgets. Nothing in play
SHALL change a budget once it is set: there is no command that raises or
lowers it, and resolving a turn does not.

#### Scenario: Registering with the default budget

- **WHEN** a player is registered without a budget being named
- **THEN** that player's budget is 250

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

The system SHALL price a unit type at `attack + health + energy`, taken from
the type as it was designed. The cost SHALL be computed rather than stored, so
that a type and its price cannot disagree.

A unit's cost SHALL be its type's cost, read from the design the unit was made
from rather than from the values play has worn down. A unit that has lost
health or spent energy SHALL still cost what it cost when it was deployed.

Defining a type SHALL be free. A player may define a type they cannot afford
to deploy; what a budget refuses is the deployment.

#### Scenario: Costing a type

- **WHEN** a type is defined with attack 1, health 10 and energy 10
- **THEN** that type costs 21 points

#### Scenario: The cheapest and the dearest type

- **WHEN** a type is defined with attack 1, health 1 and energy 1
- **THEN** it costs 3 points
- **WHEN** a type is defined with attack 10, health 10 and energy 100
- **THEN** it costs 120 points

#### Scenario: A worn unit costs what its type cost

- **WHEN** a unit deployed from a type costing 21 has lost health and spent
  energy in combat
- **THEN** the unit still costs 21 points

#### Scenario: Defining a type is free

- **WHEN** a player defines a type costing more than their whole budget
- **THEN** the type is defined
- **AND** nothing is spent
- **AND** deploying a unit of that type is refused

### Requirement: What A Player Has Spent Is Derived From The Board

The system SHALL compute what a player has spent as the sum of the costs of
every unit the board holds for that player, and SHALL NOT keep a running
total. What is left SHALL be the budget less that sum.

A destroyed unit SHALL still count as spent. There is no refund: points buy a
unit, not the time it survives for.

#### Scenario: Spend is the sum of what is deployed

- **WHEN** a player with a budget of 100 has deployed three units of a type
  costing 21
- **THEN** they have spent 63 points
- **AND** they have 37 points left

#### Scenario: A player who has deployed nothing

- **WHEN** a player has deployed no units
- **THEN** they have spent 0 points
- **AND** they have their whole budget left

#### Scenario: A destroyed unit is not refunded

- **WHEN** one of a player's deployed units is destroyed
- **THEN** that player's spend is unchanged
- **AND** what they have left is unchanged

#### Scenario: Spend follows the board

- **WHEN** a game is saved and opened again
- **THEN** each player's spend is the same number it was, derived from the
  units the board was restored with

### Requirement: A Deployment Is Refused When The Budget Cannot Pay

The system SHALL refuse to deploy a unit whose type costs more than the
deploying player has left, and SHALL allow a deployment that spends exactly
what is left. A refusal SHALL name the cost, what the player has left, and the
budget it is left out of, and SHALL leave the game exactly as it was: no unit
is created, nothing is spent, and the session continues.

#### Scenario: A deployment that fits

- **WHEN** a player with 37 points left deploys a unit of a type costing 21
- **THEN** the unit is deployed
- **AND** the player has 16 points left

#### Scenario: A deployment that exactly spends what is left

- **WHEN** a player with 21 points left deploys a unit of a type costing 21
- **THEN** the unit is deployed
- **AND** the player has 0 points left

#### Scenario: A deployment that costs more than is left

- **WHEN** a player with 16 points left deploys a unit of a type costing 21
- **THEN** the deployment is refused, naming the cost, what is left, and the
  budget
- **AND** no unit is created
- **AND** the player still has 16 points left

#### Scenario: A spent budget refuses every further deployment

- **WHEN** a player has 0 points left
- **THEN** every deployment is refused, whatever type it names
- **AND** the player may still order the units they already hold

### Requirement: The Turn Resolution Enforces The Budget

The system SHALL apply the budget again when a turn is resolved, so that a
deployment reaching the board by any route is paid for. A published
deployment its owner cannot afford SHALL be refused through the same channel
as any other refused order — reported to that player as a rejected order, with
the reason naming the cost and what was left — and SHALL NOT be placed on the
board. The rest of that player's orders SHALL still be carried out.

#### Scenario: A deployment the player cannot afford is rejected

- **WHEN** an order deploying a unit costing more than its owner has left is
  published
- **THEN** the turn resolves without that unit reaching the board
- **AND** the order is reported to its owner as rejected, naming the cost and
  what was left

#### Scenario: The player's other orders still stand

- **WHEN** one of a player's published orders is rejected for cost
- **THEN** every other order that player published is carried out as usual

#### Scenario: A loaded player file with more units than the budget buys

- **WHEN** a player file is loaded whose units cost more in total than that
  player's budget
- **THEN** the units the budget can pay for are deployed
- **AND** the rest are rejected, each naming the cost and what was left

### Requirement: Deployments Are Charged In A Settled Order

Where a player publishes more deployments in one turn than the budget can pay
for, the system SHALL charge them in order of unit name, and SHALL refuse
those the budget can no longer pay for. Which deployments survive SHALL be
decidable from the board and the orders alone, and SHALL NOT depend on the
order a file or a list happened to hold them in.

#### Scenario: Charging order is by unit name

- **WHEN** a player with 50 points left publishes deployments of units named
  `beta` and `alpha`, each costing 30, in that order
- **THEN** `alpha` is deployed and `beta` is rejected
- **AND** reversing the order the two were published in resolves the same way

#### Scenario: The same orders resolve the same way

- **WHEN** the same set of over-budget deployments is resolved twice against
  the same board
- **THEN** the same deployments are placed and the same ones are rejected

### Requirement: A Budget Is Known Only Where The Record Is Read

The system SHALL let a session know a player's budget, spend and remaining
points only where that session is entitled to read that player's record: its
own, and every player's for the administrator and the observer. Where a
session is not entitled, the three numbers SHALL be unknown rather than
guessed at or defaulted.

#### Scenario: A player knows their own numbers

- **WHEN** a player asks what they have left
- **THEN** their budget, spend and remaining points are reported

#### Scenario: A player does not learn another player's numbers

- **WHEN** a player asks about the registered players
- **THEN** another player's budget, spend and remaining points are unknown

#### Scenario: The administrator and the observer know every player's numbers

- **WHEN** the administrator or the observer asks about the registered players
- **THEN** every player's budget, spend and remaining points are reported
