# game-server Specification

## Purpose

The server is the game administrator, player 0. It sets up the board, registers
players, and then runs continuously as the commit authority: waiting for every
player to commit, resolving the turn, publishing results, and waiting again.

## Requirements

### Requirement: Server Invocation

The system SHALL launch the server against one game, acting as player 0.

#### Scenario: Starting the server

- **WHEN** the server is started with a game number
- **THEN** it opens that game as the administrator, player 0

#### Scenario: Missing game number

- **WHEN** the server is started without a game number
- **THEN** it reports the error and exits

### Requirement: Interactive Setup Mode

The system SHALL present an interactive prompt while the game is new, and SHALL
leave that prompt once the game has been committed. When there is no more input
to read, the session SHALL end as though `exit` had been entered, rather than
treating the end of input as a blank line and prompting again.

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
via `add player <number>`.

#### Scenario: Adding a player

- **WHEN** `add player` is given a player number and the game is new
- **THEN** that player is registered with no unit types

#### Scenario: Adding a player to an established game

- **WHEN** `add player` is run after the game has started
- **THEN** the server refuses, reporting that players cannot be added to an existing game

#### Scenario: Wrong argument count

- **WHEN** `add player` is given other than one argument
- **THEN** the server reports that one argument is required

### Requirement: Loading Configuration From Files

The system SHALL let the administrator import board and player configuration
from files via `load board <file>` and `load player <file>`.

#### Scenario: Loading a board

- **WHEN** `load board` names a file containing board dimensions
- **THEN** a board of those dimensions is created

#### Scenario: Loading a player

- **WHEN** `load player` names a file containing a player number, types, and units
- **THEN** that player is registered with those types and units

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

The system SHALL let the administrator inspect the full game state.

#### Scenario: Showing the board

- **WHEN** `show board` is entered
- **THEN** the board is rendered

#### Scenario: Showing types

- **WHEN** `show types` is entered
- **THEN** every player's unit types are listed

#### Scenario: Showing units

- **WHEN** `show units` is entered
- **THEN** the units on the board are listed

#### Scenario: Showing players

- **WHEN** `show players` is entered
- **THEN** the registered players are listed

#### Scenario: Showing pending orders

- **WHEN** `show pending` is entered
- **THEN** the orders queued for the next turn are listed per player

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, or with an unrecognised one
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
