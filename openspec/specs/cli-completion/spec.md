# cli-completion Specification

## Purpose

What completes while a command is being typed, and where the candidates come
from. Completion offers a role only what that role may run, reads the game the
session already holds rather than the disk, and changes nothing. It is a help
with typing and nothing more: what a command means, and whether it may be
carried out, are still the parser's and the service layer's to say. This also
covers completing the arguments the three commands are launched with, in the
shell.

## Requirements

### Requirement: Completion In An Interactive Session

When a role's input is a terminal, the system SHALL let the person at the
prompt complete what they are typing, by pressing the completion key their
terminal binds to it, conventionally Tab. Completion SHALL offer only what
would be a valid continuation of the line already typed, and SHALL leave the
line unchanged when nothing matches.

Where exactly one candidate matches what has been typed, the system SHALL
complete the word. Where several match, it SHALL complete as far as they agree
and list them.

#### Scenario: Completing a command word

- **WHEN** a player has typed the first letters of a command and asks for
  completion
- **THEN** the word is completed if only one command starts that way
- **AND** the candidates are listed if more than one does

#### Scenario: Nothing matches

- **WHEN** completion is asked for and no valid continuation starts with what
  has been typed
- **THEN** the line is left exactly as it was
- **AND** the session prints no error and takes no action

#### Scenario: Completion is not a command

- **WHEN** completion is asked for
- **THEN** no command is run, nothing is printed as a command's output, and the
  session is still waiting for the same line

### Requirement: Candidates Come From The Grammar

Completion candidates SHALL be derived from the same description of the
grammar that `help` is generated from and that the parser works to. A command
added to that description SHALL become completable without a second list of
words being maintained anywhere.

#### Scenario: A new command completes without being listed twice

- **WHEN** a command is added to the shared grammar description
- **THEN** it is offered by completion
- **AND** no separate table of completable words had to be edited

#### Scenario: Completion and help agree

- **WHEN** a role completes the empty line
- **THEN** the words offered are the commands that role's `help` lists

### Requirement: Completion Is Limited By Role

Completion SHALL offer a role only what that role is allowed to run. A command
its role would refuse SHALL NOT be offered, and neither SHALL a `show` subject
that role may not ask for. The limit SHALL be read from the same table that
refuses a command once it is entered.

#### Scenario: A command the role does not have

- **WHEN** the observer completes at the start of a line
- **THEN** `move`, `add` and `commit` are not among the candidates

#### Scenario: A show subject the role does not have

- **WHEN** a player completes after `show `
- **THEN** the subjects that player's client accepts are offered
- **AND** `pending`, which it does not accept, is not

#### Scenario: The offer matches the refusal

- **WHEN** any role is offered a word by completion
- **THEN** entering the command that word forms is not refused as a command
  that role may not run

### Requirement: Completing Words Of The Language

The system SHALL complete every fixed word of the grammar at the position it
may be typed: the verbs at the start of a line; `board`, `types`, `units`,
`players` and `pending` after `show`; the optional `json` after a `show`
subject; `board` after `set`; `player`, `type` and `unit` after `add`; `board`
and `player` after `load`; and `north`, `east`, `south` and `west` where a
direction is expected.

#### Scenario: Completing a show subject

- **WHEN** a role completes after `show `
- **THEN** the show subjects it may ask for are offered

#### Scenario: Completing the JSON form

- **WHEN** a role completes after a complete `show` subject
- **THEN** `json` is offered

#### Scenario: Completing a direction

- **WHEN** a player completes where `move` expects a direction
- **THEN** `north`, `east`, `south` and `west` are offered

#### Scenario: Nothing is offered where the grammar takes a number

- **WHEN** completion is asked for where the grammar expects a number, such as
  a coordinate or a statistic
- **THEN** no candidate is offered and the line is left as it was

#### Scenario: Nothing is offered where a new name is being invented

- **WHEN** completion is asked for where the grammar expects a name for
  something that does not exist yet, such as the name of a type being defined
- **THEN** no candidate is offered

#### Scenario: A command that takes no arguments

- **WHEN** completion is asked for after a complete command that takes no
  arguments, such as `commit`
- **THEN** no candidate is offered

### Requirement: Completing Names From The Game

Where the grammar expects the name of something the game already holds, the
system SHALL offer the names the session can see, read from the game the
session already has in memory.

`move` SHALL offer the names of the asking player's own units that are still in
play. `add unit` SHALL offer the names of the unit types that player has
defined. A name the player could not act on SHALL NOT be offered: another
player's unit, a destroyed unit, and another player's type are all absent.

#### Scenario: Completing a unit to order

- **WHEN** a player completes where `move` expects a unit
- **THEN** the names of their own units in play are offered

#### Scenario: A unit deployed this session

- **WHEN** a player deploys a unit and then completes where `move` expects a
  unit
- **THEN** the unit just deployed is among the names offered
- **AND** the game was not re-read from disk to find it

#### Scenario: Another player's unit of the same name

- **WHEN** a player completes where `move` expects a unit, and another player
  holds a unit whose name starts the same way
- **THEN** only the asking player's own unit is offered

#### Scenario: A destroyed unit

- **WHEN** a player completes where `move` expects a unit and one of their units
  has been destroyed
- **THEN** the destroyed unit is not offered

#### Scenario: Completing a type to deploy

- **WHEN** a player completes where `add unit` expects a type
- **THEN** the names of the types that player has defined are offered
- **AND** no type belonging to another player is offered

#### Scenario: Nothing to offer yet

- **WHEN** a player completes where a unit or a type is expected and they have
  defined none
- **THEN** no candidate is offered and the line is left as it was

### Requirement: Completing File Paths

Where the grammar expects a file, the system SHALL complete paths against the
working directory the role was started in, offering files and directories as a
shell does, so that `load board` and `load player` can be typed without the
path being remembered in full.

#### Scenario: Completing a file to load

- **WHEN** the server completes where `load board` expects a file
- **THEN** matching names in the working directory are offered

#### Scenario: Completing inside a directory

- **WHEN** a partial path naming a directory is completed
- **THEN** the entries of that directory are offered

#### Scenario: A path is one word

- **WHEN** a path being completed contains a separator
- **THEN** the whole path is treated as the one word being completed, not as
  several

### Requirement: Completion Reads And Never Writes

Completing SHALL NOT change the game or the session: it SHALL NOT load, save,
reload, commit, order, deploy or define anything, and SHALL NOT re-read the
game from disk. It SHALL answer only from what the session already holds and
from the working directory it is asked about.

#### Scenario: Completion leaves the game alone

- **WHEN** completion is asked for repeatedly during a session
- **THEN** nothing is written to the game directory
- **AND** the next command behaves as though completion had never been asked
  for

#### Scenario: Completion does not reload

- **WHEN** completion is asked for
- **THEN** the game is not read again from disk

### Requirement: Non-Interactive Input Is Unaffected

When a role's input is not a terminal, the system SHALL read commands exactly
as it does without this capability: the same prompt on the same stream, one
line taken at a time, end of input ending the session as `exit` does. No
completion SHALL be attempted, and no line editing, escape sequence or
redrawn prompt SHALL appear in the output.

#### Scenario: A role driven by a pipe

- **WHEN** a role is run with its input coming from a pipe or a file
- **THEN** it prompts and answers exactly as it did before completion existed
- **AND** its output holds no terminal escape sequence

#### Scenario: End of piped input

- **WHEN** the input of a role reading from a pipe runs out without `exit`
- **THEN** the session ends with a success status and does not prompt again

#### Scenario: A transcript stays readable

- **WHEN** the output of a piped session is captured
- **THEN** each command's output appears between two prompts, as it does today

### Requirement: Sessions Run Without Line Editing Support

Where the line editing library is unavailable, the system SHALL run the session
anyway, without completion, and SHALL NOT fail, warn or exit because of it.

#### Scenario: No line editing available

- **WHEN** a role starts on a system where the line editing library cannot be
  loaded
- **THEN** the session starts and accepts commands as usual
- **AND** completion does nothing
- **AND** nothing is printed about the missing library

### Requirement: Shell Completion For Launching A Role

The system SHALL provide bash and zsh completion for the three commands, so
that the arguments a role is launched with can be completed by the shell.

`bgcclient` SHALL complete a game number as its first argument and a player
number registered in that game as its second. `bgcobserver` SHALL complete a
game number. `bgcserver` SHALL complete its options and a game number after
`-g` or `--game-number`. Game numbers SHALL be the games found beneath the
working directory, which is where a role resolves a game from.

The completion SHALL be provided as files to source, documented where the
commands are documented. Installing the package SHALL NOT put any command on
the path other than the three roles.

#### Scenario: Completing a game number

- **WHEN** the completion is sourced and `bgcclient` is completed for its first
  argument in a directory holding games
- **THEN** the game numbers of those games are offered
- **AND** the storage prefix the directories are named with is not part of what
  is offered

#### Scenario: Completing a player number

- **WHEN** `bgcclient` is completed for its second argument after a game number
- **THEN** the player numbers registered in that game are offered

#### Scenario: Completing a server option

- **WHEN** `bgcserver` is completed after `-g`
- **THEN** game numbers are offered

#### Scenario: No games to offer

- **WHEN** a role's arguments are completed in a directory holding no games
- **THEN** nothing is offered and the command line is left as it was

#### Scenario: Completion adds no command

- **WHEN** the package is installed
- **THEN** the commands on the path are the three roles and nothing else
