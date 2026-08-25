## ADDED Requirements

### Requirement: A Turn Is Resolved From The Whole Game

The system SHALL resolve a turn only from a session entitled to the whole game,
whatever transport carried the commit that closed the barrier. A player's
session is built from that player's own published view and is given no other
player's orders, so a turn resolved from one would apply half the orders that
were given and publish half the board as the record of the game — every other
player wiped off it and eliminated for having nothing left standing. A session
not entitled to the whole game SHALL be refused, and the turn SHALL be left
unresolved rather than resolved from part of the game.

#### Scenario: A commit that closes the barrier resolves as the administrator

- **WHEN** a player's commit closes the barrier and the turn is resolved during that commit
- **THEN** the turn is resolved from a session entitled to the whole game
- **AND** every player's published orders are applied
- **AND** the record the turn publishes holds every player's units

#### Scenario: A player's session may not resolve a turn

- **WHEN** a session opened as a player asks for a turn to be resolved
- **THEN** it is refused
- **AND** the game is unchanged
- **AND** the turn is still there to be resolved by the administrator

#### Scenario: Committing last does not win the game

- **WHEN** two players have each deployed a unit and commit one after the other
- **THEN** the turn resolves with both players' units on the board
- **AND** neither player is eliminated
- **AND** the game is undecided
