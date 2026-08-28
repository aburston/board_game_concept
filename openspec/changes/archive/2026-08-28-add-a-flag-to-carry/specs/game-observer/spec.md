## MODIFIED Requirements

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
