# turn-commit Specification

## Purpose

The game advances in simultaneous turns. Players issue orders independently and
commit them; the server waits until every player has committed, then resolves
all orders at once. No player's orders are applied before another's, so no
player gains an advantage from committing early or late.

## Requirements

### Requirement: Energy Regeneration

The system SHALL give back `REST_GAIN` energy, which SHALL be 2, at the end
of each turn, to every unit standing on the board, whatever it did during
the turn: a unit that moved, struck, was struck, thought, was charged by its
meter, slept or stood still all recover alike. A unit SHALL NOT recover past
the energy its type was designed with, so a type designed with no energy
recovers nothing, and a destroyed unit SHALL recover nothing. Regeneration
SHALL happen after combat and before elimination is judged, so that a player
whose units are merely out of energy is judged on what they will hold rather
than on what they hold mid-turn. The turn's account SHALL report a unit as
rested only where its energy rose.

#### Scenario: A unit that was given no order

- **WHEN** a turn resolves in which a unit was given no order and paid for nothing
- **THEN** that unit's energy is two higher than it was, up to the energy its type was designed with

#### Scenario: A unit already at the energy it was designed with

- **WHEN** a turn resolves in which such a unit took no action
- **THEN** its energy is unchanged
- **AND** the turn's account does not say it rested

#### Scenario: A unit one short of the energy it was designed with

- **WHEN** a turn resolves in which such a unit did nothing
- **THEN** its energy is the energy its type was designed with, not one more

#### Scenario: A unit that was ordered to move

- **WHEN** a turn resolves in which a unit's controller ordered it to move and the move was carried out
- **THEN** that unit's energy is the fare lower and two higher than it was, within the energy its type was designed with

#### Scenario: A unit ordered off the board

- **WHEN** a turn resolves in which a unit's controller ordered it off the board, which costs it nothing
- **THEN** that unit recovers two energy like any other

#### Scenario: A unit that fought

- **WHEN** a turn resolves in which a unit struck in a contest
- **THEN** that unit's energy is its attack lower and two higher than it was, within the energy its type was designed with

#### Scenario: A unit that was attacked but could not pay to fight back

- **WHEN** a turn resolves in which a unit was attacked and could not afford to attack
- **THEN** that unit recovers two energy like any other

#### Scenario: A unit that thought a little and gave no order

- **WHEN** a turn resolves in which a unit's controller ran, gave no order, and its meter did not fill
- **THEN** that unit recovers two energy like any other

#### Scenario: A unit whose meter charged

- **WHEN** a turn resolves in which a unit's meter filled and charged 1 energy
- **THEN** that unit recovers two energy like any other

#### Scenario: A sleeping unit

- **WHEN** a turn resolves in which a unit slept
- **THEN** that unit recovers two energy like any other

#### Scenario: A type designed with no energy

- **WHEN** a turn resolves with a Wall standing on the board
- **THEN** its energy is 0, as it was designed

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

### Requirement: A Setup Commit Clashing With A Committed Square Is Refused

The system SHALL refuse a player's **setup** commit when one of the units it
deploys stands on a square another player has already committed a unit to, and
SHALL name that square in the refusal so the player can deploy elsewhere.

The refused commit SHALL leave that player's setup exactly as it was — nothing
committed, nothing published, every unit and type still theirs to change — so
that they may move the unit and commit again. Setup stays open for them, and
the turn is not held to have begun.

The square SHALL be kept by the setup that was committed first. Where a
deployment reaches the server without having been through a commit — a loaded
player file, or orders written by hand — it SHALL still be refused when the
turn resolves, because nothing checked it on the way in.

This rule SHALL apply to the **setup commit only**. Two things follow from it
that are accepted for setup and would not be for a turn of play: the order in
which players commit decides who keeps a contested square, and the refusal
tells the refused player that the square is occupied, which contact-based
visibility otherwise withholds. Deployments happen only during setup, so
there is nothing for this to reach on any later turn.

#### Scenario: A setup commit that lands on a committed square

- **WHEN** a player commits a setup deploying a unit onto a square another player has already committed a unit to
- **THEN** the commit is refused, naming the square
- **AND** that player's setup is still uncommitted, with its units and types unchanged

#### Scenario: The refused player deploys elsewhere and commits

- **WHEN** a player whose setup commit was refused for a clash moves the unit to a free square and commits again
- **THEN** the commit is accepted

#### Scenario: The first setup committed keeps the square

- **WHEN** two players commit setups deploying onto the same square, one after the other
- **THEN** the first keeps the square and stays committed
- **AND** only the second is refused

#### Scenario: A setup that clashes with nothing

- **WHEN** a player commits a setup whose deployments are all on squares nobody has committed to
- **THEN** the commit is accepted

#### Scenario: A clash reaching the server without a commit

- **WHEN** deployments onto one square reach the server without having been through a commit
- **THEN** they are refused when the turn resolves, as they are today

### Requirement: Deployment On First Resolution, After A Commit That Was Accepted

The system SHALL place newly created units onto the board when the turn is
resolved. Deploying a brand new unit onto a square that is already taken is
illegal: the system SHALL refuse the deployment and SHALL resolve the turn
without it, rather than failing the turn.

Where two deployments that never passed through an accepted commit contend for
one square in the same turn, the system SHALL refuse both, so that nothing
which bypasses a commit is favoured by the order it happens to be read in.

#### Scenario: Deploying a new unit

- **WHEN** a turn is resolved and a unit is in the `INITIAL` state
- **THEN** the unit is placed at its assigned coordinates
- **AND** the unit moves to the `NOP` state

#### Scenario: Deploying onto an occupied square

- **WHEN** a unit is deployed at coordinates that already hold a unit
- **THEN** the deployment is refused with an error naming the unit and the square
- **AND** no unit is created
- **AND** the unit already holding the square is unaffected

#### Scenario: Two unchecked deployments onto one square in the same turn

- **WHEN** two units that never passed through an accepted commit are deployed at the same coordinates before the turn is resolved
- **THEN** both are refused
- **AND** the turn resolves with neither on that square
- **AND** the square is left empty

#### Scenario: Deployment is not movement

- **WHEN** a unit already on the board is ordered to move into a square another unit holds
- **THEN** the order is allowed
- **AND** the two units contest the square

### Requirement: Only Units In Play Are Resolved

The system SHALL resolve movement and combat only for units currently on the
board, skipping units that have been destroyed or not yet deployed.

A unit belonging to an eliminated player SHALL be resolved as terrain: it
holds its square, takes no order and lands no attack, and is attacked and
destroyed like any other unit.

#### Scenario: Skipping units not in play

- **WHEN** a turn is resolved
- **THEN** units not on the board take no action

#### Scenario: An eliminated player's units hold their squares

- **WHEN** a turn is resolved and an eliminated player has units standing
- **THEN** those units stay where they are
- **AND** they land no attack in any contest they are part of

#### Scenario: Clearing them

- **WHEN** another player's unit attacks one of them
- **THEN** it takes damage and is destroyed if it runs out of health

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

### Requirement: The Think Phase

The system SHALL run every awake unit's controller against the board as the
turn began, before deployment, movement and combat, as the first phase of
resolving a turn, every controller reading the same snapshot so that none
sees another's order, message or move from the same turn. The orders the
controllers give SHALL be the turn's only orders once play has begun, and the
energy the meter charges SHALL be deducted in this phase.

#### Scenario: What a controller reads

- **WHEN** a controller runs
- **THEN** it reads the board, its army's map, the flags and its own inbox as they stood when the turn began

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
