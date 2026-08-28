## ADDED Requirements

### Requirement: The Flag Is Designated In The Armoury

The system SHALL let a player choose which of their deployed units carries
their flag while they are setting up, SHALL show which one currently does, and
SHALL NOT offer the choice once the setup is committed.

Where a player has deployed units and designated none, the interface SHALL say
that a carrier is needed before the setup can be committed, before the commit
is attempted rather than after.

#### Scenario: Choosing a carrier

- **WHEN** a player chooses one of their deployed units during setup
- **THEN** that unit is shown as carrying the flag

#### Scenario: Changing the choice

- **WHEN** a player chooses a different unit before committing
- **THEN** only the second is shown as carrying it

#### Scenario: Committing without one

- **WHEN** a player has deployed units and designated no carrier
- **THEN** the interface says a carrier is needed
- **AND** does not offer to commit the setup

#### Scenario: After committing

- **WHEN** the setup is committed
- **THEN** the carrier is shown and cannot be changed

### Requirement: Every Flag Is Drawn On The Board

The system SHALL draw every flag in the game on the square it stands on,
whoever it belongs to and whether or not its carrier has been met, and SHALL
say in the roster which unit carries the player's own flag.

A flag drawn for a carrier the seat has not met SHALL show the square and the
owner and nothing else: no symbol, no type and no statistics.

#### Scenario: An enemy flag out of contact

- **WHEN** an enemy flag stands on a square the seat cannot otherwise see
- **THEN** the square is drawn with a flag mark naming the player it belongs to
- **AND** no unit, type or statistics are drawn for it

#### Scenario: The seat's own flag

- **WHEN** the seat's own units are listed
- **THEN** the one carrying the flag is marked as the carrier

#### Scenario: A flag that has fallen

- **WHEN** a flag carrier has been destroyed
- **THEN** no flag is drawn on any square for that player

### Requirement: An Eliminated Player Is Told They Are Out

The system SHALL tell a player whose flag has fallen that they are out of the
game, SHALL stop offering orders and commits, and SHALL keep showing them the
board and what the turns do.

#### Scenario: Losing the flag

- **WHEN** the turn that destroys a player's flag carrier resolves
- **THEN** that player is told they are out, and why
- **AND** no order or commit is offered

#### Scenario: Watching afterwards

- **WHEN** an eliminated player stays on the screen
- **THEN** the board and the account of each turn keep arriving
