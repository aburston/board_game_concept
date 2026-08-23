# game-persistence Specification

## Purpose

All game state lives in YAML files on disk. The filesystem is also the transport
between the server and its clients: players publish orders by writing files, and
the server publishes results the same way. Multiple games coexist, separated by
game number.

## Requirements

### Requirement: Game Directory Layout

The system SHALL store each game under a directory keyed by game number, split
into shared game data and per-player files.

#### Scenario: Resolving game paths

- **WHEN** a game with a given number is opened
- **THEN** shared data is read from and written to `games/_<gameno>/data`
- **AND** per-player files are read from and written to `games/_<gameno>/players`

#### Scenario: Creating a game directory

- **WHEN** a game's directories do not yet exist
- **THEN** they are created

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

The system SHALL persist each player's number and unit type definitions in a
per-player file.

#### Scenario: Saving a player

- **WHEN** a player's data is saved
- **THEN** their number and unit types are written to `players/<number>.yaml`

#### Scenario: Loading players

- **WHEN** a game is loaded
- **THEN** every player file is read and its types reconstructed as unit types

### Requirement: Unit State Persistence

The system SHALL persist the full state of every unit on the board and restore
it on load, including units already destroyed and units sharing a square. A unit
SHALL be restored in a state that takes no action of its own: restoring is not
an order, and a restored unit SHALL NOT be treated as waiting to be deployed.

#### Scenario: Saving units

- **WHEN** the server saves a game
- **THEN** every unit's player, type, name, symbol, attack, health, energy, coordinates, state, direction, destroyed flag, and on-board flag are written to `data/units.yaml`

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

#### Scenario: Player publishes orders

- **WHEN** a player commits
- **THEN** their pending orders are written to `players/<number>_units.yaml`
- **AND** a marker file `players/commit_<number>` records that they have committed

#### Scenario: Destroyed units are not published as orders

- **WHEN** a player commits while holding destroyed units
- **THEN** no order is published for any destroyed unit
- **AND** the server has nothing to refuse on their account

#### Scenario: Server consumes orders

- **WHEN** the server resolves a turn
- **THEN** it applies each player's pending orders according to unit state: deploying units in `INITIAL`, moving units in `MOVING`, and leaving units in `NOP` in place
- **AND** it removes the pending order files afterwards

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

The system SHALL detect that a player's own orders are still pending and report
that the turn is incomplete.

#### Scenario: Detecting an unresolved commit

- **WHEN** a player loads a game and their own pending order file still exists
- **THEN** the game data reports unprocessed moves

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
