# player-client Specification

## Purpose

The player client is the interactive command-line interface a player uses to
design unit types, deploy units, order movement, and commit a turn. It is
launched per game and per player and shows only what that player is entitled to
see.

## Requirements

### Requirement: Client Invocation

The system SHALL install the player client as the command `bgcclient`, and
SHALL launch a client session bound to one game and one player. The client SHALL
identify itself as `bgcclient` in its prompt and its usage, whichever path it
was invoked by.

#### Scenario: Starting a client

- **WHEN** `bgcclient` is run with a game number and a player number
- **THEN** it opens that game as that player

#### Scenario: Wrong arguments

- **WHEN** the client is started without both a game number and a player number
- **THEN** it prints usage naming `bgcclient` as the command
- **AND** exits with a failure status

#### Scenario: The prompt names the command

- **WHEN** the client presents its interactive prompt
- **THEN** the prompt is `bgcclient> `

#### Scenario: The prompt does not depend on how the client was launched

- **WHEN** the client is started by command name, by an explicit path, or by
  running its module file
- **THEN** the prompt is `bgcclient> ` in every case

### Requirement: Client Command Loop

The system SHALL read commands interactively, ignore blank input, and report
unrecognised commands without ending the session. When there is no more input to
read, the session SHALL end as though `exit` had been entered, rather than
treating the end of input as a blank line and prompting again.

#### Scenario: Blank input

- **WHEN** the player enters a blank line
- **THEN** the client prompts again and takes no action

#### Scenario: Unrecognised command

- **WHEN** the player enters an unrecognised command
- **THEN** the client reports the command as invalid and prompts again

#### Scenario: Help

- **WHEN** the player enters `help`
- **THEN** the client lists the available commands and their arguments

#### Scenario: Exit

- **WHEN** the player enters `exit`
- **THEN** the client session ends

#### Scenario: End of input

- **WHEN** the client's input ends without `exit` being entered
- **THEN** the client session ends with a success status
- **AND** it does not prompt again

### Requirement: Defining Unit Types

The system SHALL let a player define unit types during setup via
`add type <name> <symbol> <attack> <health> <energy>`.

#### Scenario: Defining a type

- **WHEN** the player runs `add type` with a name, symbol, attack, health, and energy
- **THEN** the type is recorded against that player

#### Scenario: Wrong argument count

- **WHEN** `add type` is given other than five arguments
- **THEN** the client reports that five arguments are required and takes no action

#### Scenario: Defining a type after setup

- **WHEN** `add type` is run after the first turn has been resolved
- **THEN** the client refuses, reporting that types cannot be added after the first turn

#### Scenario: Invalid statistics

- **WHEN** `add type` is given statistics outside their permitted ranges
- **THEN** the client reports the error and takes no action

### Requirement: Deploying Units

The system SHALL let a player deploy units during setup via
`add unit <type> <name> <x> <y>`, and SHALL refuse a deployment onto a square
the client already knows is taken, without ending the session.

#### Scenario: Deploying a unit

- **WHEN** the player runs `add unit` with a known type, a name, and coordinates
- **THEN** a unit of that type is placed at those coordinates for that player

#### Scenario: Wrong argument count

- **WHEN** `add unit` is given other than four arguments
- **THEN** the client reports that four arguments are required and takes no action

#### Scenario: No board loaded

- **WHEN** `add unit` is run before a board exists
- **THEN** the client reports that the board must be loaded first

#### Scenario: Deploying after setup

- **WHEN** `add unit` is run after the first turn has been resolved
- **THEN** the client refuses, reporting that units cannot be added after the first turn

#### Scenario: Invalid deployment

- **WHEN** `add unit` names an unknown type, or gives coordinates outside the board, or reuses one of the player's unit names
- **THEN** the client reports the error and takes no action

#### Scenario: Deploying onto a square the player already holds

- **WHEN** `add unit` names coordinates the player has already placed a unit on
- **THEN** the client reports that the square is occupied and takes no action
- **AND** the session continues and accepts further commands

### Requirement: Ordering Movement

The system SHALL let a player order their own units via
`move <unit> <north|south|east|west>`. An order SHALL be resolved against the
units that player owns, so that another player holding a unit of the same name
never affects it.

#### Scenario: Ordering a move

- **WHEN** the player runs `move` naming one of their units and a valid direction
- **THEN** the order is recorded against that unit
- **AND** the player's units are listed back showing the pending order

#### Scenario: A unit name another player also uses

- **WHEN** the player runs `move` naming one of their units, and another player holds a unit of the same name
- **THEN** the order is recorded against the player's own unit
- **AND** the order is not refused

#### Scenario: Wrong argument count

- **WHEN** `move` is given other than two arguments
- **THEN** the client reports that two arguments are required and takes no action

#### Scenario: Moving before the first turn resolves

- **WHEN** `move` is run during setup
- **THEN** the client refuses, reporting that units cannot move until the first turn is complete

#### Scenario: Moving another player's unit

- **WHEN** `move` names a unit the player does not own
- **THEN** the client refuses the order, reporting that no such unit of theirs exists

#### Scenario: Moving a unit not in play

- **WHEN** `move` names a unit of the player's that is not on the board, including one that has been destroyed
- **THEN** the client refuses the order

#### Scenario: Invalid direction

- **WHEN** `move` is given a direction other than north, south, east, or west
- **THEN** the client reports the direction as invalid

### Requirement: Client Display Commands

The system SHALL let a player inspect the game within the limits of their
visibility, showing nothing the player has not seen.

#### Scenario: Showing the board

- **WHEN** the player runs `show board`
- **THEN** the board is rendered from that player's perspective
- **AND** squares holding units they have not seen are drawn as empty

#### Scenario: Showing the board before one exists

- **WHEN** `show board` is run before a board exists
- **THEN** the client reports that the board must be created first

#### Scenario: Showing types

- **WHEN** the player runs `show types`
- **THEN** the player's own types are listed, together with the types of enemy units they have seen
- **AND** no type of a player they have made no contact with is listed

#### Scenario: Showing units

- **WHEN** the player runs `show units`
- **THEN** the player's own units are listed, together with any enemy units they have seen
- **AND** the player's destroyed units are listed marked destroyed and off the board

#### Scenario: Showing players

- **WHEN** the player runs `show players`
- **THEN** the registered player numbers are listed
- **AND** any player known to be eliminated is marked as such

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, or with an unrecognised one
- **THEN** the client reports the command as invalid

### Requirement: Committing A Turn

The system SHALL let a player finalise their turn via `commit`, after which the
client waits for the turn to be resolved.

#### Scenario: Committing

- **WHEN** the player runs `commit` and the save succeeds
- **THEN** the client confirms the commit
- **AND** the client waits for the server to resolve the turn before accepting further orders

#### Scenario: Commit refused

- **WHEN** `commit` is run and the game cannot be saved
- **THEN** the client reports the problem and returns to the prompt

#### Scenario: Reloading after resolution

- **WHEN** the server has resolved the turn
- **THEN** the client reloads the game and resumes accepting orders

### Requirement: Reporting Rejected Orders

The system SHALL show the player everything of theirs the server would not
carry out on the turn it last resolved, before taking their next command. This
SHALL include orders refused while being applied, moves that could not be
carried out while the turn was resolved, and contests of theirs that ended
undecided.

#### Scenario: An order was rejected

- **WHEN** the client starts a session and the server refused one or more of that player's orders on the last resolved turn
- **THEN** the client reports how many were rejected
- **AND** names the unit, its coordinates, and the reason for each

#### Scenario: A move that could not be carried out

- **WHEN** one of the player's moves was not carried out for want of energy, or because it would have left the board
- **THEN** the client reports it with that reason

#### Scenario: A contest that ended undecided

- **WHEN** one of the player's units was in a contest that ended undecided
- **THEN** the client reports it, naming the unit and the square

#### Scenario: Nothing was rejected

- **WHEN** the client starts a session and none of that player's orders were refused
- **THEN** the client reports nothing and prompts as usual

#### Scenario: Rejections describe only the last resolved turn

- **WHEN** a turn is resolved in which none of a player's orders are refused
- **THEN** any rejection from an earlier turn is no longer reported to them

#### Scenario: A destroyed unit is not reported every turn

- **WHEN** turns are resolved after one of the player's units has been destroyed
- **THEN** nothing is reported about that unit on any of them

### Requirement: Reporting The Outcome

The system SHALL tell a player when the game has been decided, or when they
themselves have been eliminated, and SHALL stop taking orders from them in
either case.

#### Scenario: The game was won

- **WHEN** a player opens a session for a game decided in someone's favour
- **THEN** the client reports who won and on which turn
- **AND** refuses movement orders and commits

#### Scenario: The game was drawn

- **WHEN** a player opens a session for a game decided as a draw
- **THEN** the client reports the draw and on which turn
- **AND** refuses movement orders and commits

#### Scenario: The player has been eliminated

- **WHEN** a player opens a session for a game they have been eliminated from and which is not yet decided
- **THEN** the client reports that they are out of the game
- **AND** refuses movement orders and commits
- **AND** the session can still display and exit

#### Scenario: The game is still being played

- **WHEN** a player opens a session for a game that is neither decided nor lost to them
- **THEN** the client reports no outcome and prompts as usual
