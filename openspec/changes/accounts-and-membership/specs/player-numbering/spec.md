## ADDED Requirements

### Requirement: An Identity Reached Through A Server Is Proven, Not Asserted

Where a session reaches a game through a server rather than by opening the
game directory itself, the system SHALL require the session to prove it is
entitled to the number it opens the game as, and SHALL refuse it otherwise.
Naming a number SHALL NOT be a way of being it.

What a number is entitled to SHALL be unchanged by this: the administrator,
the players and the observer are the identities this capability already
describes, and they see and change exactly what it already says they do. What
is added is that a served session must show it is the number it claims before
any of that applies.

`identity-and-accounts` states what counts as proof and which accounts may act
as which numbers.

#### Scenario: A served session that proves nothing

- **WHEN** a session reaches a game through a server and shows no entitlement
  to the number it names
- **THEN** it is refused
- **AND** it is given no view and carries out no command

#### Scenario: Naming another player's number

- **WHEN** a served session names a player number it is not entitled to
- **THEN** it is refused
- **AND** that player's view, orders and uncommitted work stay unread

#### Scenario: What a proven number is entitled to is unchanged

- **WHEN** a served session proves it is a player, the administrator or the
  observer
- **THEN** it sees and changes exactly what that identity has always seen and
  changed

#### Scenario: Opening a game directly is unaffected

- **WHEN** a session opens a game directory itself rather than through a server
- **THEN** it opens the game as the number it was started for
- **AND** nothing further is required of it

### Requirement: A Number Is One Identity However Its Seats Are Held

The system SHALL keep every number of a game a separate identity even where
one person is entitled to more than one of them. Two numbers held by one
person SHALL have their own units, their own orders, their own view, their own
uncommitted work and their own commit, and the turn SHALL be held open for
each of them that is still in the game.

Being entitled to two numbers SHALL NOT let either of them see what the other
sees. Visibility is decided by the number, as `visibility` describes, and never
by who is entitled to it.

#### Scenario: Two numbers held by one person are two identities

- **WHEN** one person is entitled to two of a game's player numbers
- **THEN** each number holds its own units and gives its own orders
- **AND** neither is shown what the other may see

#### Scenario: The barrier counts numbers, not people

- **WHEN** one person is entitled to two numbers and one of them commits
- **THEN** the turn is still held open for the other
- **AND** it resolves when every number still in the game has committed

#### Scenario: The game is decided between numbers

- **WHEN** the numbers still standing at the end of a turn are held by one person
- **THEN** the game is decided between those numbers as `game-outcome` requires
- **AND** who is entitled to them makes no difference to the outcome
