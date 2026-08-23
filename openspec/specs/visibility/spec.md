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

#### Scenario: Unseen enemy is not listed

- **WHEN** a player lists units and no unit of theirs has engaged a given enemy unit
- **THEN** that enemy unit is not included

#### Scenario: Unseen enemy is not drawn

- **WHEN** a player renders the board
- **THEN** squares holding enemy units they have not seen are drawn as empty

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
- **THEN** that type is no longer listed for them

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
