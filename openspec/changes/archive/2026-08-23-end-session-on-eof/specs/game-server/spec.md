## MODIFIED Requirements

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
