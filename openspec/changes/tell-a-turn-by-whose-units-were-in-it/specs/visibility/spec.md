## MODIFIED Requirements

### Requirement: An Account Of A Turn Is Bounded By Whose Units Were In It

The system SHALL tell a seat what a turn did to and by its own units, and
SHALL NOT tell it what other players' units did to each other. An entry SHALL
reach a seat only where one of that seat's own units was in it.

Every entry that names a unit SHALL say which players' units it names, and
whether an entry reaches a seat SHALL be decided from that. It SHALL NOT be
decided by matching the names a seat owns against the names an entry mentions:
a name has only to be unique within one player's own units, so two players who
chose the same name would each read the other's entries about it.

An account of a turn is a way of learning where somebody is, and what two
other players did to each other is theirs. Being able to see both of them is
not being in the fight: a seat standing beside a contest it took no part in
used to read every blow struck in it.

An entry that names no unit — a square being contested, emptied or shared —
SHALL reach a seat only where that seat was already told about something else
at the same square, so it reads as context for a fight the seat was in.

What a square **came to** SHALL be told the same way rather than by who it
names: a unit being destroyed or taken off the board reaches everyone who was
in that fight. A unit falling in front of you is not something that can be
kept from you, and `destroyed` names only the unit that fell — so the rule
above would otherwise withhold from a player the kill they had just made.

#### Scenario: My own unit

- **WHEN** a seat's unit strikes, is struck, moves or is destroyed
- **THEN** that seat is told, and told which unit did it

#### Scenario: Two players who chose the same unit name

- **WHEN** two players each hold a unit called `scout` and one of them is
  placed, moved or struck
- **THEN** only that unit's own player is told of it
- **AND** the other is told nothing, though the name is one they hold too

#### Scenario: A fight between units of the same name

- **WHEN** two players' units, both called `scout`, fight each other
- **THEN** each player is told what its own unit struck and what struck it
- **AND** neither is told anything the other's unit did to a third player

#### Scenario: Two enemies fighting in sight

- **WHEN** two other players' units fight and this seat can see both
- **THEN** this seat is told nothing of what they did to each other

#### Scenario: Two enemies fighting out of sight

- **WHEN** two other players' units fight and this seat can see neither
- **THEN** this seat is told nothing of it, including that a square was
  contested

#### Scenario: Half a fight

- **WHEN** two other players' units fight and this seat can see only one of them
- **THEN** this seat is told nothing of it

#### Scenario: A fight this seat is in with two others

- **WHEN** three players contest one square and this seat is one of them
- **THEN** this seat is told what its own unit struck and what struck it
- **AND** is not told what the other two did to each other
- **AND** is told the square was contested, because it was in it

#### Scenario: A kill the seat made

- **WHEN** a seat's unit destroys another player's unit
- **THEN** that seat is told the unit was destroyed, though the entry names
  only the unit that fell

#### Scenario: A kill in a fight the seat was not in

- **WHEN** a unit is destroyed in a fight this seat had no unit in
- **THEN** this seat is told nothing of it

#### Scenario: The observer

- **WHEN** the observer reads what a turn did
- **THEN** it is told all of it
