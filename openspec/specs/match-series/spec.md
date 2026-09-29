# match-series Specification

## Purpose

A series of games played by bots is evidence about the rules, and it is only
evidence if it was played the way people play: through the real roles, each
player shown only what the game shows them, on the game's own defaults, and
written down turn by turn so that a claim about what decided a game can be
checked against the board. This capability says what a series has to keep to
count, and what its write-up has to carry to be read beside the ones before it.

## Requirements

### Requirement: A Game Is Played Through The Real Roles

A game in a series SHALL be driven through the same command-line roles a
person uses: one server session that sets the game up and resolves each turn,
one client session per seat that stays open for the whole game and is typed
at like a terminal, and an observer session. Every command a bot gives SHALL
be typed at its own client's prompt and SHALL be accepted or refused by the
game exactly as it would be for a person. The harness SHALL NOT reach into the
game's storage, its domain objects or its service layer to place a unit, give
an order, read a board or resolve a turn.

#### Scenario: An order goes through the prompt

- **WHEN** a bot orders a unit to move
- **THEN** the order is typed at that bot's own client prompt as `move <unit> <direction>`
- **AND** whether it is carried out is decided by the game when the turn resolves

#### Scenario: A refusal is the game's, not the harness's

- **WHEN** a bot deploys a unit on a square outside its half, or past its budget, or onto a taken square
- **THEN** the client refuses it and says why
- **AND** the harness records the refusal as the client printed it and refuses nothing of its own

#### Scenario: The turn is the game's turn

- **WHEN** every seat still in the game has committed
- **THEN** the turn is resolved by the server session, and each client returns from the commit barrier with what the game published to it

### Requirement: A Bot Is Given Its Own View And Nothing Else

Before each turn a bot SHALL be handed what its own client can show it, read
by typing `show ... json` at that client's prompt: the board, its units, its
types, the players, the flags, its placement area, and any refusals the client
printed since the last turn. A bot SHALL NOT be given the observer's view,
another seat's view, the match log, or any record the harness keeps for
itself. What a bot knows of the enemy is therefore exactly what the game's
visibility rules publish to its seat: the squares of every flag, and any unit
its own units fought last turn.

#### Scenario: The enemy is where the rules put it

- **WHEN** none of a bot's units fought last turn
- **THEN** the view it is handed holds no enemy unit
- **AND** it still holds the square of every flag on the board

#### Scenario: The observer is never a source

- **WHEN** the harness reads the observer's board to write the match log
- **THEN** it does so only after both seats have given their orders for that turn
- **AND** nothing read from the observer is passed to either bot at any point

#### Scenario: A doctrine is a function of its view

- **WHEN** a bot is handed the same sequence of views twice
- **THEN** it gives the same commands both times: a doctrine consults no random number, clock or process identity

### Requirement: A Series Is Played On The Game's Defaults

A game in the series SHALL be created without naming a board size or a
budget, so that it plays on whatever the game gives a new two-player game: the
default board, the default budget, the placement halves the game publishes,
and the stock army and flag each seat opens with. A doctrine MAY change what
it was given through the ordinary setup commands - taking units back,
defining types, deploying, designating its flag - and SHALL be able to leave
the stock army exactly as it stands. The harness SHALL add no setup of its
own to what a doctrine returns.

#### Scenario: A doctrine that changes nothing

- **WHEN** a doctrine returns no setup commands at all
- **THEN** its seat commits the stock army as given, with the flag where the game put it
- **AND** the commit is accepted

#### Scenario: A doctrine that rebuilds

- **WHEN** a doctrine takes every stock unit back, defines its own types and deploys within its budget and half
- **THEN** each command is accepted or refused by the game on its own terms
- **AND** the seat commits what stands after them

#### Scenario: A setup the game refuses

- **WHEN** a doctrine's setup is committed with no flag carrier, or with nothing deployed
- **THEN** the client refuses the commit, as it would for a person
- **AND** the harness reports the refusal against that doctrine and ends the game as not played, rather than retrying or repairing the setup

### Requirement: The Outcome Is Read From The Game

A game SHALL end when the game declares an outcome or when the series' turn
cap is reached, whichever comes first. Whether a seat is still in the game
SHALL be read from what the game publishes about the players, not inferred by
the harness from what stands on the board; the count of units in play the
harness reports each turn is a description for the reader, not the judgement.

#### Scenario: A flag falls

- **WHEN** a turn resolves in which one seat's flag carrier is destroyed
- **THEN** the game reports that seat out and, in a two-player game, the other the winner
- **AND** the match record carries that outcome and the turn it was decided on

#### Scenario: The cap is reached

- **WHEN** the turn cap is reached with no outcome declared
- **THEN** the game is recorded as undecided after that many turns, with what each seat still holds

### Requirement: Every Game Leaves A Record That Can Be Checked

For each game the harness SHALL keep: the pairing and each doctrine's stated
army; every command each bot gave, turn by turn, and every refusal each
client printed; the observer's board after each turn; the outcome; the final
state of every unit; and a machine-readable history of the turns. The three
roles' transcripts SHALL be kept whole. Games in a series SHALL be numbered
on from the last number any earlier series used, so that no record overwrites
another.

#### Scenario: A claim in the write-up can be traced

- **WHEN** a write-up says a game was decided on a given turn by a given fight
- **THEN** that turn's orders and the board after it are in the game's log
- **AND** the full exchange is in the transcripts

#### Scenario: Numbers never collide

- **WHEN** a new series is played
- **THEN** its first game is numbered one above the highest game number in `matches/logs/`

### Requirement: A Series Write-Up Says What It Was Played Under

A series SHALL be written up in a document that names the rules it was played
under - the commit, and the rules that differ from the series before it - the
board, budget and placement it was played on, every pairing with its result
and the turn it was decided on, and what the results say about the questions
still open in the rules. It SHALL NOT change a rule: a rule change the series
argues for is proposed as its own change. When a rule a series was played
under later changes, that series' write-up SHALL carry a notice at its head
saying so and naming the series that replaced it.

#### Scenario: A reader knows which game they are reading about

- **WHEN** a write-up is opened
- **THEN** its head states the commit and the rules it was played under, and the board and budget

#### Scenario: A superseded series says so

- **WHEN** a series has been played under a rule that has since changed
- **THEN** its write-up opens with a notice that it was played under superseded rules, naming what changed and which write-up is current
