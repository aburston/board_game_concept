## MODIFIED Requirements

### Requirement: Energy Regeneration

The system SHALL give back `REST_GAIN` energy, which SHALL be 2, at the end
of each turn, to every unit standing on the board, whatever it did during
the turn: a unit that moved, struck, was struck, thought, was charged by its
meter, slept or stood still all recover alike. A unit SHALL NOT recover past
the energy its type was designed with, so a type designed with no energy
recovers nothing, and a destroyed unit SHALL recover nothing. Regeneration
SHALL happen after combat and before elimination is judged, so that a player
whose units are merely out of energy is judged on what they will hold rather
than on what they hold mid-turn. The turn's account SHALL report a unit as
rested only where its energy rose.

#### Scenario: A unit that was given no order

- **WHEN** a turn resolves in which a unit was given no order and paid for nothing
- **THEN** that unit's energy is two higher than it was, up to the energy its type was designed with

#### Scenario: A unit already at the energy it was designed with

- **WHEN** a turn resolves in which such a unit took no action
- **THEN** its energy is unchanged
- **AND** the turn's account does not say it rested

#### Scenario: A unit one short of the energy it was designed with

- **WHEN** a turn resolves in which such a unit did nothing
- **THEN** its energy is the energy its type was designed with, not one more

#### Scenario: A unit that was ordered to move

- **WHEN** a turn resolves in which a unit's controller ordered it to move and the move was carried out
- **THEN** that unit's energy is the fare lower and two higher than it was, within the energy its type was designed with

#### Scenario: A unit ordered off the board

- **WHEN** a turn resolves in which a unit's controller ordered it off the board, which costs it nothing
- **THEN** that unit recovers two energy like any other

#### Scenario: A unit that fought

- **WHEN** a turn resolves in which a unit struck in a contest
- **THEN** that unit's energy is its attack lower and two higher than it was, within the energy its type was designed with

#### Scenario: A unit whose meter charged

- **WHEN** a turn resolves in which a unit's meter filled and charged 1 energy
- **THEN** that unit recovers two energy like any other

#### Scenario: A sleeping unit

- **WHEN** a turn resolves in which a unit slept
- **THEN** that unit recovers two energy like any other

#### Scenario: A type designed with no energy

- **WHEN** a turn resolves with a Wall standing on the board
- **THEN** its energy is 0, as it was designed

#### Scenario: A destroyed unit

- **WHEN** a turn resolves in which a unit is destroyed
- **THEN** it recovers nothing
