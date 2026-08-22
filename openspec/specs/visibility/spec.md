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
- **THEN** cells holding enemy units they have not seen are drawn as empty

### Requirement: Contact Establishes Visibility

The system SHALL record mutual visibility between units that engage each other
in combat.

#### Scenario: Combat reveals both units

- **WHEN** two units attack each other in a contested cell
- **THEN** each unit records the other as seen
- **AND** each unit's owner can subsequently list the other unit

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
player may see, and clients SHALL render that view in preference to the full
board.

#### Scenario: Publishing player views

- **WHEN** the server finishes resolving a turn
- **THEN** it writes a per-player view containing that player's own units and the enemy units they have seen

#### Scenario: Client prefers its published view

- **WHEN** a client has a published view available
- **THEN** it renders and lists units from that view rather than from the full board

### Requirement: Observers See Everything

The system SHALL grant the neutral observer an unrestricted view of the board
and of all units, without belonging to any player.

#### Scenario: Observer listing

- **WHEN** the observer lists units or renders the board
- **THEN** all units are shown regardless of ownership or contact
