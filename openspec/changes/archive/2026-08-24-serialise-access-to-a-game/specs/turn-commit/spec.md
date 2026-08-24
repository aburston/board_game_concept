## MODIFIED Requirements

### Requirement: Commit Barrier

The system SHALL apply a turn only once every player still in the game has
committed, holding the turn open until then. A player who has been eliminated
SHALL NOT be waited for.

A turn SHALL be resolved while the game is held for writing, so that resolving
it cannot overlap another caller committing, resolving, or reading. Holding the
turn open SHALL NOT hold the game: a barrier waits for as long as a player takes
to decide, and a game held across that would be stopped rather than protected.

#### Scenario: Waiting for all players

- **WHEN** some but not all players still in the game have committed their orders
- **THEN** the server waits and does not resolve the turn

#### Scenario: All players committed

- **WHEN** every player still in the game has committed
- **THEN** the server resolves the turn and applies all orders together

#### Scenario: Resolving a turn excludes everything else

- **WHEN** a turn is being resolved
- **THEN** no other caller may commit, resolve, or read that game until it is finished

#### Scenario: Waiting for players does not exclude them

- **WHEN** the server is holding a turn open for players who have not committed
- **THEN** those players may commit
- **AND** anyone may read the game

#### Scenario: An eliminated player is not waited for

- **WHEN** every player still in the game has committed and an eliminated player has not
- **THEN** the server resolves the turn without waiting for them

#### Scenario: The last player standing

- **WHEN** every player but one has been eliminated
- **THEN** the game is decided rather than the turn being held open for the eliminated players
