## MODIFIED Requirements

### Requirement: Player Elimination

The system SHALL treat a player as eliminated once no unit they own could ever
act again. A unit that is on the board, not destroyed, and whose **type was
designed with energy** SHALL keep its owner in the game, whatever it is holding
at this moment: energy regenerates for a unit that takes no action, so a unit
at zero is spent for now rather than finished, and judging a player on it would
decide the game on the timing of a snapshot. A **wall** — a type designed with
no energy — SHALL NOT keep its owner in the game: it can never move, never
strike and never recover, so a player holding nothing but walls holds nothing
that can play.

#### Scenario: The last unit is destroyed

- **WHEN** a turn is resolved in which a player's last undestroyed unit is destroyed
- **THEN** that player is eliminated

#### Scenario: A unit below its attack value keeps its owner in the game

- **WHEN** a player's only remaining unit has less energy than its attack value
- **THEN** that player is not eliminated
- **AND** the game continues

#### Scenario: A spent unit keeps its owner in the game

- **WHEN** a turn is resolved after which a player's only remaining unit is at zero energy
- **THEN** that player is not eliminated, because that unit will recover by resting
- **AND** the game continues

#### Scenario: A player left holding only walls

- **WHEN** a turn is resolved after which every unit a player owns is destroyed or is a wall
- **THEN** that player is eliminated
- **AND** their walls stay on the board, holding their squares

#### Scenario: A player who never deployed a unit

- **WHEN** the first turn with units on the board is resolved and a registered player holds none of them
- **THEN** that player is eliminated

#### Scenario: Elimination is not reversible

- **WHEN** a later turn is resolved after a player has been eliminated
- **THEN** that player remains eliminated
- **AND** no unit is created for them
