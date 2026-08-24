## MODIFIED Requirements

### Requirement: Observer Invocation

The system SHALL install the observer as the command `bgcobserver`, and SHALL
launch an observer session bound to one game, as the observer identity 1000 and
not as any player. The observer SHALL identify itself as `bgcobserver` in its
prompt and its usage, whichever path it was invoked by.

The observer SHALL NOT share the administrator's identity. It is entitled to see
the whole game as the administrator is, and entitled to change nothing, and
`player-numbering` states both.

#### Scenario: Starting the observer

- **WHEN** `bgcobserver` is run with a game number
- **THEN** it opens that game with a neutral, unaffiliated view

#### Scenario: The observer is not the administrator

- **WHEN** the observer opens a game
- **THEN** its identity is the observer's and not the administrator's
- **AND** nothing it does is attributed to the administrator

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
