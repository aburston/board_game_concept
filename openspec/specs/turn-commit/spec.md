# turn-commit Specification

## Purpose

The game advances in simultaneous turns. Players issue orders independently and
commit them; the server waits until every player has committed, then resolves
all orders at once. No player's orders are applied before another's, so no
player gains an advantage from committing early or late.

## Requirements

### Requirement: Two-Phase Turn Resolution

The system SHALL resolve a turn in two phases: a movement phase that decides
every unit's destination from the board as the turn began, applies all those
moves together, and gathers the squares more than one unit finishes in; followed
by a combat phase that resolves those squares. No unit's move SHALL be applied
before another's destination has been decided.

#### Scenario: Resolving a turn

- **WHEN** a turn is resolved
- **THEN** every unit on the board first has its destination decided against the board as the turn began
- **AND** all of those moves are then applied together
- **AND** only then is combat resolved in every contested square

#### Scenario: No unit is left mid-move

- **WHEN** the combat phase begins
- **THEN** no unit remains in the `MOVING` state

#### Scenario: No unit sees another's move before its own is decided

- **WHEN** two units are ordered such that one's destination would differ according to whether the other had already moved
- **THEN** both destinations are decided from the board as the turn began
- **AND** the outcome is the same whichever unit is processed first

### Requirement: Deployment On First Resolution

The system SHALL place newly created units onto the board when the turn is
resolved. Deploying a brand new unit onto a square that is already taken is
illegal: the system SHALL refuse the deployment and SHALL resolve the turn
without it, rather than failing the turn. When two deployments contend for one
square in the same turn, the system SHALL refuse both, so that no player gains
from the order their orders happen to be read in.

#### Scenario: Deploying a new unit

- **WHEN** a turn is resolved and a unit is in the `INITIAL` state
- **THEN** the unit is placed at its assigned coordinates
- **AND** the unit moves to the `NOP` state

#### Scenario: Deploying onto an occupied square

- **WHEN** a unit is deployed at coordinates that already hold a unit
- **THEN** the deployment is refused with an error naming the unit and the square
- **AND** no unit is created
- **AND** the unit already holding the square is unaffected

#### Scenario: Deploying two units onto one square in the same turn

- **WHEN** two units are deployed at the same coordinates before the turn is resolved
- **THEN** both are refused
- **AND** the turn resolves with neither on that square
- **AND** the square is left empty

#### Scenario: Two players deploying onto one square in the same turn

- **WHEN** two players each deploy a unit onto the same square on the same turn, neither able to see the other's units
- **THEN** the server refuses both deployments
- **AND** publishes the rejection to each of them
- **AND** the turn is resolved for every other unit
- **AND** neither player is favoured by their player number or by the order their orders were read

#### Scenario: Deployment is not movement

- **WHEN** a unit already on the board is ordered to move into a square another unit holds
- **THEN** the order is allowed
- **AND** the two units contest the square

### Requirement: Only Units In Play Are Resolved

The system SHALL resolve movement and combat only for units currently on the
board, skipping units that have been destroyed or not yet deployed.

#### Scenario: Skipping units not in play

- **WHEN** a turn is resolved
- **THEN** units not on the board take no action

### Requirement: Commit Barrier

The system SHALL apply a turn only once every player still in the game has
committed, holding the turn open until then. A player who has been eliminated
SHALL NOT be waited for.

#### Scenario: Waiting for all players

- **WHEN** some but not all players still in the game have committed their orders
- **THEN** the server waits and does not resolve the turn

#### Scenario: All players committed

- **WHEN** every player still in the game has committed
- **THEN** the server resolves the turn and applies all orders together

#### Scenario: An eliminated player is not waited for

- **WHEN** every player still in the game has committed and an eliminated player has not
- **THEN** the server resolves the turn without waiting for them

#### Scenario: The last player standing

- **WHEN** every player but one has been eliminated
- **THEN** the game is decided rather than the turn being held open for the eliminated players

### Requirement: Players Wait For Turn Completion

The system SHALL prevent a player from issuing new orders while their previous
commit is still awaiting resolution.

#### Scenario: Player blocked after committing

- **WHEN** a player has committed and the turn has not yet been resolved
- **THEN** the client reports that it is waiting for the turn to complete
- **AND** the client reloads game data and retries rather than accepting new orders

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

### Requirement: Orders Are Consumed Once

The system SHALL discard players' pending order files after the turn has been
resolved, so no order is applied in a later turn.

#### Scenario: Clearing pending orders

- **WHEN** the server has resolved a turn
- **THEN** every player's pending order file is removed

### Requirement: Game Setup Precedes Play

The system SHALL treat the first commit as the end of setup, after which unit
types and unit placements are fixed and only movement orders are accepted.

#### Scenario: Adding types during setup

- **WHEN** the game has not yet had its first turn resolved
- **THEN** players may define unit types and place units
- **AND** players may not order movement

#### Scenario: Setup closed after the first turn

- **WHEN** the first turn has been resolved
- **THEN** players may order movement
- **AND** players may no longer define types or place units

### Requirement: Resolution Is Deterministic

The system SHALL resolve a turn as a pure function of the board and the orders
given. Resolving the same orders against the same board SHALL always produce the
same result: the same positions, the same health and energy, the same units
destroyed, the same contacts recorded, and the same events in the same order.

Resolving the same orders against boards whose units were registered in
different orders SHALL produce the same result and SHALL report the same events.
The order those events are narrated in MAY follow the board's own order of
units, which is a fact about the board rather than a choice made while
resolving; nothing about what happened SHALL depend on it.

No part of resolution SHALL consult a source of randomness — a random number
generator, a clock, a process or object identity, or anything else outside the
board and the orders. Where two things could happen, the rules SHALL decide
which, rather than leaving it to the order a collection happens to hold its
members in. This is an invariant of the game and constrains every rule added to
it.

#### Scenario: The same turn resolved twice

- **WHEN** the same orders are resolved against two boards built the same way
- **THEN** every unit finishes with the same position, health, energy and destroyed state
- **AND** the same events are reported in the same order

#### Scenario: The order units are held in is not an input

- **WHEN** the same orders are resolved against boards whose units were registered in different orders
- **THEN** the outcome is identical in every case
- **AND** the same events are reported, whatever order they are narrated in

#### Scenario: No rule is decided by collection order

- **WHEN** a rule must choose between two units — which is struck, which holds a square, which order is refused
- **THEN** the choice follows from the rules and the state
- **AND** it does not follow from where either unit sits in a list

#### Scenario: A contest is decided by the units in it

- **WHEN** a contested square is resolved
- **THEN** the damage each contestant takes depends only on the contestants' statistics and energy
- **AND** not on the order the square holds them in
