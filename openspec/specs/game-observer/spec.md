# game-observer Specification

## Purpose

The observer is a read-only, neutral view of a game. It belongs to no player and
issues no orders; it exists so a game can be watched or reviewed without
influencing it.

## Requirements

### Requirement: Observer Invocation

The system SHALL install the observer as the command `bgcobserver`, and SHALL
launch an observer session bound to one game, as the observer identity 1000 and
not as any player. The observer SHALL identify itself as `bgcobserver` in its
prompt and its usage, whichever path it was invoked by.

The observer SHALL NOT share the administrator's identity. It is entitled to see
the whole game as the administrator is, and entitled to change nothing, and
`player-numbering` states both.

#### Scenario: Starting the observer

- **WHEN** `bgcobserver` is run with a game number
- **THEN** it opens that game with a neutral, unaffiliated view

#### Scenario: The observer is not the administrator

- **WHEN** the observer opens a game
- **THEN** its identity is the observer's and not the administrator's
- **AND** nothing it does is attributed to the administrator

#### Scenario: Wrong arguments

- **WHEN** the observer is started without exactly one game number
- **THEN** it prints usage naming `bgcobserver` as the command
- **AND** exits with a failure status

#### Scenario: The prompt names the command

- **WHEN** the observer presents its interactive prompt
- **THEN** the prompt is `bgcobserver> `

#### Scenario: The prompt does not depend on how the observer was launched

- **WHEN** the observer is started by command name, by an explicit path, or by
  running its module file
- **THEN** the prompt is `bgcobserver> ` in every case

### Requirement: Observer Is Read-Only

The system SHALL offer the observer no command that alters game state.

#### Scenario: No mutating commands

- **WHEN** the observer session is used
- **THEN** it can display state and reload, and can neither define types, deploy units, order movement, nor commit

### Requirement: Observer Command Loop

The system SHALL read commands interactively, ignore blank input, and report
unrecognised commands without ending the session. When there is no more input to
read, the session SHALL end as though `exit` had been entered, rather than
treating the end of input as a blank line and prompting again.

When the observer's input is a terminal, the line SHALL be read with line
editing and completion as `cli-completion` describes them, offering only the
read-only commands the observer holds. When it is not a terminal, the line SHALL
be read as it was before completion existed.

#### Scenario: Blank input

- **WHEN** a blank line is entered
- **THEN** the observer prompts again and takes no action

#### Scenario: Unrecognised command

- **WHEN** an unrecognised command is entered
- **THEN** the observer reports the command as invalid and prompts again

#### Scenario: Help

- **WHEN** `help` is entered
- **THEN** the observer lists the available commands

#### Scenario: Exit

- **WHEN** `exit` is entered
- **THEN** the observer session ends

#### Scenario: End of input

- **WHEN** the observer's input ends without `exit` being entered
- **THEN** the observer session ends with a success status
- **AND** it does not prompt again

#### Scenario: Completing at the prompt

- **WHEN** the observer is run in a terminal and completion is asked for at the
  start of a line
- **THEN** only its read-only commands are offered
- **AND** no command that would change the game is among them

#### Scenario: Driven by a pipe

- **WHEN** the observer's input is a pipe or a file
- **THEN** it prompts and answers exactly as it did before completion existed

### Requirement: Observer Display Commands

The system SHALL let the observer inspect the full game state. Each subject
SHALL be shown as a table by default and as a JSON document when the command
ends in `json`, both as `cli-output` describes them.

#### Scenario: Showing the board

- **WHEN** `show board` is entered
- **THEN** the board is rendered, with a legend of the symbols on it

#### Scenario: Showing the board before one exists

- **WHEN** `show board` is entered before a board exists
- **THEN** the observer reports that the board must be created first

#### Scenario: Showing types

- **WHEN** `show types` is entered
- **THEN** every player's unit types are listed as a table

#### Scenario: Showing units

- **WHEN** `show units` is entered
- **THEN** the units on the board are listed as a table
- **AND** no storage-internal field is shown

#### Scenario: Showing players

- **WHEN** `show players` is entered
- **THEN** the registered player numbers are listed as a table, each with their
  status

#### Scenario: Showing pending orders

- **WHEN** `show pending` is entered
- **THEN** the orders queued for the next turn are listed as a table, one row
  per ordered unit, naming the player who gave each order

#### Scenario: Showing a subject as JSON

- **WHEN** any show subject the observer accepts is entered followed by `json`
- **THEN** that subject is written as a single JSON document

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, with an unrecognised one, or with
  a trailing word other than `json`
- **THEN** the observer reports the command as invalid

#### Scenario: Showing the flags

- **WHEN** the observer runs `show flags`
- **THEN** every player's flag is listed with its owner and its square
### Requirement: Refreshing The View

The system SHALL let the observer reload the game from disk to pick up turns
resolved since the session started.

#### Scenario: Reloading

- **WHEN** `reload` is entered
- **THEN** the observer re-reads the game from disk and resumes at the prompt

### Requirement: Observing A Decided Game

The system SHALL let the observer see how far a game has got and how it ended,
reporting the turn number it is showing and, once the game is decided, the
winner or the draw.

#### Scenario: Opening a decided game

- **WHEN** the observer opens a game whose outcome has been written
- **THEN** it reports the winner, or the draw, and the deciding turn number
- **AND** it can still display the final board and units

#### Scenario: Opening a game still being played

- **WHEN** the observer opens a game that is not yet decided
- **THEN** it reports no outcome
- **AND** reports the number of the last turn resolved

#### Scenario: Reloading onto a decided game

- **WHEN** `reload` is entered and the game has been decided since the session started
- **THEN** the observer reports the outcome after reloading

#### Scenario: The observer never orders

- **WHEN** a game is decided
- **THEN** the observer's read-only command surface is unchanged
