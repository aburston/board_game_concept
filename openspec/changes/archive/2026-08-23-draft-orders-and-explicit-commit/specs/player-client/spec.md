## ADDED Requirements

### Requirement: Work Survives A Session

The system SHALL restore a player's uncommitted work when they reopen a game,
so that ending a client — deliberately or otherwise — before committing does not
cost them the types they defined, the units they deployed, or the orders they
gave.

What the client shows after reopening SHALL include that work: a unit deployed
before the session ended SHALL be on the board the client draws, and a unit
under orders SHALL be listed with the order it was given, exactly as it was
before.

Where a drafted action can no longer be carried out, the client SHALL tell the
player which action was dropped and why, before taking their next command, and
SHALL continue with the rest of their work restored.

#### Scenario: Reopening after a session ends mid-setup

- **WHEN** a player defines types and deploys units, the client ends without committing, and the player runs it again for the same game
- **THEN** `show types` lists the types they defined
- **AND** `show units` lists the units they deployed, at the squares they placed them
- **AND** the player may deploy more units or commit

#### Scenario: Reopening after a session ends mid-turn

- **WHEN** a player orders a unit to move, the client ends without committing, and the player runs it again for the same game
- **THEN** `show units` lists that unit with the order it was given
- **AND** the player may change the order or commit

#### Scenario: Reopening after committing

- **WHEN** a player commits and then reopens the game
- **THEN** nothing uncommitted is restored
- **AND** the client behaves as it does after any commit

#### Scenario: A restored order that can no longer be carried out

- **WHEN** a player reopens a game and one of their drafted actions is no longer legal
- **THEN** the client reports which action was dropped and why
- **AND** the rest of their work is restored
- **AND** the client takes commands as usual

#### Scenario: Another player's work is not restored

- **WHEN** a player reopens a game while another player holds uncommitted work
- **THEN** nothing of the other player's is shown
- **AND** the board the client draws is what that client was last published, plus its own restored work
