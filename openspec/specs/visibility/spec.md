# visibility Specification

## Purpose

Players do not see the whole board. A player always sees their own units, and
sees an enemy unit only once their forces have made contact with it. Visibility
is recomputed every turn, so intelligence gathered by contact is current rather
than cumulative.

## Requirements

### Requirement: Players Always See Their Own Units

The system SHALL show a player every unit they own, wherever it stands.

#### Scenario: Listing own units

- **WHEN** a player lists units
- **THEN** all of that player's units are included

#### Scenario: Rendering own units

- **WHEN** a player renders the board
- **THEN** their own units are drawn with their symbols

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
### Requirement: Contact Establishes Visibility

The system SHALL record mutual visibility between units that engage each other
in combat. A unit SHALL be recorded as seen at most once by any one unit,
however many attacks the two exchange while resolving the turn.

#### Scenario: Combat reveals both units

- **WHEN** two units attack each other in a contested square
- **THEN** each unit records the other as seen
- **AND** each unit's owner can subsequently list the other unit

#### Scenario: A drawn-out fight reveals each unit once

- **WHEN** two units exchange attacks over several rounds in one turn
- **THEN** each unit records the other as seen exactly once

### Requirement: Visibility Is Recomputed Each Turn

The system SHALL clear all recorded contacts at the start of each turn
resolution, so that visibility reflects only contact made in the current turn.

#### Scenario: Contacts cleared before resolution

- **WHEN** a turn begins resolving
- **THEN** every unit's record of units it has seen is cleared before movement and combat run

#### Scenario: Enemy lost after disengaging

- **WHEN** a player saw an enemy unit last turn and made no contact with it this turn
- **THEN** that enemy unit is no longer listed for that player

### Requirement: Per-Player Board Views Are Published

The system SHALL write each player a view of the board limited to what that
player may see, and a client SHALL render and list from that view alone, rather
than in preference to a fuller board it also holds. A view SHALL name each unit
it reveals once, however many of that player's units made contact with it, and
SHALL name the turn it describes.

#### Scenario: Publishing player views

- **WHEN** the server finishes resolving a turn
- **THEN** it writes a per-player view containing that player's own units and the enemy units they have seen
- **AND** the view names the turn number it describes

#### Scenario: Client prefers its published view

- **WHEN** a client has a published view available
- **THEN** it renders and lists units from that view
- **AND** it holds no fuller board to render from instead

#### Scenario: A client with no view yet

- **WHEN** a client loads a game for which no view has been published
- **THEN** it shows only the units that player has deployed this session

#### Scenario: An enemy engaged by several units is named once

- **WHEN** more than one of a player's units engages the same enemy unit in a turn
- **THEN** the player's view names that enemy unit once
- **AND** the client reading that view reports it as a single unit

### Requirement: Observers See Everything

The system SHALL grant the neutral observer an unrestricted view of the board
and of all units, without belonging to any player.

#### Scenario: Observer listing

- **WHEN** the observer lists units or renders the board
- **THEN** all units are shown regardless of ownership or contact

### Requirement: A Session Is Given Only What It May See

The system SHALL give a player's session only the state that player is entitled
to see. A player's session SHALL NOT hold, read, or be able to derive the
position, statistics or existence of any unit that player has not seen, and
SHALL NOT read the authoritative record of the whole board. Hiding a unit at the
point it is displayed is not sufficient.

#### Scenario: A client does not read the shared board

- **WHEN** a client loads a game
- **THEN** it builds its board from that player's own published view
- **AND** it does not read the authoritative record of all units

#### Scenario: An unseen enemy is not in the session at all

- **WHEN** a player's session is loaded and an enemy unit has not been seen by any of their units
- **THEN** the session holds no record of that unit, its square, or its statistics

#### Scenario: The observer is unaffected

- **WHEN** the observer loads a game
- **THEN** it reads the authoritative record and sees every unit

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
### Requirement: A Design Once Met Is Remembered

The system SHALL keep, for each player, every enemy type that player has met,
with the statistics its owner designed it with and the turn it was first met
on, and SHALL keep it after contact with that type is lost.

What is kept SHALL be the design and nothing else. It SHALL NOT record where
any unit was, which units were met, or how many there were: a memory of a
design is not a memory of a position, and only the first is a player's to
keep.

A player who has fought a design and cannot afterwards say what it was built
with is being asked to keep notes on paper, which is not a rule of the game.

#### Scenario: A type met stays known

- **WHEN** a player has met an enemy type and later makes no contact with it
- **THEN** that type is still among the types they have met
- **AND** it reads with the statistics its owner designed it with

#### Scenario: A type never met is not known

- **WHEN** a player has made no contact with any unit of an enemy type
- **THEN** that type is not among the types they have met

#### Scenario: What is remembered says nothing about position

- **WHEN** a player reads the types they have met
- **THEN** no square, no unit name and no number of units is given

#### Scenario: A session entitled to the whole game

- **WHEN** the observer reads the types it has met
- **THEN** every type in the game is given, having been seen by definition

### Requirement: Destroyed Units Are A Marked Casualty Record

The system SHALL continue to show a player their own destroyed units, marked as
destroyed and off the board, so that they can see what they have lost. An enemy
unit destroyed in a turn in which the player made contact with it SHALL appear
in that player's view for that turn only, marked the same way. A destroyed unit
SHALL NOT be drawn on any square.

#### Scenario: A player's own casualties

- **WHEN** a player lists units after one of theirs has been destroyed
- **THEN** that unit is listed, marked destroyed and off the board

#### Scenario: Casualties are not drawn

- **WHEN** a player renders the board
- **THEN** no destroyed unit is drawn on any square

#### Scenario: An enemy destroyed in contact

- **WHEN** a player's unit destroys an enemy unit in a turn
- **THEN** that enemy unit appears in the player's view for that turn, marked destroyed

#### Scenario: An enemy casualty drops out next turn

- **WHEN** a further turn is resolved in which the player made no contact with that enemy
- **THEN** the destroyed enemy unit is no longer listed for them
