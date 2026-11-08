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

#### Scenario: Showing the flags

- **WHEN** the player runs `show flags`
- **THEN** every flag in the game is listed with the player it belongs to and
  the square it is on
- **AND** an enemy flag is listed whether or not that enemy has been met
- **AND** a fallen flag is listed as fallen, with no square

### Requirement: Committing A Turn

The system SHALL let a player commit their setup via `commit`, after which
their setup is fixed and the client shows them the game: the record, if every
player has committed, or that it is waiting for the other players' setups.

#### Scenario: Committing

- **WHEN** the player runs `commit` and the save succeeds
- **THEN** the client confirms the commit
- **AND** if the player's was the last setup outstanding, the game is resolved and the client shows its result and final turn
- **AND** otherwise the client says whose setups are still to come

#### Scenario: Commit refused

- **WHEN** `commit` is run and the game cannot be saved
- **THEN** the client reports the problem and returns to the prompt

#### Scenario: Reloading after resolution

- **WHEN** the game has been resolved since the player committed
- **THEN** the client reloads the game and shows the result and the final turn

#### Scenario: Committing a setup with no flag

- **WHEN** the player runs `commit` during setup and no unit of theirs carries
  the flag
- **THEN** the client reports that a unit must carry the flag
- **AND** returns to the prompt with the setup unchanged

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

The system SHALL show the player, for any turn of the record they read,
everything of theirs the turn would not carry out: orders refused while being
applied, moves that could not be carried out while the turn was resolved, and
contests of theirs that ended undecided. Each SHALL name the unit, its square
and the reason, and SHALL be the player's own unit and nobody else's of the
same name.

#### Scenario: An order was rejected

- **WHEN** the player reads a turn on which one or more of their units' orders were refused
- **THEN** the client reports how many were rejected
- **AND** names the unit, its coordinates, and the reason for each

#### Scenario: A move that could not be carried out

- **WHEN** one of the player's moves was not carried out for want of energy, or because it would have left the board
- **THEN** the client reports it with that reason

#### Scenario: A contest that ended undecided

- **WHEN** one of the player's units was in a contest that ended undecided
- **THEN** the client reports it, naming the unit and the square

#### Scenario: Nothing was rejected

- **WHEN** the player reads a turn on which none of their units' orders were refused
- **THEN** nothing is reported under rejections

#### Scenario: Rejections describe only the last resolved turn

- **WHEN** the player reads a turn of the record
- **THEN** the rejections shown are that turn's alone
- **AND** no earlier turn's rejections are shown with them

#### Scenario: A destroyed unit is not reported every turn

- **WHEN** the player reads turns after one of their units was destroyed
- **THEN** nothing is reported about that unit on any of them

#### Scenario: Another player's unit of the same name

- **WHEN** another player's unit of the same name as one of the player's was in a contest
- **THEN** nothing about it is reported to the player

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

### Requirement: Designating The Flag Carrier

The system SHALL let a player designate which of their units carries their
flag via `set flag <unit>`, during setup, naming a unit of their own. A
designation given after the player has committed their setup SHALL be refused
at the prompt, with the session continuing.

#### Scenario: Designating a unit

- **WHEN** `set flag` names one of the player's own units during setup
- **THEN** that unit carries the flag
- **AND** `show units` marks it as the carrier

#### Scenario: Designating a unit that is not theirs

- **WHEN** `set flag` names a unit the player does not own, or no unit at all
- **THEN** the client refuses, saying which
- **AND** the flag is where it was

#### Scenario: Designating after committing

- **WHEN** `set flag` is run after the player has committed their setup
- **THEN** the client refuses, saying the flag is fixed for the game

#### Scenario: Wrong argument count

- **WHEN** `set flag` is given other than one argument
- **THEN** the client reports that one unit name is required

### Requirement: A Unit Deployed And Not Committed Can Be Taken Back

The system SHALL let a player take back one of their own units while their
setup has not been committed, naming the unit. Taking one back SHALL free the
square it stood on, return the points it cost, and release its name for reuse:
it is the same as never having deployed it. Where the unit carried the
player's flag, the flag SHALL be left carried by nobody, and the setup SHALL
be refused until another unit carries it.

The system SHALL refuse to take back a unit once the player's setup has been
committed: from that point the units are published and playing, and what
happens to them is the game's business rather than the player's. It SHALL
refuse a unit that belongs to another player, and one that does not exist,
saying which.

This is what makes a refused commit something a player can act on: a setup
turned back for clashing with another player's square is fixed by taking the
offending unit back and deploying it elsewhere.

#### Scenario: Taking a unit back

- **WHEN** a player takes back a unit they deployed and have not committed
- **THEN** the unit is gone from their army
- **AND** the square it stood on is free
- **AND** the points it cost are theirs to spend again
- **AND** its name can be used for another unit

#### Scenario: Taking back the flag carrier

- **WHEN** a player takes back the unit carrying their flag
- **THEN** no unit carries their flag
- **AND** their setup cannot be committed until one does

#### Scenario: After the setup is committed

- **WHEN** a player whose setup is committed tries to take a unit back
- **THEN** it is refused, saying the setup is committed

#### Scenario: A unit that is not theirs

- **WHEN** a player tries to take back a unit belonging to another player, or one that does not exist
- **THEN** it is refused, saying no unit of theirs is called that

#### Scenario: It survives the session being reopened

- **WHEN** a player takes a unit back and opens their session again
- **THEN** the unit is still gone

### Requirement: Setting A Type's Program

The system SHALL let a player set the program of one of their own types
during setup via `set program <type> <file>`, reading it from the named file,
and SHALL list it back with `show program <type>` with each line's tick cost.
A program the instruction set refuses SHALL be refused naming the line, with
the type's program unchanged. Setting a program on a type that is not the
player's, or has compute 0, or after the setup is committed, SHALL be refused
saying why.

#### Scenario: Setting a program

- **WHEN** the player runs `set program Runner hunter.asm` during setup and the file holds a legal program
- **THEN** the type `Runner` carries that program
- **AND** the client lists it with the tick cost of each line

#### Scenario: A program with a bad line

- **WHEN** the file holds a line the instruction set does not accept
- **THEN** the client refuses, naming the line
- **AND** the type's program is as it was

#### Scenario: A program on a type with no controller

- **WHEN** the player sets a program on a type with compute 0
- **THEN** the client refuses, saying the type has no controller

#### Scenario: After commit

- **WHEN** the player runs `set program` after committing their setup
- **THEN** the client refuses, saying their setup is committed

#### Scenario: Reading a program back

- **WHEN** the player runs `show program Keep`
- **THEN** the program is listed line by line with each line's ticks and the total of a straight run
- **AND** the listing says the type's compute, how many ticks an energy buys it, and the per-turn cap

### Requirement: Watching The Replay

The system SHALL let a player read the record of a resolved game via
`show turn <n>`, `next` and `prev`, and the board as their army knew it via
`show turn <n> known`. The client SHALL open a resolved game at its final
turn, reporting the result, and SHALL refuse these commands, saying the game
has not been resolved, while any player's setup is uncommitted.

#### Scenario: Reading a turn

- **WHEN** the player runs `show turn 12` on a resolved game
- **THEN** the board after turn 12 is drawn with every unit on it
- **AND** what turn 12 did to the player's units is listed
- **AND** each of the player's controllers' traces for turn 12 is listed

#### Scenario: Stepping through

- **WHEN** the player runs `next` after `show turn 12`
- **THEN** turn 13 is shown
- **AND** `prev` then shows turn 12 again

#### Scenario: What my army knew

- **WHEN** the player runs `show turn 12 known`
- **THEN** the board is drawn from the player's map as it stood after turn 12

#### Scenario: Before the game is resolved

- **WHEN** the player runs `show turn 1` while another player has not committed their setup
- **THEN** the client refuses, saying the game has not been resolved

#### Scenario: Opening a resolved game

- **WHEN** the player opens a game that has been resolved
- **THEN** the client reports the result and shows the final turn
