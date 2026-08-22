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
it on load, including units already destroyed.

#### Scenario: Saving units

- **WHEN** the server saves a game
- **THEN** every unit's player, type, name, symbol, attack, health, energy, coordinates, state, direction, destroyed flag, and on-board flag are written to `data/units.yaml`

#### Scenario: Restoring units

- **WHEN** a game is loaded and `data/units.yaml` exists
- **THEN** each unit is recreated on the board with its stored health, energy, destroyed flag, and on-board flag

### Requirement: Order Publication

The system SHALL have players publish pending orders as a per-player file that
the server consumes when resolving a turn.

#### Scenario: Player publishes orders

- **WHEN** a player commits
- **THEN** their pending orders are written to `players/<number>_units.yaml`
- **AND** a marker file `players/commit_<number>` records that they have committed

#### Scenario: Server consumes orders

- **WHEN** the server resolves a turn
- **THEN** it applies each player's pending orders according to unit state: deploying units in `INITIAL`, moving units in `MOVING`, and leaving units in `NOP` in place
- **AND** it removes the pending order files afterwards

#### Scenario: Invalid order state

- **WHEN** a player publishes an order with a state that is not `INITIAL`, `MOVING`, or `NOP`
- **THEN** the server rejects it as invalid

### Requirement: Pending Order Detection

The system SHALL detect that a player's own orders are still pending and report
that the turn is incomplete.

#### Scenario: Detecting an unresolved commit

- **WHEN** a player loads a game and their own pending order file still exists
- **THEN** the game data reports unprocessed moves

### Requirement: Per-Player View Persistence

The system SHALL write each player a file describing what that player can
currently see, and SHALL load it in preference to the shared board.

#### Scenario: Writing player views

- **WHEN** the server finishes resolving a turn
- **THEN** it writes each player's visible units to `players/<number>_units_seen.yaml`

#### Scenario: Loading a player view

- **WHEN** a client loads a game and its own view file exists
- **THEN** a board is built from that file and used for display

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
