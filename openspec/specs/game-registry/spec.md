# game-registry Specification

## Purpose

Which games exist, and making one.

The rest of the served interface is per-game: a caller has to know a game's
number before it can ask anything at all. That is enough for a client somebody
typed the number into and not enough for a lobby, where the whole question is
which games there are and which of them is waiting for a player.

The listing is derived by reading the games rather than kept in a record of its
own. A registry that is written down is a fourth thing to hold in step with the
board, and its failure mode is a lobby that lists a game which is not there or
hides one that is. `game-outcome` derives elimination from the board for the
same reason.

## Requirements

### Requirement: Which Games Exist Can Be Asked

The system SHALL answer, over the served interface, which games exist. For
each it SHALL report the number it is known by, whether it is being set up,
being played or decided, the size of its board where it has one, the number of
the turn it has reached, and its registered player numbers.

A game SHALL be listed whether or not the caller holds a seat in it, so that a
seat can be found before it is held.

#### Scenario: Listing games

- **WHEN** the games that exist are asked for
- **THEN** every game under the games tree is reported
- **AND** each carries its number, its state and its turn number

#### Scenario: A game without a board yet

- **WHEN** a game whose board has not been sized is listed
- **THEN** it is reported as being set up
- **AND** its board size is reported as absent rather than as a size

#### Scenario: A game nobody holds a seat in

- **WHEN** the caller holds no seat in a game
- **THEN** that game is still listed

#### Scenario: A decided game

- **WHEN** a game has been decided
- **THEN** it is listed as decided
- **AND** its outcome is reported

### Requirement: The Listing Is Derived, Not Tracked

The system SHALL determine the listing by reading the games that exist, and
SHALL NOT keep a separate record of which games there are.

A game created by any means SHALL be listed without anything being told about
it, and a game that has been removed SHALL stop being listed for the same
reason.

#### Scenario: A game created outside the served interface

- **WHEN** a game is created by a command-line role and the games are listed
- **THEN** that game is listed
- **AND** nothing had to register it

#### Scenario: A game that is gone

- **WHEN** a game's storage no longer exists and the games are listed
- **THEN** it is not listed

#### Scenario: The listing cannot disagree with the games

- **WHEN** a game's state changes by any route
- **THEN** the next listing reports the changed state
- **AND** no record of the old state survives to be reported

### Requirement: A Game Can Be Created Over The Served Interface

The system SHALL let the administrator create a game over the served
interface, and SHALL refuse to create one to any other identity. A created
game SHALL be new: a board of the default size, no registered players, and
nothing played.

Creating a game SHALL be refused where a game of that number already exists,
and SHALL leave the existing game untouched.

#### Scenario: The administrator creates a game

- **WHEN** the administrator asks for a new game
- **THEN** the game exists and is listed
- **AND** it has a board of the default size and no registered players

#### Scenario: A player tries to create a game

- **WHEN** an identity that is not the administrator asks for a new game
- **THEN** it is refused
- **AND** no game is created

#### Scenario: A game number already in use

- **WHEN** a game is created with the number of a game that exists
- **THEN** it is refused
- **AND** the existing game is unchanged

#### Scenario: A created game is set up as any other

- **WHEN** a game created this way is set up
- **THEN** its board is resized and its players registered by the same
  commands as a game created any other way

