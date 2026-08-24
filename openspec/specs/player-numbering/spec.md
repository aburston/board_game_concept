# player-numbering Specification

## Purpose

Who the numbers in a game belong to. Every session opens a game as a number, and
that number is the whole of who the session is: it decides what may be seen and
what may be done. Three kinds of session share the numbering, so the ranges are
stated once here rather than assumed separately by each of them.

## Requirements

### Requirement: The Numbers A Game Uses

The system SHALL divide the numbers a session may open a game as into three,
and SHALL treat them as distinct identities:

- **0** is the administrator, who sets a game up and is the commit authority.
- **1 to 999** are the players, who own units and give orders.
- **1000** is the observer, who watches and changes nothing.

A number outside these SHALL NOT identify anything, and a session SHALL NOT be
opened as one.

#### Scenario: The three kinds of identity

- **WHEN** a session is opened as 0, as a number from 1 to 999, or as 1000
- **THEN** it is the administrator, a player, or the observer respectively
- **AND** no two of those are the same identity

#### Scenario: A number that identifies nobody

- **WHEN** a session is opened as a number that is negative, or above 1000, or is 1000's neighbour on either side without being a player or the observer
- **THEN** it is refused rather than opened

### Requirement: Reserved Numbers Are Not Players

The system SHALL NOT allow 0 or 1000 to be registered as a player of a game.
The administrator and the observer own no units, give no orders, and SHALL NOT
be counted among the players a turn is held open for or a game is decided
between.

#### Scenario: Registering the administrator as a player

- **WHEN** a player is registered with the number 0
- **THEN** the registration is refused
- **AND** no player is added to the game

#### Scenario: Registering the observer as a player

- **WHEN** a player is registered with the number 1000
- **THEN** the registration is refused
- **AND** no player is added to the game

#### Scenario: The commit barrier does not wait for a reserved number

- **WHEN** every registered player has committed
- **THEN** the turn is resolved
- **AND** it is not held open for the administrator or the observer

### Requirement: A Player Number Is Within Range

The system SHALL refuse a player number below 1 or above 999 wherever one
arrives — registered at a prompt, read from a configuration file, or held by a
game being opened. A number out of range SHALL be refused in a way the caller
can act on, and SHALL NOT end the session that reported it, except when it is a
game on disk that cannot be read as a result.

#### Scenario: Registering a number below the range

- **WHEN** a player is registered with a number below 1
- **THEN** the registration is refused, naming the permitted range
- **AND** the session continues and takes further commands

#### Scenario: Registering a number above the range

- **WHEN** a player is registered with a number above 999
- **THEN** the registration is refused, naming the permitted range
- **AND** the session continues and takes further commands

#### Scenario: A configuration file naming a number out of range

- **WHEN** a player configuration file names a player number outside 1 to 999
- **THEN** loading it is refused, naming the permitted range
- **AND** the session continues and takes further commands

#### Scenario: A game holding a number out of range

- **WHEN** a game is opened whose registered players include a number outside 1 to 999
- **THEN** the game is reported as one that cannot be read
- **AND** the session exits rather than opening onto it

### Requirement: Only An Identity Entitled To Change A Game May Change It

The system SHALL decide from a session's identity alone whether it may change a
game, and SHALL refuse a command that would change one from an identity that may
not. The observer SHALL NOT be able to change a game by any route. The
administrator and the players SHALL, each within the rules that already govern
what they may do and when.

#### Scenario: The observer may not change a game

- **WHEN** a command that would change a game is carried out for the observer
- **THEN** it is refused
- **AND** the game is unchanged

#### Scenario: The administrator may still set a game up

- **WHEN** the administrator sizes a board or registers a player before the game starts
- **THEN** the command is carried out

#### Scenario: A player may still order their units

- **WHEN** a player deploys a unit or orders a move, within the rules for when they may
- **THEN** the command is carried out

### Requirement: Entitlement To See The Whole Game

The system SHALL grant the administrator and the observer sight of the whole
game, and SHALL grant a player only their own published view. Which of these a
session gets SHALL follow from its identity rather than from any one number, so
that both entitled identities are served the same way.

#### Scenario: The observer sees the whole game

- **WHEN** the observer opens a game
- **THEN** it is shown every unit on the board, whoever owns it

#### Scenario: The administrator sees the whole game

- **WHEN** the administrator opens a game
- **THEN** it is shown every unit on the board, whoever owns it

#### Scenario: A player sees only their own view

- **WHEN** a player opens a game
- **THEN** they are shown their own units and the enemy units they have made contact with, and no others

### Requirement: A Session Reads Only Its Own Uncommitted Work

The system SHALL restore to a session only the work that session drafted, and
SHALL NOT restore to it work drafted under another identity. In particular the
observer SHALL NOT be shown the administrator's uncommitted setup.

#### Scenario: The observer does not see the administrator's uncommitted setup

- **WHEN** the administrator sizes a board and registers players without committing, and the observer then opens the same game
- **THEN** the observer is not shown that board or those players
- **AND** the observer holds no draft of its own

#### Scenario: The administrator's own setup is still restored to the administrator

- **WHEN** the administrator sizes a board without committing and the administrator opens the game again
- **THEN** the board is restored
