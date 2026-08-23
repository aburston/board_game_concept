## MODIFIED Requirements

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
