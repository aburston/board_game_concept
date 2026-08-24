## ADDED Requirements

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

## MODIFIED Requirements

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
