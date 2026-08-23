# game-observer Specification

## Purpose

The observer is a read-only, neutral view of a game. It belongs to no player and
issues no orders; it exists so a game can be watched or reviewed without
influencing it.

## Requirements

### Requirement: Observer Invocation

The system SHALL install the observer as the command `bgcobserver`, and SHALL
launch an observer session bound to one game, with no player affiliation. The
observer SHALL identify itself as `bgcobserver` in its prompt and its usage,
whichever path it was invoked by.

#### Scenario: Starting the observer

- **WHEN** `bgcobserver` is run with a game number
- **THEN** it opens that game with a neutral, unaffiliated view

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

### Requirement: Observer Display Commands

The system SHALL let the observer inspect the full game state.

#### Scenario: Showing the board

- **WHEN** `show board` is entered
- **THEN** the board is rendered

#### Scenario: Showing the board before one exists

- **WHEN** `show board` is entered before a board exists
- **THEN** the observer reports that the board must be created first

#### Scenario: Showing types

- **WHEN** `show types` is entered
- **THEN** every player's unit types are listed

#### Scenario: Showing units

- **WHEN** `show units` is entered
- **THEN** the units on the board are listed

#### Scenario: Showing players

- **WHEN** `show players` is entered
- **THEN** the registered player numbers are listed

#### Scenario: Showing pending orders

- **WHEN** `show pending` is entered
- **THEN** the orders queued for the next turn are listed per player

#### Scenario: Incomplete show command

- **WHEN** `show` is given without a subject, or with an unrecognised one
- **THEN** the observer reports the command as invalid

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
