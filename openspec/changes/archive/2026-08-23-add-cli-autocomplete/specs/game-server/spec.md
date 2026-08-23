## MODIFIED Requirements

### Requirement: Interactive Setup Mode

The system SHALL present an interactive prompt while the game is new, and SHALL
leave that prompt once the game has been committed. When there is no more input
to read, the session SHALL end as though `exit` had been entered, rather than
treating the end of input as a blank line and prompting again.

While that prompt is presented and the server's input is a terminal, the line
SHALL be read with line editing and completion as `cli-completion` describes
them, including completing file paths for `load board` and `load player`. When
the input is not a terminal, the line SHALL be read as it was before completion
existed. The unattended cycle the server runs after setup reads no commands and
is unaffected.

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

#### Scenario: Completing a setup command

- **WHEN** the server is run in a terminal during setup and completion is asked
  for
- **THEN** the setup commands it accepts at that point are offered

#### Scenario: Completing a file to load

- **WHEN** the server is run in a terminal and completion is asked for where
  `load board` or `load player` expects a file
- **THEN** matching paths in the working directory are offered

#### Scenario: The unattended cycle is unaffected

- **WHEN** the server has left setup and is resolving turns
- **THEN** it reads no commands and completion plays no part
