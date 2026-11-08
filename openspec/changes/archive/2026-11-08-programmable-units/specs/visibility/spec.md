# Spec Delta

## ADDED Requirements

### Requirement: An Army Remembers Where It Has Been And What It Met

The system SHALL keep for each player, beside the view it publishes, a map of
the board as that player's army knows it, as `unit-program` describes, and
SHALL give it to the player's controllers and to nobody else's. The map SHALL
disclose nothing a contact did not disclose at the time: what it adds is
memory, stamped with the turn.

#### Scenario: What the map holds

- **WHEN** a player's map is read
- **THEN** it holds the squares friendly units have stood on and when, the enemies they have fought with where and when and the design contact revealed, and every standing flag

#### Scenario: The map is the army's

- **WHEN** a player's unit fights an enemy on a square
- **THEN** that player's map holds that enemy, its design and the turn, on that square, from the next turn
- **AND** no other player's map does

#### Scenario: The map outlives contact

- **WHEN** a player's units lose contact with an enemy
- **THEN** the published view no longer lists it
- **AND** the player's map still holds where and when it was last met

#### Scenario: The map is not shown to another seat

- **WHEN** another seat, or an enemy controller, reads anything the game offers
- **THEN** nothing of this player's map is in it

### Requirement: Programs Are Never Disclosed

The system SHALL never show a type's program, its compute or its units'
controller traces to any seat but its owner. Contact SHALL disclose a type's
attack, health and energy as it does today, and nothing of how its units
think. The observer MAY read every seat's traces and programs, as it reads
everything.

#### Scenario: The type of an enemy just fought

- **WHEN** a player's unit fights an enemy and its type is disclosed
- **THEN** the disclosure holds its attack, health and energy
- **AND** neither its compute nor its program

#### Scenario: The replay withholds the other seat's thinking

- **WHEN** a seat reads any turn of the record
- **THEN** it reads no other seat's traces, programs or compute

### Requirement: The Replay Shows The Whole Board Once The Game Is Resolved

The system SHALL show every seat, once the game has been resolved to its end,
the whole board at every turn of the record - every unit of every player as
the observer sees them - because nothing a finished game shows can be used
against anyone. A seat SHALL also be able to read, for any turn, the board as
its own army knew it at that turn, so that a player can see what their
programs saw.

#### Scenario: A seat replays a finished game

- **WHEN** a player reads turn 12 of a finished game's record
- **THEN** every unit on the board after turn 12 is shown, whichever player it belongs to

#### Scenario: What my army knew

- **WHEN** a player asks for turn 12 as their army knew it
- **THEN** they are shown their map as it stood when turn 12 was resolved: known squares, remembered enemies with their stamps, friends and flags, and nothing else

## MODIFIED Requirements

### Requirement: A Design Once Met Is Remembered

The system SHALL keep, for each player, every enemy type that player has met,
with the statistics its owner designed it with and the turn it was first met
on, and SHALL keep it after contact with that type is lost.

What is kept here SHALL be the design and nothing else. The published list of
designs met SHALL NOT record where any unit was, which units were met, or how
many there were. Where an enemy was met, and when, is kept on the army's map
for the army's controllers to read, as `An Army Remembers Where It Has Been
And What It Met` states; it is the army's memory of its own contacts rather
than a disclosure.

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
