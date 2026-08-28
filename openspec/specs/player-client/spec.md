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

The player number SHALL be one `player-numbering` permits a player: a client
started for a number outside 1 to 999 SHALL be refused before a session is
opened, rather than opened as an identity that can never be a player.

#### Scenario: Starting a client

- **WHEN** `bgcclient` is run with a game number and a player number
- **THEN** it opens that game as that player

#### Scenario: Starting a client for a reserved number

- **WHEN** `bgcclient` is run with the number 0 or the number 1000
- **THEN** it reports that the number is not a player's
- **AND** exits with a failure status without opening the game

#### Scenario: Starting a client for a number out of range

- **WHEN** `bgcclient` is run with a player number below 1 or above 999
- **THEN** it reports the permitted range
- **AND** exits with a failure status without opening the game

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

When the client's input is a terminal, the line SHALL be read with line editing
and completion as `cli-completion` describes them, so a command can be recalled,
edited and completed at the prompt. When it is not a terminal, the line SHALL be
read as it was before completion existed: same prompt, same stream, one line at
a time.

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

#### Scenario: Completing at the prompt

- **WHEN** the client is run in a terminal and completion is asked for
- **THEN** the commands and names the client accepts at that point are offered

#### Scenario: Recalling a command

- **WHEN** the client is run in a terminal and an earlier line of the session is
  recalled at the prompt
- **THEN** it can be edited and entered as a command

#### Scenario: Driven by a pipe

- **WHEN** the client's input is a pipe or a file
- **THEN** it prompts and answers exactly as it did before completion existed
- **AND** its output holds no terminal escape sequence

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

A deployment SHALL also be refused when the named type costs more than the
player has left of their point budget, as `point-budget` describes. The
refusal SHALL name the cost, what the player has left, and their budget, and
SHALL leave the session running and the game unchanged.

#### Scenario: Deploying a unit

- **WHEN** the player runs `add unit` with a known type, a name, and coordinates
- **THEN** a unit of that type is placed at those coordinates for that player
- **AND** the type's cost is spent from the player's budget

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

#### Scenario: Deploying more than the budget can pay for

- **WHEN** `add unit` names a type costing more than the player has left
- **THEN** the client reports the cost, what is left, and the budget
- **AND** no unit is placed and nothing is spent
- **AND** the session continues and accepts further commands
### Requirement: Ordering Movement

The system SHALL let a player order their own units via
`move <unit> <north|south|east|west>`. An order SHALL be resolved against the
units that player owns, so that another player holding a unit of the same name
never affects it. The units listed back after an order SHALL be listed as
`show units` lists them, in the same table and by the same renderer.

#### Scenario: Ordering a move

- **WHEN** the player runs `move` naming one of their units and a valid direction
- **THEN** the order is recorded against that unit
- **AND** the player's units are listed back as a table showing the pending order
- **AND** no storage-internal field is shown

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
visibility, showing nothing the player has not seen. Each subject SHALL be
shown as a table by default and as a JSON document when the command ends in
`json`, both as `cli-output` describes them, and the JSON form SHALL be held to
the same visibility limit as the table.

#### Scenario: Showing the board

- **WHEN** the player runs `show board`
- **THEN** the board is rendered from that player's perspective, with a legend
  of the symbols they can see
- **AND** squares holding units they have not seen are drawn as empty

#### Scenario: Showing the board before one exists

- **WHEN** `show board` is run before a board exists
- **THEN** the client reports that the board must be created first

#### Scenario: Showing types

- **WHEN** the player runs `show types`
- **THEN** the player's own types are listed as a table, together with the types of enemy units they have seen
- **AND** no type of a player they have made no contact with is listed

#### Scenario: Showing units

- **WHEN** the player runs `show units`
- **THEN** the player's own units are listed as a table, together with any enemy units they have seen
- **AND** the player's destroyed units are listed with their state reading destroyed and no position
- **AND** no storage-internal field is shown

#### Scenario: Showing players

- **WHEN** the player runs `show players`
- **THEN** the registered player numbers are listed as a table
- **AND** any player known to be eliminated is marked as such in their status

#### Scenario: Showing a subject as JSON

- **WHEN** the player enters any show subject the client accepts followed by `json`
- **THEN** that subject is written as a single JSON document
- **AND** it holds nothing the table form would have withheld

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, with an unrecognised one, or with
  a trailing word other than `json`
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

### Requirement: Work Survives A Session

The system SHALL restore a player's uncommitted work when they reopen a game,
so that ending a client — deliberately or otherwise — before committing does not
cost them the types they defined, the units they deployed, or the orders they
gave.

What the client shows after reopening SHALL include that work: a unit deployed
before the session ended SHALL be on the board the client draws, and a unit
under orders SHALL be listed with the order it was given, exactly as it was
before.

Where a drafted action can no longer be carried out, the client SHALL tell the
player which action was dropped and why, before taking their next command, and
SHALL continue with the rest of their work restored.

#### Scenario: Reopening after a session ends mid-setup

- **WHEN** a player defines types and deploys units, the client ends without committing, and the player runs it again for the same game
- **THEN** `show types` lists the types they defined
- **AND** `show units` lists the units they deployed, at the squares they placed them
- **AND** the player may deploy more units or commit

#### Scenario: Reopening after a session ends mid-turn

- **WHEN** a player orders a unit to move, the client ends without committing, and the player runs it again for the same game
- **THEN** `show units` lists that unit with the order it was given
- **AND** the player may change the order or commit

#### Scenario: Reopening after committing

- **WHEN** a player commits and then reopens the game
- **THEN** nothing uncommitted is restored
- **AND** the client behaves as it does after any commit

#### Scenario: A restored order that can no longer be carried out

- **WHEN** a player reopens a game and one of their drafted actions is no longer legal
- **THEN** the client reports which action was dropped and why
- **AND** the rest of their work is restored
- **AND** the client takes commands as usual

#### Scenario: Another player's work is not restored

- **WHEN** a player reopens a game while another player holds uncommitted work
- **THEN** nothing of the other player's is shown
- **AND** the board the client draws is what that client was last published, plus its own restored work

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
