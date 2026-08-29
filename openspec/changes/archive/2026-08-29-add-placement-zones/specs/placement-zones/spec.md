## ADDED Requirements

### Requirement: Two Players Deploy On Their Own Half

During setup, when a game has exactly two players, the system SHALL restrict
each player's deployments to one half of the board, split by rows into a top
half and a bottom half. The player with the lower number SHALL deploy only in
the top half — the rows nearer row 0 — and the higher-numbered player only in
the bottom half. Columns SHALL NOT be restricted: a player's half is the full
width of the board.

The split SHALL be a pure function of the board size and the two player
numbers, so a game reloaded from storage answers the same halves it answered
before, and nothing about who deploys where depends on the order units happen
to be held in.

#### Scenario: The lower-numbered player deploys in the top half

- **WHEN** a game has two players and the lower-numbered player deploys a unit in a top-half row
- **THEN** the deployment is allowed

#### Scenario: A player deploys outside their half

- **WHEN** a player in a two-player game deploys a unit in a row belonging to the other half
- **THEN** the deployment is refused
- **AND** the board is left as it was

#### Scenario: Which half is whose does not depend on the numbers used

- **WHEN** the two players are numbered other than 1 and 2
- **THEN** the lower of the two numbers deploys in the top half and the higher in the bottom half

### Requirement: An Odd Row Count Leaves A Neutral Middle Row

When a two-player game's board has an odd number of rows, the system SHALL make
the single middle row neutral: neither player may deploy in it, and it belongs
to neither half. When the number of rows is even, there SHALL be no neutral row
and the two halves SHALL meet.

#### Scenario: The middle row is neutral

- **WHEN** a two-player board has an odd number of rows and either player deploys a unit in the middle row
- **THEN** the deployment is refused

#### Scenario: An even row count has no neutral row

- **WHEN** a two-player board has an even number of rows
- **THEN** every row belongs to one half or the other
- **AND** no row is neutral

### Requirement: Only A Two-Player Game Is Restricted

The system SHALL restrict placement only when the game has exactly two players.
With one player, or with three or more, the whole board SHALL be open for
placement and no row SHALL be neutral.

A game that is not two-player SHALL be the null case of the same rule, not a
path around it: the whole board being open is what the rule returns when the
player count is not two, reached through the same calls — the same allowed
area computed, the same view published, the same refusal check made — as a
two-player game. The observable behaviour of a game that is not two-player
SHALL therefore be exactly what it was before this rule existed: every square
open, nothing greyed, no deployment refused for where it is.

#### Scenario: A single-player game is unrestricted

- **WHEN** a game has one player
- **THEN** that player may deploy on any square of the board

#### Scenario: A three-player game is unrestricted

- **WHEN** a game has three or more players
- **THEN** every player may deploy on any square of the board

#### Scenario: The behaviour of a non-two-player game is unchanged

- **WHEN** any deployment is made in a game that is not two-player
- **THEN** it is allowed exactly where it was allowed before this rule, and
  refused only where it was refused before — never for being outside an area

### Requirement: The Placement Area Is Published Per Seat

The system SHALL publish, for a seat, the area of the board in which that seat
may deploy during setup, so that a client can show the limit without knowing
the rule that produced it. The area published to a seat SHALL be the same area
the system enforces for that seat: the seat's half in a two-player game, less
any neutral row, and the whole board otherwise. A session entitled to watch
rather than to place — the observer, the administrator — SHALL be told the
whole board.

#### Scenario: A restricted seat reads its half

- **WHEN** a seat in a two-player game reads its placement area
- **THEN** it is given exactly the squares of its own half, excluding any neutral row

#### Scenario: An unrestricted seat reads the whole board

- **WHEN** a seat in a game that is not two-player reads its placement area
- **THEN** it is given every square of the board

#### Scenario: The published area matches what is enforced

- **WHEN** a seat reads its placement area and then deploys
- **THEN** every square the area names is one the deployment is allowed on
- **AND** every square it does not name is one the deployment is refused on

### Requirement: A Deployment Outside The Area Is Refused At The Client And At Resolution

The system SHALL refuse a deployment outside the placing player's allowed area
when the player makes it, and SHALL refuse it again when the turn resolves, so
that a deployment written by hand or loaded from a file — never passed through
the client — is bound by the same limit as one typed at a prompt.

#### Scenario: The client refuses an out-of-area deployment

- **WHEN** a player deploys a unit outside their allowed area
- **THEN** the deployment is refused and reported, and no unit is created

#### Scenario: Resolution refuses an out-of-area deployment it never saw

- **WHEN** a deployment outside a player's allowed area reaches the server without having been through the client
- **THEN** the turn resolves without placing it
- **AND** the player is told it was refused
