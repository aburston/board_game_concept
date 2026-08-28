## MODIFIED Requirements

### Requirement: Enemy Units Are Hidden Until Contact

The system SHALL hide enemy units from a player until one of that player's units
has engaged them.

The one exception is a flag: the square a flag carrier stands on, and the
player it belongs to, SHALL be shown to every player without contact, as
`flag-carrier` describes. Nothing else about that unit SHALL be shown - not
its name, its type, its symbol or its statistics - so what is disclosed is
where to go rather than what will be met.

#### Scenario: Unseen enemy is not listed

- **WHEN** a player lists units and no unit of theirs has engaged a given enemy unit
- **THEN** that enemy unit is not included

#### Scenario: Unseen enemy is not drawn

- **WHEN** a player renders the board
- **THEN** squares holding enemy units they have not seen are drawn as empty

#### Scenario: An enemy flag is shown without contact

- **WHEN** a player lists the flags and has engaged nothing
- **THEN** each enemy flag's square and owner are given

#### Scenario: The unit carrying it is still hidden

- **WHEN** a player is shown an enemy flag's square and has not engaged the
  unit carrying it
- **THEN** that unit is not among the units they are shown
- **AND** the square is drawn as holding a flag rather than as holding a unit

### Requirement: Enemy Unit Types Are Disclosed By Contact

The system SHALL disclose an enemy unit type to a player only through contact
with a unit of that type, on the same terms as the unit itself. A player SHALL
NOT be shown the types another player has defined merely because that player is
registered in the game.

#### Scenario: Types of an enemy never met

- **WHEN** a player lists unit types and none of their units has made contact with an enemy
- **THEN** only their own types are listed

#### Scenario: The type of an enemy just fought

- **WHEN** a player's unit exchanges attacks with an enemy unit in a turn
- **THEN** that enemy unit's type is listed for that player
- **AND** it is listed with the statistics its owner designed it with, rather than with the state the unit happened to be in when it was met

#### Scenario: The type of an enemy no longer in contact

- **WHEN** a player made no contact with any unit of an enemy type this turn
- **THEN** that type is no longer listed among the types they are in contact
  with
- **AND** it remains among the types they have met, as `A Design Once Met Is
  Remembered` describes

#### Scenario: A flag discloses no type

- **WHEN** a player is shown the square an enemy flag is on
- **THEN** the type of the unit carrying it is not listed for them
