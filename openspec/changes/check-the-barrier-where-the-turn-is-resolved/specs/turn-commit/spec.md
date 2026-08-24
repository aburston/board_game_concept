## MODIFIED Requirements

### Requirement: Commit Barrier

The system SHALL apply a turn only once every player still in the game has
committed, holding the turn open until then. A player who has been eliminated
SHALL NOT be waited for.

A turn SHALL be resolved while the game is held for writing, so that resolving
it cannot overlap another caller committing, resolving, or reading. Holding the
turn open SHALL NOT hold the game: a barrier waits for as long as a player takes
to decide, and a game held across that would be stopped rather than protected.

Whether the barrier is met SHALL be asked where the turn is resolved, while the
game is held, and about the game as it is then — not about the game as a caller
last read it. A turn SHALL NOT be resolved on a barrier that was met before the
game was held. Waiting to be told the barrier is met is a hint to ask again, not
an answer to act on.

Finding the barrier unmet when it is asked SHALL NOT be an error: it means
another caller resolved the turn first, which is the barrier doing its work. The
caller SHALL be told the turn was not resolved, distinguishably from being told
it could not be, and SHALL be free to wait and ask again.

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

#### Scenario: The barrier is asked where the turn is resolved

- **WHEN** a turn is resolved
- **THEN** whether every player still in the game has committed was asked while the game was held
- **AND** about the game as it was then

#### Scenario: A turn is not resolved twice on one barrier

- **WHEN** two callers each find the barrier met and each ask for the turn to be resolved
- **THEN** one of them resolves it
- **AND** the other is told the barrier is no longer met
- **AND** the turn is resolved once

#### Scenario: An unmet barrier is not a failure

- **WHEN** a caller asks for the turn to be resolved and the barrier is not met
- **THEN** it is told the turn was not resolved
- **AND** that is distinguishable from being told the turn could not be resolved
- **AND** the game is unchanged

