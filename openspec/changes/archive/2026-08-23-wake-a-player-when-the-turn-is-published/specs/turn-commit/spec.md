## MODIFIED Requirements

### Requirement: Players Wait For Turn Completion

The system SHALL prevent a player from issuing new orders while their previous
commit is still awaiting resolution. A player SHALL be held until the turn they
committed to has been published — until everything that turn produced, and in
particular the view they will be shown, can be read — and not merely until the
server has taken their orders. A player released from that wait SHALL be able to
read the result of the turn they were waiting for.

#### Scenario: Player blocked after committing

- **WHEN** a player has committed and the turn has not yet been resolved
- **THEN** the client reports that it is waiting for the turn to complete
- **AND** the client reloads game data and retries rather than accepting new orders

#### Scenario: A released player can read the turn they waited for

- **WHEN** a player stops waiting because the turn they committed to has been resolved
- **THEN** the view they are shown is the one that turn published
- **AND** it holds the units that turn left them, rather than the previous turn's

#### Scenario: Taking a player's orders is not the same as publishing the turn

- **WHEN** the server has consumed a player's orders but has not yet published everything the turn produced
- **THEN** that player is still held
- **AND** is not offered the chance to give orders against a turn that has not been published
