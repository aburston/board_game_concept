# game-server Specification

## Purpose

The server is the game administrator, player 0. It sets up the board, registers
players, and then runs continuously as the commit authority: waiting for every
player to commit, resolving the turn, publishing results, and waiting again.

## Requirements

### Requirement: Server Invocation

The system SHALL install the server as the command `bgcserver`, and SHALL
launch it against one game, acting as player 0. The server SHALL identify itself
as `bgcserver` in its prompt, its usage and its argument errors, whichever path
it was invoked by.

#### Scenario: Starting the server

- **WHEN** `bgcserver` is run with a game number
- **THEN** it opens that game as the administrator, player 0

#### Scenario: Missing game number

- **WHEN** the server is started without a game number
- **THEN** it reports the error, naming `bgcserver` as the command
- **AND** exits with a failure status

#### Scenario: The prompt names the command

- **WHEN** the server presents its interactive prompt
- **THEN** the prompt is `bgcserver> `

#### Scenario: The prompt does not depend on how the server was launched

- **WHEN** the server is started by command name, by an explicit path, or by
  running its module file
- **THEN** the prompt is `bgcserver> ` in every case

### Requirement: Interactive Setup Mode

The system SHALL present an interactive prompt while the game is new, and SHALL
leave that prompt once the game has been committed. When there is no more input
to read, the session SHALL end as though `exit` had been entered, rather than
treating the end of input as a blank line and prompting again.

While that prompt is presented and the server's input is a terminal, the line
SHALL be read with line editing and completion as `cli-completion` describes
them, including completing file paths for `load board` and `load player`. When
the input is not a terminal, the line SHALL be read as it was before completion
existed. The unattended cycle the server runs after setup reads no commands and
is unaffected.

#### Scenario: New game

- **WHEN** the server opens a game that has not yet been set up
- **THEN** it presents an interactive prompt

#### Scenario: Established game

- **WHEN** the server opens a game that has already been set up
- **THEN** it does not present a prompt and runs unattended

#### Scenario: Blank input

- **WHEN** a blank line is entered
- **THEN** the server prompts again and takes no action

#### Scenario: Unrecognised command

- **WHEN** an unrecognised command is entered
- **THEN** the server reports the command as invalid and prompts again

#### Scenario: Help

- **WHEN** `help` is entered
- **THEN** the server lists the available commands and their arguments

#### Scenario: Exit

- **WHEN** `exit` is entered
- **THEN** the server session ends

#### Scenario: End of input

- **WHEN** the server's input ends during setup without `exit` being entered
- **THEN** the server session ends with a success status
- **AND** it does not prompt again

#### Scenario: Completing a setup command

- **WHEN** the server is run in a terminal during setup and completion is asked
  for
- **THEN** the setup commands it accepts at that point are offered

#### Scenario: Completing a file to load

- **WHEN** the server is run in a terminal and completion is asked for where
  `load board` or `load player` expects a file
- **THEN** matching paths in the working directory are offered

#### Scenario: The unattended cycle is unaffected

- **WHEN** the server has left setup and is resolving turns
- **THEN** it reads no commands and completion plays no part

### Requirement: Setting Board Size

The system SHALL let the administrator size the board before the game starts via
`set board <size_x> <size_y>`.

#### Scenario: Setting the size

- **WHEN** `set board` is given two dimensions and no board exists yet
- **THEN** a board of that size is created

#### Scenario: Resizing an existing board

- **WHEN** `set board` is run and a board already exists
- **THEN** the server refuses, reporting that an existing board cannot be resized

#### Scenario: Wrong argument count

- **WHEN** `set board` is given other than two arguments
- **THEN** the server reports that both dimensions are required

#### Scenario: Non-numeric dimensions

- **WHEN** `set board` is given dimensions that are not numbers
- **THEN** the server reports that the dimensions must be numbers

#### Scenario: Dimensions below the minimum

- **WHEN** `set board` is given a dimension below 2
- **THEN** the server reports that the dimension must be greater than 1

#### Scenario: Only the administrator may size the board

- **WHEN** `set board` is run by anyone other than player 0
- **THEN** the server refuses

### Requirement: Registering Players

The system SHALL let the administrator register players before the game starts
via `add player <number>`. The number SHALL be one `player-numbering` permits a
player, and one that is not SHALL be refused at the prompt — reported, with the
session continuing — rather than ending the session.

#### Scenario: Adding a player

- **WHEN** `add player` is given a player number and the game is new
- **THEN** that player is registered with no unit types

#### Scenario: Adding a player with a reserved number

- **WHEN** `add player` is given 0 or 1000
- **THEN** the server refuses, reporting that the number is reserved
- **AND** no player is registered
- **AND** the server takes further commands

#### Scenario: Adding a player with a number out of range

- **WHEN** `add player` is given a number below 1 or above 999
- **THEN** the server refuses, naming the permitted range
- **AND** no player is registered
- **AND** the server takes further commands

#### Scenario: Adding a player to an established game

- **WHEN** `add player` is run after the game has started
- **THEN** the server refuses, reporting that players cannot be added to an existing game

#### Scenario: Wrong argument count

- **WHEN** `add player` is given other than one argument
- **THEN** the server reports that one argument is required

### Requirement: Loading Configuration From Files

The system SHALL let the administrator import board and player configuration
from files via `load board <file>` and `load player <file>`. A player file
naming a number `player-numbering` does not permit a player SHALL be refused at
the prompt, with the session continuing.

#### Scenario: Loading a board

- **WHEN** `load board` names a file containing board dimensions
- **THEN** a board of those dimensions is created

#### Scenario: Loading a player

- **WHEN** `load player` names a file containing a player number, types, and units
- **THEN** that player is registered with those types and units

#### Scenario: Loading a player whose number is not a player's

- **WHEN** `load player` names a file whose player number is outside 1 to 999
- **THEN** the server refuses, naming the permitted range
- **AND** no player is registered
- **AND** the server returns to the prompt

#### Scenario: Loading a player into an established game

- **WHEN** `load player` is run after the game has started
- **THEN** the server refuses, reporting that players cannot be added to an existing game

#### Scenario: Unreadable file

- **WHEN** `load board` or `load player` names a file that cannot be read or parsed
- **THEN** the server reports the error and returns to the prompt

#### Scenario: Wrong argument count

- **WHEN** `load board` or `load player` is given other than one argument
- **THEN** the server reports that one argument is required

### Requirement: Server Display Commands

The system SHALL let the administrator inspect the full game state. Each
subject SHALL be shown as a table by default and as a JSON document when the
command ends in `json`, both as `cli-output` describes them.

#### Scenario: Showing the board

- **WHEN** `show board` is entered
- **THEN** the board is rendered, with a legend of the symbols on it

#### Scenario: Showing types

- **WHEN** `show types` is entered
- **THEN** every player's unit types are listed as a table

#### Scenario: Showing units

- **WHEN** `show units` is entered
- **THEN** the units on the board are listed as a table
- **AND** no storage-internal field is shown

#### Scenario: Showing players

- **WHEN** `show players` is entered
- **THEN** the registered players are listed as a table, each with their status

#### Scenario: Showing pending orders

- **WHEN** `show pending` is entered
- **THEN** the orders queued for the next turn are listed as a table, one row
  per ordered unit, naming the player who gave each order

#### Scenario: Showing a subject as JSON

- **WHEN** any show subject the server accepts is entered followed by `json`
- **THEN** that subject is written as a single JSON document

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, with an unrecognised one, or with
  a trailing word other than `json`
- **THEN** the server reports the command as invalid

### Requirement: Committing Setup

The system SHALL let the administrator end setup via `commit`, writing the game
to disk and leaving interactive mode.

#### Scenario: Committing setup

- **WHEN** `commit` is entered and the game saves successfully
- **THEN** the server confirms the commit and leaves interactive mode

#### Scenario: Commit refused

- **WHEN** `commit` is entered and the game cannot be saved
- **THEN** the server reports the problem and returns to the prompt

### Requirement: Setup Survives A Session

The system SHALL restore the administrator's uncommitted setup when the server
is run again for the same game, so that ending the session before committing
setup does not cost the board that was sized or the players that were
registered.

Where a restored setup action can no longer be carried out, the server SHALL
report which action was dropped and why, before taking its next command, and
SHALL continue with the rest of the setup restored. A configuration loaded from
a file SHALL be restored by reading that file again; if it can no longer be
read, that is a dropped action like any other and SHALL NOT prevent the game
from being opened.

#### Scenario: Reopening after a session ends during setup

- **WHEN** the administrator sets a board size and registers players, the session ends without committing, and the server is run again for the same game
- **THEN** `show board` shows the board at the size that was set
- **AND** `show players` lists the players that were registered
- **AND** the administrator may register more players or commit setup

#### Scenario: Reopening after committing setup

- **WHEN** the administrator commits setup and the server is run again
- **THEN** nothing uncommitted is restored
- **AND** the server resumes its unattended turn cycle

#### Scenario: A loaded file that has since gone

- **WHEN** setup is restored and a file a `load` command named can no longer be read
- **THEN** the server reports that the command was dropped and why
- **AND** the rest of the setup is restored
- **AND** the administrator may reissue the command

### Requirement: Unattended Turn Cycle

The system SHALL run continuously once setup is complete, resolving each turn as
soon as every player still in the game has committed, and SHALL stop once the
game is decided rather than waiting for commits that will never come.

#### Scenario: The turn loop

- **WHEN** the server is running unattended
- **THEN** it waits for every player still in the game to commit
- **AND** resolves the turn
- **AND** writes the resulting board, units, turn number, and per-player views to disk
- **AND** logs the board and units before waiting again

#### Scenario: A turn decides the game

- **WHEN** the server resolves a turn that leaves at most one player not eliminated
- **THEN** it writes the outcome with the game
- **AND** reports the winner, or the draw, and the deciding turn number
- **AND** ends its turn cycle without waiting for further commits
- **AND** exits with a success status

#### Scenario: Starting against a game already decided

- **WHEN** the server is started against a game whose outcome has already been written
- **THEN** it reports the outcome and exits without resolving a turn

#### Scenario: Save failure during the cycle

- **WHEN** the server cannot save game state while resolving a turn
- **THEN** it reports an internal error and exits with a failure status
