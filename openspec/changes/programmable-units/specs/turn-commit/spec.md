# Spec Delta

## ADDED Requirements

### Requirement: The Think Phase

The system SHALL run every awake unit's controller against the board as the
turn began, before deployment, movement and combat, as the first phase of
resolving a turn. Each controller SHALL read the same snapshot - the board,
its army's map, the flags and its own inbox as they stood when the turn began
- so that no controller sees another's order, message or move from the same
turn. The orders the controllers give SHALL be the turn's orders; there SHALL
be no other source of movement orders once play has begun. Energy the meter
charges SHALL be deducted in this phase.

#### Scenario: Controllers run first

- **WHEN** a turn is resolved
- **THEN** every awake controller runs before any unit is deployed, moved or fought
- **AND** the orders they give are the ones movement applies

#### Scenario: No controller sees another's turn

- **WHEN** two controllers run in one turn and one's answer would differ if the other had already moved or spoken
- **THEN** both read the board, map and inboxes as the turn began
- **AND** the outcome is the same whichever ran first

#### Scenario: A unit with no controller

- **WHEN** a turn is resolved
- **THEN** a unit of a type with compute 0 is given no order
- **AND** it is moved, fought and rested like any other unit

### Requirement: The Game Is Resolved To Its End When Setup Completes

The system SHALL resolve every turn of the game, one after another without
waiting for anyone, as soon as every registered player's setup has been
committed. Resolution SHALL continue until the game is decided, until the
whole state of the game repeats, or until the turn cap, as `game-outcome`
states, and SHALL record every turn as it goes. The commit that completes
setup SHALL be the last act any player takes in the game.

#### Scenario: The last setup commit plays the game

- **WHEN** the last registered player commits their setup
- **THEN** the game is resolved turn by turn to its end before that commit returns, or as soon after as the server can
- **AND** every turn's record is written

#### Scenario: Nobody is waited for

- **WHEN** the game is being resolved
- **THEN** no turn waits for any player's commit, order or acknowledgement

#### Scenario: A seat opening a resolved game

- **WHEN** a player opens a game whose setups were all committed
- **THEN** the game is already resolved to its end
- **AND** the player is shown its record

### Requirement: Every Turn Is Recorded

The system SHALL record, for every turn it resolves, the board and every unit
as the turn left them, the flags, what the turn did, each seat's share of it,
and each unit's controller trace, against the turn's number, and SHALL keep
every turn's record for the life of the game so that the game can be replayed
from its first turn to its last.

#### Scenario: A turn is recorded

- **WHEN** a turn is resolved
- **THEN** its record holds the board, the units, the flags, the events and every controller's trace, named by its turn number

#### Scenario: Every turn is kept

- **WHEN** a game has been resolved to its end
- **THEN** the record of every turn from the first to the last is readable

## MODIFIED Requirements

### Requirement: Energy Regeneration

The system SHALL give back `REST_GAIN` energy, at the end of each turn, to
every unit on the board that took no action during it - one that was given no
order **and** paid for nothing while the turn resolved. A unit SHALL NOT
recover past the energy its type was designed with, and a destroyed unit SHALL
recover nothing. Regeneration SHALL happen after combat and before elimination
is judged, so that a player whose units are merely out of energy is judged on
what they will hold rather than on what they hold mid-turn.

Both halves of "took no action" are required. A unit whose controller ordered
it to move has acted whether or not the move was carried out: one ordered off
the board pays nothing and still does not rest, so a program that walks a
unit into the edge every turn is not a way to refuel. A unit that was attacked
and could not afford to strike back has done nothing at all, and does rest -
being attacked is not an action.

Thinking is paying only when the meter charges. A unit whose controller ran
and gave no order, and whose meter did not reach its capacity this turn, paid
for nothing and SHALL rest. A unit whose meter charged energy this turn paid
for something and SHALL NOT rest. A sleeping unit's controller does not run,
so a sleeper that was not in a fight SHALL rest.

#### Scenario: A unit that was given no order

- **WHEN** a turn resolves in which a unit was given no order and paid for nothing
- **THEN** that unit's energy is one higher than it was, up to the energy its type was designed with

#### Scenario: A unit already at the energy it was designed with

- **WHEN** a turn resolves in which such a unit took no action
- **THEN** its energy is unchanged

#### Scenario: A unit that was ordered to move

- **WHEN** a turn resolves in which a unit's controller ordered it to move
- **THEN** that unit does not recover energy, whether or not the move was carried out

#### Scenario: A unit ordered off the board

- **WHEN** a turn resolves in which a unit's controller ordered it off the board, which costs it nothing
- **THEN** that unit does not recover energy

#### Scenario: A unit that was attacked but could not pay to fight back

- **WHEN** a turn resolves in which a unit was attacked and could not afford to attack
- **THEN** that unit recovers energy

#### Scenario: A unit that thought a little and gave no order

- **WHEN** a turn resolves in which a unit's controller ran, gave no order, and its meter did not fill
- **THEN** that unit recovers energy

#### Scenario: A unit whose meter charged

- **WHEN** a turn resolves in which a unit's meter filled and charged 1 energy, and the unit gave no order
- **THEN** that unit does not recover energy

#### Scenario: A sleeping unit

- **WHEN** a turn resolves in which a unit slept and was not in a fight
- **THEN** that unit recovers energy

#### Scenario: A destroyed unit

- **WHEN** a turn resolves in which a unit is destroyed
- **THEN** it recovers nothing

### Requirement: Two-Phase Turn Resolution

The system SHALL resolve a turn in phases, in this order: a think phase in
which every awake controller runs against the board as the turn began and
gives its unit's order; a movement phase that decides every unit's
destination from that same board, applies all those moves together, and
gathers the squares more than one unit finishes in; a combat phase that
resolves those squares; and a rest phase. No unit's move SHALL be applied
before another's destination has been decided, and no controller SHALL run
after any move has been applied.

#### Scenario: Resolving a turn

- **WHEN** a turn is resolved
- **THEN** every awake controller first runs against the board as the turn began
- **AND** every unit on the board then has its destination decided against that same board
- **AND** all of those moves are then applied together
- **AND** only then is combat resolved in every contested square

#### Scenario: No unit is left mid-move

- **WHEN** the combat phase begins
- **THEN** no unit remains in the `MOVING` state

#### Scenario: No unit sees another's move before its own is decided

- **WHEN** two units are ordered such that one's destination would differ according to whether the other had already moved
- **THEN** both destinations are decided from the board as the turn began
- **AND** the outcome is the same whichever unit is processed first

### Requirement: Drafting Before Committing

The system SHALL record what a session has done since its last commit as it is
done, rather than holding it only for the life of the session. Everything a
caller may do to a game before committing SHALL be drafted: unit types defined,
programs set, units deployed, the flag designated, and the administrator's
setup of the board and its players.

A draft SHALL be restored when its owner reopens the game, so that work is not
lost when a session ends before it commits.

A draft SHALL be private to the session that made it. No other player, the
administrator, and no observer SHALL be able to read it. A drafted setup is not
a published one, and knowing that an opponent is still deciding - or what they
are deciding about - SHALL NOT be obtainable from the game.

Restoring a draft SHALL apply the same rules that applied when each action was
first taken. An action that is no longer legal SHALL be dropped and reported to
its owner, and the rest of the draft SHALL still be restored; a draft SHALL NOT
make a game impossible to open.

#### Scenario: Work is drafted as it is done

- **WHEN** a player defines a type, sets its program, or deploys a unit, and does not commit
- **THEN** the action is recorded against that player
- **AND** it is recorded before the session ends

#### Scenario: A session that ends before committing

- **WHEN** a player defines types and deploys units, the session ends without committing, and the player reopens the game
- **THEN** the types they defined are theirs again, with their programs
- **AND** the units they deployed are where they placed them
- **AND** they may continue from where they stopped

#### Scenario: A draft is not visible to anyone else

- **WHEN** a player has drafted a setup and has not committed
- **THEN** no other player is shown it
- **AND** the administrator is not shown it
- **AND** an observer is not shown it
- **AND** nothing reveals that the player has drafted anything at all

#### Scenario: A draft from an earlier turn

- **WHEN** a game is opened holding a draft recorded before the game was resolved
- **THEN** the draft is discarded, the setup having been committed
- **AND** the game opens on its record

#### Scenario: Drafting is not permitted while awaiting resolution

- **WHEN** a player has committed their setup and another player has not
- **THEN** no further action is drafted for them
- **AND** the client reports that it is waiting for the other setups

#### Scenario: A drafted action that is no longer legal

- **WHEN** a draft is restored and one of its actions can no longer be carried out
- **THEN** that action is dropped and reported to its owner
- **AND** every other action in the draft is restored
- **AND** the game opens

#### Scenario: Committing consumes the draft

- **WHEN** a player commits
- **THEN** their draft is discarded, having become their committed setup
- **AND** reopening the game restores no draft for them

### Requirement: Commits Are Final

The system SHALL treat a commit as irreversible; a player cannot withdraw or
amend their setup once committed. A player MAY amend their draft freely up to
the moment they commit, and SHALL NOT be able to amend it afterwards. There
SHALL be no way to withdraw a commit: a player who has committed is committed
for the game, whatever any other player does next.

#### Scenario: Committing orders

- **WHEN** a player commits
- **THEN** their types, programs, units and flag are fixed
- **AND** the player cannot undo them

#### Scenario: Amending before committing

- **WHEN** a player sets a program on a type and then sets another on the same type, before committing
- **THEN** the later program stands
- **AND** the earlier one has no effect on the game

#### Scenario: A commit cannot be withdrawn

- **WHEN** a player has committed and another player has not
- **THEN** there is no command or request that withdraws their commit
- **AND** the game is resolved with the setup they committed

### Requirement: Orders Are Consumed Once

The system SHALL clear every unit's order after the turn it was given for has
been resolved, so that no order is applied in a later turn. An order SHALL
come from the unit's controller in the turn it is applied, and from nowhere
else.

#### Scenario: Clearing pending orders

- **WHEN** a turn has been resolved
- **THEN** every unit's direction is cleared and its state returns to `NOP`
- **AND** a unit whose controller gives no order next turn does not move

### Requirement: Game Setup Precedes Play

The system SHALL treat a player's setup commit as the end of their setup,
after which their unit types, programs, unit placements and flag are fixed,
and SHALL treat the last player's setup commit as the start of play, after
which no player gives the game anything: every order is a controller's.

A player's setup commit SHALL be refused unless exactly one of their units
carries their flag, as `flag-carrier` requires.

#### Scenario: Adding types during setup

- **WHEN** a player has not committed their setup
- **THEN** they may define unit types, set programs, place units and designate the flag
- **AND** there is no order they may give a unit

#### Scenario: Setup closed by committing it

- **WHEN** a player has committed their setup
- **THEN** they may no longer define types, set programs, place units or move the flag
- **AND** the refusal says their setup is committed

#### Scenario: Setup closed after the first turn

- **WHEN** every player's setup is committed and the first turn has resolved
- **THEN** the game is resolved by the controllers alone
- **AND** no command a player gives changes it
- **AND** no player may define types, set programs or place units

#### Scenario: A setup with no flag

- **WHEN** a player commits a setup in which no unit of theirs carries the flag
- **THEN** the commit is refused
- **AND** setup remains open for that player

## REMOVED Requirements

### Requirement: Commit Barrier

**Reason**: There is no per-turn commit for a barrier to wait on. Every order
comes from a unit's controller, and the game is resolved to its end once every
player's setup is committed. What the barrier protected - that a turn is
resolved once, while the game is held, from the whole game - is kept by `A
Turn Is Resolved From The Whole Game` and `The Game Is Resolved To Its End
When Setup Completes`.

**Migration**: Remove the per-turn wait and the player-count check from the
resolver; resolve all turns in one held act when the last setup commit lands.
The setup-clash and no-flag refusals on a setup commit are unchanged.

### Requirement: Players Wait For Turn Completion

**Reason**: A player has nothing to wait for. Their last act is the setup
commit; what follows is a record they read.

**Migration**: The client, after its setup commit, opens the record and offers
the replay commands `player-client` states, instead of blocking on a turn.
