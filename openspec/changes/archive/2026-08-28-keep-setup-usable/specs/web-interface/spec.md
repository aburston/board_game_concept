## ADDED Requirements

### Requirement: A Half-Made Choice Survives A Redraw

The interface draws every screen again from one state object whenever anything
changes, so a choice held only in the page is thrown away by work done beside
it. The system SHALL keep a choice that is still being used where a redraw
cannot lose it, so that using one form does not empty another.

The type a unit is being deployed from SHALL be kept as it was left, so that
several units of one type can be placed without choosing it again for each.

A board size that has been typed and not yet sent SHALL be kept while seats are
registered and removed, and SHALL go back to reading the board once a size has
been accepted.

#### Scenario: Deploying several units of one type

- **WHEN** a unit is deployed and the screen is drawn again
- **THEN** the chooser still names the type that was deployed
- **AND** the next square deploys another unit of it

#### Scenario: A type that is no longer offered

- **WHEN** the chooser was left on a type the seat no longer has
- **THEN** it falls back to the first type offered

#### Scenario: Registering a seat with a size half-typed

- **WHEN** a width and height are typed and a seat is registered or removed before they are sent
- **THEN** the width and height are still as they were typed

#### Scenario: A size that has been accepted

- **WHEN** a board size is sent and accepted
- **THEN** the fields show the size the board now is

## MODIFIED Requirements

### Requirement: A Committed Setup Is Shown As Committed

The system SHALL show a player who has committed a setup what they committed,
where they committed it, and that it takes the field when the first turn
resolves.

Until that turn resolves the army is published orders and stands on no board,
so a screen drawn from the board alone shows a player nothing of theirs and
reads as work lost.

A seat that has committed SHALL be taken to the board rather than to the
armoury, and the armoury SHALL NOT offer to design or deploy for a seat whose
setup is committed. This SHALL hold once the turn has resolved as well as
before it: a seat whose army was published and then destroyed has no setup
left to do, and offering it the forms invites commands that are all refused.

#### Scenario: The board before the first turn

- **WHEN** a player has committed a setup and the first turn has not resolved
- **THEN** the units they committed are shown where they deployed them
- **AND** they are shown as not yet on the board
- **AND** the screen says the first turn is what puts them there

#### Scenario: Coming back from the lobby

- **WHEN** a player who has committed a setup opens their seat from the lobby
- **THEN** they are taken to the board

#### Scenario: The armoury after committing

- **WHEN** a player who has committed a setup reaches the armoury
- **THEN** it says the setup is committed and offers no design or deployment

#### Scenario: The armoury after the setup turn has resolved

- **WHEN** a player whose setup has been resolved reaches the armoury
- **THEN** it says the setup is over and offers no design or deployment
- **AND** it sends them to the board

#### Scenario: Who is being waited for

- **WHEN** a player has committed a setup and another seat has not
- **THEN** the seats still to commit a setup are named
