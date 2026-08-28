## ADDED Requirements

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

## MODIFIED Requirements

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

#### Scenario: Committing a setup with no flag

- **WHEN** the player runs `commit` during setup and no unit of theirs carries
  the flag
- **THEN** the client reports that a unit must carry the flag
- **AND** returns to the prompt with the setup unchanged
