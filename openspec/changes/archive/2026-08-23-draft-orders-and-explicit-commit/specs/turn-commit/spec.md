## ADDED Requirements

### Requirement: Drafting Before Committing

The system SHALL record what a session has done since its last commit as it is
done, rather than holding it only for the life of the session. Everything a
caller may do to a game before committing SHALL be drafted: unit types defined,
units deployed, movement ordered, and the administrator's setup of the board and
its players.

A draft SHALL be restored when its owner reopens the game, so that work is not
lost when a session ends before it commits.

A draft SHALL be private to the session that made it. No other player, the
administrator, and no observer SHALL be able to read it. A drafted order is not
a published one, and knowing that an opponent is deliberating — or what they are
deliberating about — SHALL NOT be obtainable from the game.

A draft SHALL record the turn it was made for. A draft made for any turn other
than the game's current turn SHALL be discarded rather than restored, so that
work left behind by a session that ended while a turn was being resolved is
never applied to a later turn.

Restoring a draft SHALL apply the same rules that applied when each action was
first taken. An action that is no longer legal SHALL be dropped and reported to
its owner, and the rest of the draft SHALL still be restored; a draft SHALL NOT
make a game impossible to open.

#### Scenario: Work is drafted as it is done

- **WHEN** a player defines a type, deploys a unit, or orders a move, and does not commit
- **THEN** the action is recorded against that player
- **AND** it is recorded before the session ends

#### Scenario: A session that ends before committing

- **WHEN** a player defines types and deploys units, the session ends without committing, and the player reopens the game
- **THEN** the types they defined are theirs again
- **AND** the units they deployed are where they placed them
- **AND** they may continue from where they stopped

#### Scenario: A draft is not visible to anyone else

- **WHEN** a player has drafted orders and has not committed
- **THEN** no other player is shown them
- **AND** the administrator is not shown them
- **AND** an observer is not shown them
- **AND** nothing reveals that the player has drafted anything at all

#### Scenario: A draft from an earlier turn

- **WHEN** a game is opened holding a draft recorded for a turn earlier than the game's current turn
- **THEN** the draft is discarded
- **AND** none of its actions are applied
- **AND** the game opens normally

#### Scenario: A drafted action that is no longer legal

- **WHEN** a draft is restored and one of its actions can no longer be carried out
- **THEN** that action is dropped and reported to its owner
- **AND** every other action in the draft is restored
- **AND** the game opens

#### Scenario: Drafting is not permitted while awaiting resolution

- **WHEN** a player has committed and the turn has not yet been resolved
- **THEN** no further action is drafted for them
- **AND** the client reports that it is waiting for the turn to complete

#### Scenario: Committing consumes the draft

- **WHEN** a player commits
- **THEN** their draft is discarded, having become their committed orders
- **AND** reopening the game restores no draft for them

## MODIFIED Requirements

### Requirement: Commits Are Final

The system SHALL treat a commit as irreversible; a player cannot withdraw or
amend orders once committed. A player MAY amend their draft freely up to the
moment they commit, and SHALL NOT be able to amend it afterwards. There SHALL
be no way to withdraw a commit: a player who has committed is committed for
that turn, whatever any other player does next.

#### Scenario: Committing orders

- **WHEN** a player commits
- **THEN** their orders are written for the server to consume
- **AND** the player cannot undo them

#### Scenario: Amending before committing

- **WHEN** a player orders a unit to move and then orders the same unit to move elsewhere, before committing
- **THEN** the later order stands
- **AND** the earlier one has no effect on the turn

#### Scenario: A commit cannot be withdrawn

- **WHEN** a player has committed and the turn has not yet been resolved
- **THEN** there is no command or request that withdraws their commit
- **AND** the turn is still resolved with the orders they committed
