## MODIFIED Requirements

### Requirement: A Command-Line Role Proves Itself With A Token

The system SHALL let a command-line role talking to a server carry a token,
named on the command line or taken from the environment, and SHALL send it
with every request that role makes.

A role talking to a server with no token given and none in the environment
SHALL ask for a username and a password where there is a person at a terminal
to ask, and SHALL open the session with the token it is issued. Where there is
no terminal, it SHALL report that a token is needed and SHALL NOT open a
session.

A token named on the command line or taken from the environment SHALL be used
without asking anybody anything, so that a script and a bot behave exactly as
they do today.

#### Scenario: Running a role against a server with a token

- **WHEN** a role is run against a server with a token for an account that may
  act as the number it was started for
- **THEN** it opens the session
- **AND** every request it makes carries that token
- **AND** it asks for no username and no password

#### Scenario: Running a role against a server without a token, at a terminal

- **WHEN** a role is run against a server with no token given and none in the
  environment, with a terminal to read from
- **THEN** it asks for a username and a password
- **AND** it opens the session with the token it is issued
- **AND** every request it makes carries that token

#### Scenario: Running a role against a server without a token

- **WHEN** a role is run against a server with no token given and none in the
  environment, and its input is not a terminal
- **THEN** it reports that a token is needed
- **AND** exits with a failure status without opening a session

#### Scenario: A token for an account that may not act as that number

- **WHEN** a role is run for a number the token's account may not act as
- **THEN** the server refuses
- **AND** the role reports the refusal rather than opening a session

#### Scenario: Signing in as an account that may not act as that number

- **WHEN** a role is run against a server and the username and password given
  at the prompt are an account's that may not act as the number the role was
  started for
- **THEN** the server refuses
- **AND** the role reports the refusal rather than opening a session

### Requirement: The Local File Flow Needs No Account

The system SHALL require no account, no token and no authentication of a role
that opens a game directory itself rather than talking to a server. There is
no server to prove anything to, and playing through the file flow SHALL behave
exactly as it did before accounts existed.

This is about playing, not about accounts. A role run against local storage
SHALL still offer the account commands, and SHALL answer them against the
account store where games are kept - so that an account's password can be
changed with no server running. Opening the store this way SHALL create it,
with the two system accounts, exactly as opening it any other way does.

A role SHALL NOT open or create an account store for a local session that
does not ask it to.

#### Scenario: Playing locally

- **WHEN** a role is run with no server named and none found
- **THEN** it opens the game directory itself
- **AND** it asks for no username, no password and no token

#### Scenario: The account store is not needed locally

- **WHEN** a role plays a game locally and no account store exists
- **THEN** the session works
- **AND** no account store is created

#### Scenario: Changing a password locally

- **WHEN** a role run against local storage is asked to sign in and change a
  password, with no server running anywhere
- **THEN** it is answered against the account store where the games are kept
- **AND** the changed password is the one that authenticates afterwards, over
  HTTP as at a command line

#### Scenario: The first local sign-in creates the store

- **WHEN** a role run against local storage is asked to sign in and no account
  store exists
- **THEN** the store is created, holding `admin` and `observer`, each needing
  its password changed
- **AND** the sign-in is answered against it

## ADDED Requirements

### Requirement: Every Command-Line Role Offers The Account Commands

The system SHALL offer, in every command-line role, commands to sign in, to
sign out, to say which account is signed in, and to change a password. Which
role a session is SHALL NOT decide whether it may ask any of them: who is
asking is not a thing one role may say and another may not.

Signing in SHALL take a username and a password and SHALL hold the token it is
issued for the life of that process and no longer. A role SHALL NOT keep a
credential of its own anywhere - no token file, no remembered password - so
that a later run holds no token until it signs in again or is given one.

The record the account store keeps of an issued token is not a credential the
role keeps. That is where a token has always lived, it is what ending a token
ends, and it is reached only by presenting the token itself.

Signing out SHALL end the token the session holds, after which the session
SHALL hold none.

Saying which account is signed in SHALL name the account and its kind, and
SHALL say so when no account is signed in.

#### Scenario: Every role offers them

- **WHEN** any of the command-line roles lists the commands it offers
- **THEN** signing in, signing out, saying who is signed in and changing a
  password are among them
- **AND** the same four are offered by each of the roles

#### Scenario: Signing in

- **WHEN** a session gives a username and the password of that account
- **THEN** it is signed in as that account
- **AND** saying who is signed in names that account and its kind

#### Scenario: A wrong password at a command line

- **WHEN** a session gives a username with a password that is not its
  account's
- **THEN** it is refused
- **AND** the refusal does not say which of the two was wrong
- **AND** the session is signed in as nobody

#### Scenario: Signing out

- **WHEN** a signed-in session signs out
- **THEN** the token it held is ended
- **AND** saying who is signed in reports that nobody is

#### Scenario: A token is not kept between runs

- **WHEN** a session signs in and the process ends
- **THEN** the role has written no credential of its own
- **AND** a later run is signed in as nobody until it signs in or is given a
  token

### Requirement: A Command-Line Role Captures A Forced Password Change

The system SHALL tell a command-line session that signs in as an account
needing a password change that the password must be changed, and SHALL ask for
a new one there and then. The token issued by the sign-in is what the change is
made with, as it is in a browser.

A session that declines to give a new one SHALL be left signed in as an
account that may do nothing else, and SHALL be refused by anything it asks
until the password is changed, with a refusal that says the password must be
changed.

Once the change is made the session SHALL carry on with the same token, and
SHALL NOT be asked again in that session or in a later one.

#### Scenario: Signing in as an account whose password must change

- **WHEN** a session signs in as `admin` with the password `admin`
- **THEN** it is told the password must be changed
- **AND** it is asked for a new one

#### Scenario: Changing it carries on

- **WHEN** a session gives a new password of at least 8 characters at that
  prompt
- **THEN** the change is made
- **AND** the session carries on as that account, with the token it already
  holds
- **AND** a later sign-in with the new password asks for no change

#### Scenario: Declining to change it

- **WHEN** a session signs in as an account that must change its password and
  gives no new one
- **THEN** it is signed in as that account
- **AND** anything else it asks for is refused, saying the password must be
  changed

#### Scenario: Starting a role against a server as such an account

- **WHEN** a role is run against a server with no token, and the username and
  password given at its start-up prompt are an account's that must change its
  password
- **THEN** it asks for a new password before it opens the session
- **AND** the session is opened once the change is made

#### Scenario: A new password that is too short

- **WHEN** a new password shorter than 8 characters is given at that prompt
- **THEN** it is refused, naming the minimum length
- **AND** the password is unchanged

### Requirement: The Account Commands Answer The Same Under Every Access Method

The system SHALL answer signing in, signing out, saying who is signed in and
changing a password identically whether the session reaches the game over HTTP
or by opening a game directory itself. The rules about accounts SHALL be the
ones already stated - what a username may be, how long a password must be, that
a system account must change its password, that a refusal does not say which of
the username and the password was wrong - and no access method SHALL state them
differently.

A password changed under one access method SHALL be the password under every
other.

#### Scenario: The same refusal either way

- **WHEN** the same wrong password, reserved username, or too-short new
  password is given over HTTP and at a local command line
- **THEN** each is refused
- **AND** the refusals say the same thing

#### Scenario: A change made one way holds the other

- **WHEN** an account's password is changed at a command line against local
  storage
- **THEN** signing in with the new password over HTTP is answered
- **AND** the old password authenticates nowhere

#### Scenario: A change made in a browser holds at a command line

- **WHEN** an account's password is changed in a browser
- **THEN** a command-line role signs in with the new password
- **AND** it is not asked to change it again

### Requirement: A Password Typed At A Command Line Is Not Kept

The system SHALL read a password typed at a terminal without echoing it, and
SHALL NOT put a password into a command history, a completion candidate, a log
line, an error message or a process argument list.

A password SHALL NOT be accepted as a command-line argument of any role, so
that it cannot be left in a shell history or read from a process listing by
anybody on the same machine.

#### Scenario: Typing a password

- **WHEN** a password is typed at a prompt on a terminal
- **THEN** it is not echoed
- **AND** the line it was typed on is not added to the command history

#### Scenario: A password is not an argument

- **WHEN** a role is started
- **THEN** it takes no argument that is a password
- **AND** no password appears in its process arguments

#### Scenario: A refusal says nothing of the password

- **WHEN** a sign-in or a password change is refused
- **THEN** neither password given is in what is reported
