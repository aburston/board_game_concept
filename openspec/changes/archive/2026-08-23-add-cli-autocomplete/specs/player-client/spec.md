## MODIFIED Requirements

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
