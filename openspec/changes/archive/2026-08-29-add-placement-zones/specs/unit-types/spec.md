## ADDED Requirements

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

## REMOVED Requirements

### Requirement: Walls

**Reason**: A type with no attack is no longer required to have no energy, so
"the two zeroes go together" is no longer the rule. Replaced by "Walls And
Scouts", which keeps every wall behaviour unchanged and adds the scout - no
attack, but energy to move on.

**Migration**: A wall is still attack 0 with energy 0 and behaves exactly as
before. What was refused and is now allowed is attack 0 with energy above 0.
What is still refused is energy 0 with an attack above it, and a type with any
energy must still hold at least its movement cost in it - a rule a scout is
now held to as well.
