## MODIFIED Requirements

### Requirement: Server Invocation

The system SHALL install the server as the command `bgcserver`, and SHALL
launch it against one game, acting as player 0. The server SHALL identify itself
as `bgcserver` in its prompt, its usage and its argument errors, whichever path
it was invoked by.

#### Scenario: Starting the server

- **WHEN** `bgcserver` is run with a game number
- **THEN** it opens that game as the administrator, player 0

#### Scenario: Missing game number

- **WHEN** the server is started without a game number
- **THEN** it reports the error, naming `bgcserver` as the command
- **AND** exits with a failure status

#### Scenario: The prompt names the command

- **WHEN** the server presents its interactive prompt
- **THEN** the prompt is `bgcserver> `

#### Scenario: The prompt does not depend on how the server was launched

- **WHEN** the server is started by command name, by an explicit path, or by
  running its module file
- **THEN** the prompt is `bgcserver> ` in every case
