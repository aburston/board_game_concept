## ADDED Requirements

### Requirement: Energy Regeneration

The system SHALL give back `REST_GAIN` energy, at the end of each turn, to
every unit on the board that took no action during it — one that was given no
order **and** paid for nothing while the turn resolved. A unit SHALL NOT
recover past the energy its type was designed with, and a destroyed unit SHALL
recover nothing. Regeneration SHALL happen after combat and before elimination
is judged, so that a player whose units are merely out of energy is judged on
what they will hold rather than on what they hold mid-turn.

Both halves of "took no action" are required. A unit ordered to move has acted
whether or not the move was carried out: one ordered off the board pays nothing
and still does not rest, so ordering a unit into the edge every turn is not a
way to refuel. A unit that was attacked and could not afford to strike back has
done nothing at all, and does rest — being attacked is not an action.

#### Scenario: A unit that was given no order

- **WHEN** a turn resolves in which a unit was given no order and paid for nothing
- **THEN** that unit's energy is one higher than it was, up to the energy its type was designed with

#### Scenario: A unit already at the energy it was designed with

- **WHEN** a turn resolves in which such a unit took no action
- **THEN** its energy is unchanged

#### Scenario: A unit that was ordered to move

- **WHEN** a turn resolves in which a unit was ordered to move
- **THEN** that unit does not recover energy, whether or not the move was carried out

#### Scenario: A unit ordered off the board

- **WHEN** a turn resolves in which a unit was ordered off the board, which costs it nothing
- **THEN** that unit does not recover energy

#### Scenario: A unit that was attacked but could not pay to fight back

- **WHEN** a turn resolves in which a unit was attacked and could not afford to attack
- **THEN** that unit recovers energy

#### Scenario: A destroyed unit

- **WHEN** a turn resolves in which a unit is destroyed
- **THEN** it recovers nothing
