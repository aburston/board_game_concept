# game-persistence Specification

## Purpose

All game state lives in YAML files on disk. The filesystem is also the transport
between the server and its clients: players publish orders by writing files, and
the server publishes results the same way. Multiple games coexist, separated by
game number.

## Requirements

### Requirement: Game Directory Layout

The system SHALL store each game under a directory keyed by game number, split
into shared game data and per-player files. Whatever the system needs to hold a
game SHALL be kept where nothing that classifies a game's files by name will
read it.

#### Scenario: Resolving game paths

- **WHEN** a game with a given number is opened
- **THEN** shared data is read from and written to `games/_<gameno>/data`
- **AND** per-player files are read from and written to `games/_<gameno>/players`

#### Scenario: Creating a game directory

- **WHEN** a game's directories do not yet exist
- **THEN** they are created

#### Scenario: What holds a game is not one of its files

- **WHEN** a game is held
- **THEN** whatever records that is not read as shared game data, as a player, as published orders, or as a commit

### Requirement: A Game May Be Held While It Is Used

The system SHALL let a caller hold a game while reading or writing it, and
SHALL serialise those holdings: a caller holding a game for writing SHALL
exclude every other holder, and callers holding it for reading SHALL be able to
hold it together.

Holding SHALL be something the storage offers rather than something a caller
arranges for itself, so that storage which keeps a game some other way may hold
it some other way.

A game SHALL NOT be held across a wait for something a person must do. The
commit barrier holds a turn open for as long as a player takes to decide, and a
game held across that would be stopped rather than protected.

Where the platform offers no means of holding a game, the system SHALL carry on
without holding it, behaving as it does when nothing is held, and SHALL NOT
report that a game was held when it was not.

#### Scenario: Two writers do not overlap

- **WHEN** one caller holds a game for writing and another asks to hold it for writing
- **THEN** the second waits until the first has finished

#### Scenario: A reader waits for a writer

- **WHEN** a caller holds a game for writing and another asks to hold it for reading
- **THEN** the reader waits until the writer has finished
- **AND** does not read a game part way through being written

#### Scenario: Readers do not exclude each other

- **WHEN** one caller holds a game for reading and another asks to hold it for reading
- **THEN** both hold it at once

#### Scenario: Holding is released when the caller is done

- **WHEN** a caller finishes with a game it was holding, whether it finished normally or because of an error
- **THEN** the game is no longer held
- **AND** another caller may hold it

#### Scenario: Waiting for a turn does not hold the game

- **WHEN** the server is waiting for players to commit, or a player is waiting for a turn to be resolved
- **THEN** the game is not held
- **AND** another caller may hold it meanwhile

### Requirement: A Write Replaces What It Replaces

The system SHALL write a game's files by replacing them rather than by emptying
and refilling them, so that a reader sees either what was there before or what
is there after, and never part of either. A write that does not finish — because
the process ended — SHALL leave the previous contents readable.

#### Scenario: A reader never sees a partly written file

- **WHEN** a game file is being written and another caller reads it
- **THEN** it reads either the previous contents or the new contents in full

#### Scenario: A write that does not finish leaves the file readable

- **WHEN** a process ends part way through writing a game file
- **THEN** the file still holds what it held before
- **AND** the game can still be opened

#### Scenario: What a write leaves behind is not mistaken for a game's own files

- **WHEN** a game's files are written
- **THEN** nothing left behind by the writing is read as a player, as published orders, or as a commit

### Requirement: Board Configuration Persistence

The system SHALL persist the board dimensions and restore them when the game is
loaded.

#### Scenario: Saving board configuration

- **WHEN** a game is saved
- **THEN** the board dimensions are written to `data/board.yaml`

#### Scenario: Loading board configuration

- **WHEN** a game is loaded and `data/board.yaml` exists
- **THEN** a board of the stored dimensions is created

#### Scenario: Missing board configuration for a player

- **WHEN** a player loads a game whose board configuration is absent
- **THEN** the client reports that no such game exists and stops

#### Scenario: Missing board configuration for the server

- **WHEN** the server loads a game whose board configuration is absent
- **THEN** the game is treated as new and the server enters interactive setup

### Requirement: Player And Type Persistence

The system SHALL persist each player's number, point budget and unit type
definitions in a per-player record, and SHALL restore all three when the game
is loaded.

A stored player record SHALL carry the budget that player was registered with.
A record read without one is malformed game data and SHALL be treated as
`Malformed Data Is Fatal` requires: the game is not opened, and the error names
the player whose record has no budget. A budget is a rule the game was set up
under, and defaulting a missing one would carry on playing a game by rules it
was not set up with.

This applies to a record a game has written. A player file offered to
`load player` is configuration rather than stored state, and `game-server`
states what a missing budget means there.

#### Scenario: Saving a player

- **WHEN** a player's data is saved
- **THEN** their number, budget and unit types are written to their record

#### Scenario: Loading players

- **WHEN** a game is loaded
- **THEN** every player record is read, its budget restored, and its types
  reconstructed as unit types

#### Scenario: A stored record with no budget

- **WHEN** a game is opened holding a player record that carries no budget
- **THEN** the error is reported, naming that player
- **AND** the game is not opened

#### Scenario: A budget survives a round trip

- **WHEN** a player registered with a budget of 150 is saved and the game is
  opened again
- **THEN** that player's budget is 150
### Requirement: Unit State Persistence

The system SHALL persist the full state of every unit on the board and restore
it on load, including units already destroyed and units sharing a square. A unit
SHALL be restored in a state that takes no action of its own: restoring is not
an order, and a restored unit SHALL NOT be treated as waiting to be deployed.

#### Scenario: Saving units

- **WHEN** the server saves a game
- **THEN** every unit's player, type, name, symbol, attack, health, energy, coordinates, state, direction, destroyed flag, on-board flag, and whether it carries its player's flag are written to `data/units.yaml`

#### Scenario: Restoring the carrier

- **WHEN** a game holding a flag carrier is loaded
- **THEN** the same unit carries that player's flag

#### Scenario: Restoring units

- **WHEN** a game is loaded and `data/units.yaml` exists
- **THEN** each unit is recreated on the board with its stored health, energy, destroyed flag, and on-board flag

#### Scenario: A restored unit is not waiting to deploy

- **WHEN** a unit is restored
- **THEN** it is not in the state that means a unit is waiting to be placed
- **AND** resolving the next turn does not deploy it again

#### Scenario: Restoring a destroyed unit

- **WHEN** a destroyed unit is restored
- **THEN** it is restored destroyed and off the board
- **AND** it occupies no square
- **AND** resolving the next turn does not place it on one

#### Scenario: Restoring a shared square

- **WHEN** a saved game holds several units on one square
- **THEN** loading it restores every one of those units to that square
- **AND** loading does not fail
- **AND** the rule refusing deployment onto an occupied square does not apply
### Requirement: Order Publication

The system SHALL have players publish pending orders as a per-player file that
the server consumes when resolving a turn, and SHALL apply each order to the
unit it names rather than to whatever occupies the square. A player SHALL publish
orders only for units in play: a destroyed unit SHALL NOT be published as an
order of any kind.

Committing SHALL be recorded as a fact about a player and a turn, rather than
inferred from the presence of a file, so that the system can answer whether a
given player has committed for the turn now open. Which players the commit
barrier is waiting for SHALL be determined from that record.

A player's pending orders SHALL NOT be removed until everything the turn
produced has been published, because their removal is what releases a player
waiting on that turn. Orders published on a player's behalf for the turn *about
to be* resolved SHALL be written after that removal, so that seeding the next
turn cannot erase them.

#### Scenario: Player publishes orders

- **WHEN** a player commits
- **THEN** their pending orders are written to `players/<number>_units.yaml`
- **AND** a marker file `players/commit_<number>` records that they have committed
- **AND** the marker records the turn they committed for

#### Scenario: Determining who has committed

- **WHEN** the system is asked which players have committed for the turn now open
- **THEN** the answer comes from the commit records
- **AND** a player whose most recent commit was for an earlier turn is not counted

#### Scenario: A player who has drafted but not committed

- **WHEN** a player has drafted orders and has not committed
- **THEN** they are not counted as having committed
- **AND** the turn is still held open for them

#### Scenario: Destroyed units are not published as orders

- **WHEN** a player commits while holding destroyed units
- **THEN** no order is published for any destroyed unit
- **AND** the server has nothing to refuse on their account

#### Scenario: Server consumes orders

- **WHEN** the server resolves a turn
- **THEN** it applies each player's pending orders according to unit state: deploying units in `INITIAL`, moving units in `MOVING`, and leaving units in `NOP` in place
- **AND** it removes the pending order files afterwards

#### Scenario: Orders are removed only once the turn is published

- **WHEN** the server resolves a turn
- **THEN** it writes the turn number, each player's file and refusals, the record of every unit, and every player's view
- **AND** only then removes the pending order files

#### Scenario: Seeding the next turn does not erase it

- **WHEN** the server resolves a turn for a game whose player was loaded from a file holding units
- **THEN** that player's units are published as their orders for the turn about to be resolved
- **AND** those orders survive the removal of the turn's consumed orders
- **AND** the units reach the board when that turn is resolved

#### Scenario: An order naming a destroyed unit

- **WHEN** a player publishes an order for a unit the server holds as destroyed
- **THEN** the server refuses the order
- **AND** creates no unit
- **AND** resolves the turn without it

#### Scenario: A player with no units commits

- **WHEN** a player who holds no units commits, publishing an order file that lists none
- **THEN** the server resolves the turn with no orders from that player
- **AND** the turn completes for every other player

#### Scenario: Invalid order state

- **WHEN** a player publishes an order with a state that is not `INITIAL`, `MOVING`, or `NOP`
- **THEN** the server rejects it as invalid
- **AND** records the rejection for that player
- **AND** resolves the turn without it, rather than failing

#### Scenario: A move order naming a unit the player does not own

- **WHEN** a player publishes a move order for a unit that is not theirs or does not exist
- **THEN** the server rejects the order
- **AND** resolves the turn without it

#### Scenario: Applying an order to a unit on a shared square

- **WHEN** the server applies a move order for a unit whose square holds several units
- **THEN** the order is applied to the named unit belonging to the ordering player
- **AND** the other units in that square are unaffected

### Requirement: Pending Order Detection

The system SHALL detect that a player's own committed orders are still pending
and report that the turn is incomplete. A player's orders SHALL be treated as
pending until the turn that consumes them has been published in full.

A session SHALL NOT read a game part way through a turn being resolved: it holds
the game for reading, and a turn being resolved holds it for writing, so a
session opening one mid-resolution waits and then reads a turn that is
complete.

A draft SHALL NOT be treated as a pending commit: a player who has drafted work
and not committed it has an open turn, not an unresolved one.

#### Scenario: Detecting an unresolved commit

- **WHEN** a player loads a game and their own pending order file still exists
- **THEN** the game data reports unprocessed moves

#### Scenario: Loading while a turn is being resolved

- **WHEN** a player opens a game after the server has begun resolving the turn they committed to and before it has finished
- **THEN** the session waits until the resolution is finished
- **AND** is not shown a partly published turn
- **AND** once it opens, the turn it reads is complete and its orders are no longer pending

#### Scenario: A draft is not an unresolved commit

- **WHEN** a player loads a game holding a draft and no published orders
- **THEN** the game data reports no unprocessed moves
- **AND** the player may continue to give orders

### Requirement: Draft Persistence

The system SHALL store each session's uncommitted work in a per-session file
under the game's players directory, separate from the orders that session has
published. The file SHALL record the turn the work was drafted for.

A draft file SHALL be read only for the session that owns it. Loading a game
SHALL NOT read another session's draft, in the same way that a client reads its
own view rather than the shared record of all units.

A draft SHALL be removed when its owner commits, the work having become their
published orders.

#### Scenario: Writing a draft

- **WHEN** a session carries out an action without committing
- **THEN** the action is written to that session's draft file under `games/_<gameno>/players`
- **AND** the file records the turn it was drafted for

#### Scenario: Reading a draft back

- **WHEN** a game is loaded and the loading session's draft file exists and names the current turn
- **THEN** the actions it holds are applied to the game the session sees

#### Scenario: A session does not read another's draft

- **WHEN** a game is loaded
- **THEN** no draft file belonging to another player is read
- **AND** the administrator's session reads no player's draft

#### Scenario: Committing removes the draft

- **WHEN** a player commits
- **THEN** their draft file is removed
- **AND** their published orders hold the work it held

#### Scenario: A game with no draft

- **WHEN** a game is loaded and the loading session has no draft file
- **THEN** the game loads as though the draft were empty
- **AND** nothing is reported as missing

### Requirement: Per-Player View Persistence

The system SHALL write each player a file describing what that player can
currently see, and a client SHALL load that file as the only board it holds. A
client SHALL NOT read the shared record of all units.

#### Scenario: Writing player views

- **WHEN** the server finishes resolving a turn
- **THEN** it writes each player's visible units to `players/<number>_units_seen.yaml`

#### Scenario: Loading a player view

- **WHEN** a client loads a game and its own view file exists
- **THEN** a board is built from that file and used for everything the client shows

#### Scenario: A client does not read the shared unit record

- **WHEN** a client loads a game
- **THEN** it does not read `data/units.yaml`

#### Scenario: A client does not read other players' files

- **WHEN** a client loads a game
- **THEN** it does not read another player's `players/<number>.yaml`
- **AND** the enemy types it knows of come from its own view

### Requirement: Board Size Validated Before Saving

The system SHALL refuse to save a game whose board has not been given valid
dimensions.

#### Scenario: Saving without a board size

- **WHEN** a save is attempted and either board dimension is 1 or smaller
- **THEN** the save is refused and reported
- **AND** the caller returns to the interactive prompt

### Requirement: Malformed Data Is Fatal

The system SHALL stop rather than continue with partially parsed game data.

#### Scenario: Unparseable YAML

- **WHEN** a game file cannot be parsed
- **THEN** the error is reported and the process exits

#### Scenario: Unknown player

- **WHEN** a session is opened for a player number that does not exist in the game
- **THEN** the error is reported and the process exits

### Requirement: Rejected Order Publication

The system SHALL publish the orders it refused while resolving a turn as a
per-player file the client reads, so that a player learns why an order of theirs
had no effect. This SHALL cover every order that did not do what it said,
including one refused while being applied and one that failed while the turn was
being resolved. The file SHALL be written for every player on every resolved
turn, and SHALL name the turn it describes, so it always describes the turn just
resolved.

#### Scenario: An order is refused

- **WHEN** the server refuses one of a player's orders while resolving a turn
- **THEN** it writes that order to `players/<number>_rejected.yaml`
- **AND** records the unit's name, type, coordinates, and the reason it was refused
- **AND** records the turn number the refusal belongs to

#### Scenario: A move that failed while the turn was resolved

- **WHEN** a unit's move is not carried out because it cannot pay, or because it would leave the board
- **THEN** that order is written to the ordering player's rejection file with the reason

#### Scenario: A contest that ended undecided

- **WHEN** a contest ends with more than one unit undestroyed
- **THEN** each contestant is written to its owner's rejection file, recording that the contest was undecided and the square it was fought over

#### Scenario: No orders were refused

- **WHEN** the server resolves a turn without refusing any of a player's orders
- **THEN** `players/<number>_rejected.yaml` is written with no entries

#### Scenario: Rejections do not accumulate

- **WHEN** the server resolves a turn
- **THEN** the file it writes replaces the previous turn's rejections rather than adding to them

#### Scenario: Rejected orders are not player files

- **WHEN** the client scans the players directory to load player data
- **THEN** it skips the rejection files
- **AND** reads them separately

#### Scenario: A refused order leaves no unit behind

- **WHEN** the server refuses a deployment
- **THEN** no unit of that name exists on the board for that player
- **AND** the board holds no trace of the refused unit
- **AND** the player is free to deploy it elsewhere on a later turn

### Requirement: Turn Event Publication

The system SHALL record what each resolution did - units placed and moved,
engagements, every attack with its damage, every destruction, and how each
contested square was decided - as a log of the whole turn, and SHALL record
for each seat the part of that log the seat was entitled to be told.

A seat's record SHALL be decided at resolution, from what that seat could see
while the turn was being fought. It SHALL NOT be produced by filtering the
whole log when it is read, because a sighting lasts one turn and by then there
is nothing left to say who could see what.

Both records SHALL keep the turns that came before, so that what a game did
can be read back rather than inferred from the position it left.

#### Scenario: A resolution is recorded

- **WHEN** the server resolves a turn
- **THEN** the whole of what that turn did is recorded against the turn number
- **AND** each seat's share of it is recorded against that seat and that turn

#### Scenario: A fight a seat was in

- **WHEN** one of a seat's units fights
- **THEN** that seat's record holds every attack of that fight, the damage each
  dealt, and the square it was fought on

#### Scenario: A fight a seat could not see

- **WHEN** two other players fight where this seat can see neither of them
- **THEN** nothing of that fight is in this seat's record

#### Scenario: The turns before this one

- **WHEN** several turns have been resolved
- **THEN** each turn's record is still readable, named by its turn number

#### Scenario: An added record does not need the game to be remade

- **WHEN** a game made before turn events were recorded is opened
- **THEN** the store gains the tables or files they are kept in
- **AND** nothing already stored is changed

### Requirement: Turn Number And Outcome Persistence

The system SHALL persist the number of the last turn resolved and, once the game
is decided, its outcome, so that any session opened on the game reads the same
turn number and the same result.

#### Scenario: Saving the turn number

- **WHEN** the server resolves a turn
- **THEN** the number of that turn is written with the game's shared data

#### Scenario: Loading the turn number

- **WHEN** a game is loaded
- **THEN** it reports the number of the last turn resolved
- **AND** a game with no resolved turn reports none

#### Scenario: Saving the outcome

- **WHEN** the server resolves a turn that decides the game
- **THEN** the winner or the draw, and the deciding turn number, are written with the game's shared data

#### Scenario: An undecided game holds no outcome

- **WHEN** a game that is still being played is loaded
- **THEN** no outcome is read

### Requirement: Flag Publication

The system SHALL publish, on every resolution, the square each player's flag
is on and whether it is still standing, as a record every player may read
whatever their visibility. It SHALL NOT publish the name, type or statistics
of the unit carrying it: those reach a player only through their own view, as
contact allows.

#### Scenario: Publishing the flags

- **WHEN** a turn is resolved
- **THEN** each player's flag is published with its owner and its square

#### Scenario: A flag that has fallen

- **WHEN** a resolution destroys a flag carrier
- **THEN** that flag is published as fallen, with no square

#### Scenario: What is not published with it

- **WHEN** the published flags are read
- **THEN** no carrier's name, type, symbol or statistics are in them
