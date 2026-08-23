## MODIFIED Requirements

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
