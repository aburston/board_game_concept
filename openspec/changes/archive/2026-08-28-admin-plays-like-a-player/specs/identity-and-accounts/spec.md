## ADDED Requirements

### Requirement: A Seat The Administrator Holds Is An Ordinary Seat

The system SHALL treat a seat held by the account of the administrator kind
exactly as it treats a seat held by an account of the player kind. The kind of
the account holding a seat SHALL NOT be consulted when the system decides:

- what that seat's views hold - board, types, units, players, pending, events,
  designs and flags alike;
- what that seat's point budget is, what its army has spent, and what it has
  left;
- which commands that seat may give, and which of them are refused;
- whether the turn is held open for that seat at the commit barrier;
- when that seat may be claimed, and when it may be given up.

Two seats of the same number, in two games set up alike, SHALL be answered
identically whether the account holding them is the administrator or a
registered player. A difference between the two is a defect, not a privilege.

#### Scenario: The same board a player would be shown

- **WHEN** the administrator holds a seat and reads that seat's board
- **THEN** it is shown what a registered player holding that seat would be shown
- **AND** enemy units it has not made contact with are not in it

#### Scenario: The same budget

- **WHEN** the administrator holds a seat and reads the players view
- **THEN** that seat's budget, spend and remainder are those the seat was
  registered with
- **AND** they are what a registered player holding it would be given

#### Scenario: The turn waits for it

- **WHEN** the administrator holds a seat and commits it while another seat has
  not committed
- **THEN** the turn is not resolved
- **AND** the seat is named among those still being waited for until it commits

#### Scenario: The same refusal

- **WHEN** the administrator holds a seat and gives a command that seat may not
  give
- **THEN** it is refused for the reason a registered player would be refused it
- **AND** nothing of that seat's is changed

#### Scenario: A seat is claimed and given up on the same terms

- **WHEN** the administrator claims a seat, or gives one up
- **THEN** it is allowed or refused by the rules `Claiming A Seat` and `Giving
  Up A Seat` state
- **AND** being the administrator neither permits nor prevents anything those
  rules do not

### Requirement: The Administrator's Privileges Do Not Reach Into Its Seat

The system SHALL keep what the administrator is entitled to as player 0 and as
the observer separate from what a seat it holds is entitled to. A session
opened as a seat SHALL be given that seat's view and no more, whatever the
account holding it may see when it acts as another number.

This is the half of the rule that makes the account worth testing with. An
administrator playing a seat plays blind, as everybody else at the table does;
that it could open a second session as player 0 and see the whole board is
something it chooses to do, and is not something its seat does for it.

#### Scenario: A seat sees its own view, not everything

- **WHEN** the administrator holds a seat in a game and reads that seat's units
- **THEN** only the units that seat is entitled to see are listed
- **AND** an enemy unit it has not made contact with is not among them

#### Scenario: Two numbers, two entitlements, one account

- **WHEN** the administrator reads a game as player 0 and as a seat it holds
- **THEN** the reading as player 0 holds the whole game
- **AND** the reading as the seat holds only what that seat may see

#### Scenario: Administering a game it plays in

- **WHEN** the administrator holds a seat in a game and acts as player 0 of that
  same game
- **THEN** it is allowed, as it is of every game
- **AND** the seat it holds is unaffected by its having done so

## MODIFIED Requirements

### Requirement: The Administrator Is Player 0 Of Every Game

The system SHALL treat the account of the administrator kind as player 0 of
every game, without a membership and without being registered as a player of
any of them.

The administrator SHALL NOT act as a player number unless it holds a seat for
that number like any other account. Where it does hold one, the seat is an
ordinary seat and is governed by `A Seat The Administrator Holds Is An Ordinary
Seat`.

#### Scenario: Administering any game

- **WHEN** the administrator asks to act as player 0 of a game
- **THEN** it is allowed, for every game, with no membership needed

#### Scenario: The administrator is not a player by default

- **WHEN** the administrator asks to act as a player number it holds no seat for
- **THEN** it is refused

#### Scenario: The administrator may hold a seat

- **WHEN** the administrator claims an unclaimed seat
- **THEN** it holds that seat as any account would
- **AND** it is still player 0 of that game

### Requirement: One Account May Hold Several Seats In One Game

The system SHALL allow one account to hold more than one seat in the same
game, so that one person may play more than one side. This SHALL be true of the
administrator as it is of any other account.

Each seat SHALL remain a separate identity: its orders, its view, its draft
and its commit are its own, and the turn SHALL be held open for each seat that
is still in the game as it would be for seats held by different accounts.

An account holding every seat of a game SHALL be able to play that game from
its setup to its outcome, unaided. Nothing SHALL refuse a turn on the grounds
that one account committed every seat of it. This is what lets a game be played
through by one person to test it.

#### Scenario: Holding two seats

- **WHEN** an account claims two unclaimed seats in one game
- **THEN** it holds both
- **AND** it may act as either number in that game

#### Scenario: Two seats are two identities

- **WHEN** an account holds two seats in a game and gives orders as one of them
- **THEN** those orders belong to that seat only
- **AND** the other seat's orders, view and draft are unaffected

#### Scenario: The barrier waits for each seat

- **WHEN** an account holds two seats and commits one of them
- **THEN** the turn is still held open for the other
- **AND** it resolves when every seat still in the game has committed

#### Scenario: One account plays a game through

- **WHEN** the administrator sets a game up, holds every seat of it, and commits
  each seat of every turn
- **THEN** each turn resolves when the last of its seats has committed
- **AND** the game reaches an outcome as it would with a person at each seat

### Requirement: Claiming A Seat

The system SHALL let a registered account claim a seat in a game, where a seat
is a player number the administrator has registered for that game. A seat
SHALL have at most one holder.

A claim SHALL be refused when the seat is already held, when the game has no
such registered player, and when the game has started.

The system SHALL refuse a claim from the account of the observer kind. The
observer is 1000 of every game and holds a seat in none: the account is shared
and `visibility` grants it every unit of every player, so a seat it held would
be a seat played with the whole board in view by whoever knows the shared
password. The refusal SHALL say that the observer holds a seat in no game.

An account of the observer kind SHALL NOT be able to act as a player number of
any game, whatever the system has stored about which seats are held. The rule
SHALL be answered from what the account is, so that it holds of a store as it
is found and not only of a store as it is written.

A game SHALL be taken to have started once one of its turns has been resolved,
rather than once its setup has been committed. The administrator's commit that
ends setup is not a turn and does not number one, so between that commit and
the first resolved turn the board is set and nobody has moved - which is the
window a person joining a game arrives in, and a seat SHALL still be claimable
then.

#### Scenario: Claiming an unclaimed seat

- **WHEN** an account claims a seat no account holds, in a game that has not started
- **THEN** it holds that seat
- **AND** it may act as that number in that game

#### Scenario: Claiming a seat someone holds

- **WHEN** an account claims a seat another account holds
- **THEN** it is refused
- **AND** the holder is unchanged

#### Scenario: Claiming a seat that is not registered

- **WHEN** an account claims a number the administrator has not registered as a
  player of that game
- **THEN** it is refused
- **AND** no player is added to the game

#### Scenario: Claiming after the game has started

- **WHEN** an account claims a seat in a game one of whose turns has resolved
- **THEN** it is refused

#### Scenario: Claiming after setup is committed but before the first turn

- **WHEN** an account claims an unclaimed seat in a game whose setup has been
  committed and none of whose turns has resolved
- **THEN** it holds that seat

#### Scenario: Claiming does not register a player

- **WHEN** a seat is claimed
- **THEN** the game's registered players are the same as before
- **AND** the budget of the seat is the one it was registered with

#### Scenario: The observer is refused a seat

- **WHEN** the observer claims an unclaimed seat of a game that has not started
- **THEN** it is refused, saying it holds a seat in no game
- **AND** the seat is still unclaimed

#### Scenario: A stored seat does not make the observer a player

- **WHEN** the system holds a record that the observer holds a seat, and the
  observer asks to act as that number
- **THEN** it is refused
- **AND** what it may see as 1000 of that game is unchanged
