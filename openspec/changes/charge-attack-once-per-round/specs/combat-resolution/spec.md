## MODIFIED Requirements

### Requirement: Attacking Costs Energy

The system SHALL charge a unit its attack value in energy once for each round of
a contest in which it attacks, however many opponents it strikes in that round,
and SHALL prevent the unit from attacking when it cannot pay. A round SHALL be
all or nothing: a unit that cannot pay makes no attack at all, so no opponent is
favoured by where it happens to sit in the cell.

#### Scenario: Paying to attack

- **WHEN** a unit attacks
- **THEN** its energy is reduced by its attack value

#### Scenario: Paying once however many opponents there are

- **WHEN** a unit attacks in a round of a contest against two or more opponents
- **THEN** its energy is reduced by its attack value once
- **AND** it deals its attack value in damage to every one of those opponents

#### Scenario: Exhausted unit cannot attack

- **WHEN** a unit's energy is below its attack value
- **THEN** it deals no damage
- **AND** its energy is unchanged

#### Scenario: A round is all or nothing

- **WHEN** a unit that cannot pay for a round contests a cell with two or more opponents
- **THEN** it strikes none of them
- **AND** which opponents it would have struck does not depend on the order the cell holds them in

#### Scenario: Outlasting a crowd

- **WHEN** a unit with energy for N rounds contests a cell against several opponents
- **THEN** it can still attack in N rounds
- **AND** the number of opponents does not shorten how long it can fight
