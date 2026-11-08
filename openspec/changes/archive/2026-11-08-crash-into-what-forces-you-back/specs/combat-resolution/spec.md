## MODIFIED Requirements

### Requirement: Square Ownership After Combat

The system SHALL leave the surviving unit in sole possession of the contested
square when the contest is decided, SHALL empty the square when no unit
survives, and SHALL return every survivor that moved into the square to the
square it came from when the contest is undecided.

No square SHALL hold more than one unit once a turn is resolved.

A survivor that cannot return to the square it left, because another unit
moved into that square during the same turn, SHALL crash into that unit: one
exchange on the ordinary terms, simultaneous, so a unit that is hit hits back
even when the blow destroys it. Where both survive the crash, the unit in the
way SHALL give ground and fall back in its turn, crashing into whoever is
behind it, for as long as the column runs.

Being forced back SHALL cost nothing. The fare paid for the move that was
ordered covers being put back out of it, and a unit SHALL NOT be charged
energy for a blow it lands in the pile-up. It SHALL still have to be able to
strike to land one.

#### Scenario: One survivor

- **WHEN** combat leaves exactly one undestroyed unit in a square
- **THEN** that unit alone occupies the square

#### Scenario: No survivors

- **WHEN** combat destroys every unit contesting a square
- **THEN** the square becomes empty

#### Scenario: Undecided contest between units that all moved in

- **WHEN** combat ends undecided and every survivor moved into the square this turn
- **THEN** each survivor is returned to the square it came from
- **AND** no survivor is destroyed
- **AND** the contested square is left empty

#### Scenario: Undecided contest against a unit that held the square

- **WHEN** combat ends undecided between a unit that moved in and a unit already holding the square
- **THEN** the unit that moved in is returned to the square it came from
- **AND** the unit that held the square keeps it

#### Scenario: Survivor with nowhere to fall back

- **WHEN** combat ends undecided and a survivor cannot return to the square it
  left, because another unit moved into that square during the same turn
- **THEN** the two crash, each striking the other once
- **AND** where both survive, the unit in the way falls back in its turn

#### Scenario: A column that walks into what it cannot shift

- **WHEN** a column of units is ordered forward and the leading unit's contest
  ends undecided
- **THEN** each unit crashes into the one behind it, down the column
- **AND** every unit ends the turn on the square it started it on
- **AND** no square holds more than one unit

#### Scenario: A unit damaged twice in one turn

- **WHEN** a unit is struck by what it moved into and then crashes into the
  unit that took the square behind it
- **THEN** it takes damage from both

#### Scenario: Being forced back costs nothing

- **WHEN** a unit is forced back and crashes into the unit behind it
- **THEN** it pays no energy for that blow
- **AND** the unit it crashes into pays nothing for its own

#### Scenario: A unit too spent to fight lands nothing, paid for or not

- **WHEN** a unit with less energy than its attack is crashed into
- **THEN** it lands no blow

#### Scenario: A crash that clears the way

- **WHEN** a unit falling back destroys the unit in its way
- **THEN** it takes that square

### Requirement: Simultaneous Damage Application

The system SHALL apply all damage from one exchange simultaneously, so that a
unit destroyed in an exchange still lands the blow it paid for.

A unit SHALL strike each other unit at most once in a turn, however many
exchanges that turn holds. A unit with no unstruck opponent left in a square
SHALL pay nothing and strike nothing.

#### Scenario: Mutual destruction

- **WHEN** two units in a contest each land a blow that destroys the other
- **THEN** both are destroyed

#### Scenario: The same opponent met twice in one turn

- **WHEN** a unit contests a square with an opponent and then crashes into the
  same opponent while falling back
- **THEN** it strikes that opponent once, not twice

#### Scenario: Nothing left to strike

- **WHEN** every unit in a square has already been struck by this unit this turn
- **THEN** it lands no blow and pays no energy for one
