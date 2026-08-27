## ADDED Requirements

### Requirement: An Account Is Who A Person Is

The system SHALL hold accounts, each of which is one person or one program
that plays. An account SHALL carry a username, a password, and a kind, where
the kind is the administrator, the observer, or a player.

An account SHALL NOT be a player number. A number says what a session is
entitled to within one game; an account says who is asking, across every game.
The two SHALL be related only by the memberships this capability describes and
by the two system accounts it fixes.

#### Scenario: An account and a number are different things

- **WHEN** an account holds a seat in one game and a different seat in another
- **THEN** it is the same account in both
- **AND** the number it acts as in each is the number of the seat it holds there

#### Scenario: The kinds an account may be

- **WHEN** an account is created
- **THEN** it is the administrator, the observer, or a player
- **AND** no account is more than one of those

### Requirement: Accounts Live Outside Any Game

The system SHALL keep accounts, memberships and sessions in one store that
belongs to the server rather than to a game, and SHALL NOT keep any of them
inside a game's own storage.

Deleting a game SHALL NOT delete an account. Creating a game SHALL NOT create
one.

#### Scenario: An account outlives a game

- **WHEN** a game an account held a seat in is deleted
- **THEN** the account still exists
- **AND** it may hold a seat in another game

#### Scenario: A game's storage holds no account

- **WHEN** a game's own storage is read
- **THEN** it holds no username, no password and no account of any kind

### Requirement: The Two System Accounts Exist From First Start

The system SHALL create two accounts the first time the account store is
opened: one named `admin`, of the administrator kind, with the password
`admin`; and one named `observer`, of the observer kind, with the password
`observer`. Both SHALL be created needing a password change.

Opening a store that already holds them SHALL NOT create them again and SHALL
NOT alter the passwords they now have.

#### Scenario: First start

- **WHEN** the account store is opened for the first time
- **THEN** an account `admin` of the administrator kind exists
- **AND** an account `observer` of the observer kind exists
- **AND** each needs its password changed

#### Scenario: A later start does not reset a changed password

- **WHEN** the administrator's password has been changed and the server is restarted
- **THEN** the changed password is the one that authenticates
- **AND** `admin` is not the password of any account

### Requirement: A System Account Is Unusable Until Its Password Is Changed

The system SHALL refuse every request from an account that needs a password
change, except the request that changes that account's password. The refusal
SHALL say that the password must be changed.

An account SHALL stop needing a change once one is made, and SHALL NOT need
one again because the server restarted.

#### Scenario: Acting before the password is changed

- **WHEN** the administrator authenticates with the password `admin` and asks
  for anything other than a password change
- **THEN** the request is refused, saying the password must be changed
- **AND** nothing is read and nothing is changed

#### Scenario: Changing the password lifts the refusal

- **WHEN** an account that needs a password change changes it
- **THEN** its later requests are answered
- **AND** it does not need another change

#### Scenario: The observer is held to it too

- **WHEN** the observer authenticates with the password `observer` and asks to
  see a game
- **THEN** the request is refused, saying the password must be changed

### Requirement: Registering An Account

The system SHALL let anyone register an account of the player kind by giving a
username and a password. A registered account SHALL hold no seat until it
claims one.

A password SHALL be at least 8 characters. The system SHALL NOT require any
other property of a password.

#### Scenario: Registering

- **WHEN** an unused username and a password of at least 8 characters are given
- **THEN** an account of the player kind is created
- **AND** it holds no seat in any game

#### Scenario: A password that is too short

- **WHEN** a password shorter than 8 characters is given
- **THEN** registration is refused, naming the minimum length
- **AND** no account is created

#### Scenario: Registration does not choose a kind

- **WHEN** an account is registered
- **THEN** it is of the player kind
- **AND** no registration produces the administrator or the observer

### Requirement: Reserved And Duplicate Usernames Are Refused

The system SHALL refuse to register the usernames `admin` and `observer`, and
SHALL refuse a username already held by an account. Both comparisons SHALL
ignore case, so that a name differing only in case is the same name.

The username SHALL be stored as it was typed, and compared without regard to
case.

#### Scenario: Registering a reserved name

- **WHEN** registration is attempted with the username `admin` or `observer`
- **THEN** it is refused, saying the name is reserved
- **AND** no account is created

#### Scenario: Registering a reserved name in another case

- **WHEN** registration is attempted with the username `Admin` or `OBSERVER`
- **THEN** it is refused for the same reason
- **AND** no account is created

#### Scenario: Registering a name already taken

- **WHEN** registration is attempted with a username an account already holds,
  in any case
- **THEN** it is refused
- **AND** the existing account is unchanged

#### Scenario: The stored name keeps its case

- **WHEN** an account is registered as `Ada`
- **THEN** it is shown as `Ada`
- **AND** `ada` cannot be registered afterwards

### Requirement: Passwords Are Stored Hashed

The system SHALL store a password only as a one-way hash with a salt, and
SHALL NOT store, log or report a password in a form it could be read back
from. Authenticating SHALL compare against the hash.

#### Scenario: What is stored

- **WHEN** an account's stored record is read
- **THEN** the password is not in it in any recoverable form

#### Scenario: Two accounts with the same password

- **WHEN** two accounts are registered with the same password
- **THEN** the stored hashes differ

### Requirement: Changing And Resetting A Password

The system SHALL let an account change its own password by giving its current
one and a new one, and SHALL refuse the change when the current password is
wrong. The administrator SHALL be able to set any account's password without
giving that account's current one.

A password change SHALL be possible while the server runs, without restarting
it.

#### Scenario: Changing your own password

- **WHEN** an account gives its current password and a new one of at least 8 characters
- **THEN** the new password is the one that authenticates
- **AND** the old one no longer does

#### Scenario: Changing with the wrong current password

- **WHEN** an account gives a current password that is not its own
- **THEN** the change is refused
- **AND** the password is unchanged

#### Scenario: The administrator resets another account

- **WHEN** the administrator sets an account's password without giving that account's current one
- **THEN** the new password authenticates that account

#### Scenario: A player cannot reset another account

- **WHEN** an account of the player kind tries to set another account's password
- **THEN** it is refused
- **AND** the other account's password is unchanged

### Requirement: A Session Is Held By A Token

The system SHALL issue a token when an account authenticates with its username
and password, and SHALL accept that token in place of them on later requests.
A token SHALL name the account it was issued to and SHALL have a time after
which it is no longer accepted.

The system SHALL let an account end a token, after which it SHALL NOT be
accepted. An account SHALL be able to mint a token for a program to use, and
such a token SHALL be one of these tokens and no other kind of thing.

#### Scenario: Authenticating

- **WHEN** an account gives its username and its password
- **THEN** it receives a token
- **AND** that token identifies it on later requests

#### Scenario: A wrong password

- **WHEN** a username is given with a password that is not its account's
- **THEN** no token is issued
- **AND** the refusal does not say which of the two was wrong

#### Scenario: A token that has been ended

- **WHEN** a token is ended and then presented
- **THEN** it is refused
- **AND** the account may authenticate again for a new one

#### Scenario: A token past its time

- **WHEN** a token is presented after the time it is accepted until
- **THEN** it is refused

### Requirement: The Administrator Is Player 0 Of Every Game

The system SHALL treat the account of the administrator kind as player 0 of
every game, without a membership and without being registered as a player of
any of them.

The administrator SHALL NOT act as a player number unless it holds a seat for
that number like any other account.

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

### Requirement: The Observer Is 1000 Of Every Game And Sees Everything

The system SHALL treat the account of the observer kind as the observer,
number 1000, of every game, without a membership.

The observer account is shared, and the system SHALL NOT attempt to prevent a
person who holds a seat in a game from also using it to watch that game. What
`visibility` grants the observer is the whole board, and using the shared
account to see a game one is playing is left to the honesty of the people
playing. The system SHALL state, where an account authenticates, that the
observer sees every unit of every player.

#### Scenario: Observing any game

- **WHEN** the observer asks to act as 1000 of a game
- **THEN** it is allowed, for every game, with no membership needed

#### Scenario: A player may also use the observer account

- **WHEN** a person holding a seat in a game authenticates as the observer and
  watches that game
- **THEN** the request is answered
- **AND** nothing refuses it on the grounds that they hold a seat

#### Scenario: The bargain is stated

- **WHEN** the place an account authenticates is shown
- **THEN** it says that the observer account sees every unit of every player

#### Scenario: The observer still changes nothing

- **WHEN** the observer asks to change a game
- **THEN** it is refused, as `player-numbering` requires of the number 1000

### Requirement: Claiming A Seat

The system SHALL let a registered account claim a seat in a game, where a seat
is a player number the administrator has registered for that game. A seat
SHALL have at most one holder.

A claim SHALL be refused when the seat is already held, when the game has no
such registered player, and when the game has started.

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

- **WHEN** an account claims a seat in a game that has started
- **THEN** it is refused

#### Scenario: Claiming does not register a player

- **WHEN** a seat is claimed
- **THEN** the game's registered players are the same as before
- **AND** the budget of the seat is the one it was registered with

### Requirement: One Account May Hold Several Seats In One Game

The system SHALL allow one account to hold more than one seat in the same
game, so that one person may play more than one side.

Each seat SHALL remain a separate identity: its orders, its view, its draft
and its commit are its own, and the turn SHALL be held open for each seat that
is still in the game as it would be for seats held by different accounts.

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

### Requirement: Giving Up A Seat

The system SHALL let the account holding a seat give it up while the game has
not started, after which the seat is unclaimed and may be claimed again. It
SHALL refuse to give up a seat once the game has started.

#### Scenario: Giving up before the game starts

- **WHEN** the holder of a seat gives it up and the game has not started
- **THEN** the seat is unclaimed
- **AND** another account may claim it

#### Scenario: Giving up after the game has started

- **WHEN** the holder of a seat gives it up and the game has started
- **THEN** it is refused
- **AND** they still hold the seat

#### Scenario: Only the holder gives up a seat

- **WHEN** an account that does not hold a seat tries to give it up
- **THEN** it is refused
- **AND** the holder is unchanged

### Requirement: Which Account May Act As Which Number

The system SHALL decide whether an account may act as a number of a game by
one rule, stated once and asked by every caller:

- **0** requires the account of the administrator kind.
- **1000** requires the account of the observer kind or the administrator.
- **1 to 999** requires that the account holds that seat in that game.

A request to act as a number the account may not act as SHALL be refused, and
SHALL neither read nor change anything.

#### Scenario: A player acting as their own seat

- **WHEN** an account holding seat 2 of a game acts as 2 in that game
- **THEN** it is allowed

#### Scenario: A player acting as another seat

- **WHEN** an account holding seat 2 of a game acts as 3 in that game
- **THEN** it is refused
- **AND** nothing of seat 3's is read

#### Scenario: A seat in another game is not a seat in this one

- **WHEN** an account holding seat 2 of one game acts as 2 in a game it holds
  no seat in
- **THEN** it is refused

#### Scenario: A player acting as the administrator or the observer

- **WHEN** an account of the player kind acts as 0 or as 1000
- **THEN** it is refused

#### Scenario: The administrator acting as the observer

- **WHEN** the administrator acts as 1000
- **THEN** it is allowed, as it is already entitled to see the whole game

#### Scenario: A refused request reads nothing

- **WHEN** a request to act as a number is refused
- **THEN** no view of that number is returned
- **AND** no command of that number is carried out

### Requirement: An Unproven Request Is Refused

The system SHALL refuse a request to a served game that carries no token or an
unaccepted one, and SHALL answer it without reading the game. A number in the
path of a request SHALL NOT by itself identify anybody.

#### Scenario: No credential

- **WHEN** a request for a game is made with no token
- **THEN** it is refused
- **AND** no view of any player is returned

#### Scenario: An unaccepted token

- **WHEN** a request carries a token that was never issued, was ended, or is
  past its time
- **THEN** it is refused

#### Scenario: The number alone proves nothing

- **WHEN** a request names a player number and carries no accepted token
- **THEN** it is refused
- **AND** naming a different number does not change that

### Requirement: A Command-Line Role Proves Itself With A Token

The system SHALL let a command-line role talking to a server carry a token,
named on the command line or taken from the environment, and SHALL send it
with every request that role makes.

A role talking to a server without a token SHALL report that it needs one and
SHALL NOT open a session.

#### Scenario: Running a role against a server with a token

- **WHEN** a role is run against a server with a token for an account that may
  act as the number it was started for
- **THEN** it opens the session
- **AND** every request it makes carries that token

#### Scenario: Running a role against a server without a token

- **WHEN** a role is run against a server with no token given and none in the
  environment
- **THEN** it reports that a token is needed
- **AND** exits with a failure status without opening a session

#### Scenario: A token for an account that may not act as that number

- **WHEN** a role is run for a number the token's account may not act as
- **THEN** the server refuses
- **AND** the role reports the refusal rather than opening a session

### Requirement: The Local File Flow Needs No Account

The system SHALL require no account, no token and no authentication of a role
that opens a game directory itself rather than talking to a server. There is
no server to prove anything to, and the file flow SHALL behave exactly as it
did before accounts existed.

#### Scenario: Playing locally

- **WHEN** a role is run with no server named and none found
- **THEN** it opens the game directory itself
- **AND** it asks for no username, no password and no token

#### Scenario: The account store is not needed locally

- **WHEN** a role plays a game locally and no account store exists
- **THEN** the session works
- **AND** no account store is created
