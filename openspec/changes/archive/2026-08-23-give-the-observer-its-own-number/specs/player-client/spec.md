## MODIFIED Requirements

### Requirement: Client Invocation

The system SHALL install the player client as the command `bgcclient`, and
SHALL launch a client session bound to one game and one player. The client SHALL
identify itself as `bgcclient` in its prompt and its usage, whichever path it
was invoked by.

The player number SHALL be one `player-numbering` permits a player: a client
started for a number outside 1 to 999 SHALL be refused before a session is
opened, rather than opened as an identity that can never be a player.

#### Scenario: Starting a client

- **WHEN** `bgcclient` is run with a game number and a player number
- **THEN** it opens that game as that player

#### Scenario: Starting a client for a reserved number

- **WHEN** `bgcclient` is run with the number 0 or the number 1000
- **THEN** it reports that the number is not a player's
- **AND** exits with a failure status without opening the game

#### Scenario: Starting a client for a number out of range

- **WHEN** `bgcclient` is run with a player number below 1 or above 999
- **THEN** it reports the permitted range
- **AND** exits with a failure status without opening the game

#### Scenario: Wrong arguments

- **WHEN** the client is started without both a game number and a player number
- **THEN** it prints usage naming `bgcclient` as the command
- **AND** exits with a failure status

#### Scenario: The prompt names the command

- **WHEN** the client presents its interactive prompt
- **THEN** the prompt is `bgcclient> `

#### Scenario: The prompt does not depend on how the client was launched

- **WHEN** the client is started by command name, by an explicit path, or by
  running its module file
- **THEN** the prompt is `bgcclient> ` in every case
