## MODIFIED Requirements

### Requirement: Contact Establishes Visibility

The system SHALL record mutual visibility between units that engage each other
in combat. A unit SHALL be recorded as seen at most once by any one unit,
however many attacks the two exchange while resolving the turn.

#### Scenario: Combat reveals both units

- **WHEN** two units attack each other in a contested cell
- **THEN** each unit records the other as seen
- **AND** each unit's owner can subsequently list the other unit

#### Scenario: A drawn-out fight reveals each unit once

- **WHEN** two units exchange attacks over several rounds in one turn
- **THEN** each unit records the other as seen exactly once

### Requirement: Per-Player Board Views Are Published

The system SHALL write each player a view of the board limited to what that
player may see, and clients SHALL render that view in preference to the full
board. A view SHALL name each unit it reveals once, however many of that
player's units made contact with it.

#### Scenario: Publishing player views

- **WHEN** the server finishes resolving a turn
- **THEN** it writes a per-player view containing that player's own units and the enemy units they have seen

#### Scenario: Client prefers its published view

- **WHEN** a client has a published view available
- **THEN** it renders and lists units from that view rather than from the full board

#### Scenario: An enemy engaged by several units is named once

- **WHEN** more than one of a player's units engages the same enemy unit in a turn
- **THEN** the player's view names that enemy unit once
- **AND** the client reading that view reports it as a single unit
