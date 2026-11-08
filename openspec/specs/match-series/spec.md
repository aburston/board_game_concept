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
person uses: one `bgcserver` session that registers the seats and commits,
one `bgcclient` session per seat, typed at like a terminal, and a session
that reads the record back once the game is resolved. Every command a
doctrine gives SHALL be typed at its own client's prompt and SHALL be
accepted or refused by the game exactly as it would be for a person. The
harness SHALL NOT reach into the game's storage or its service layer to set
anything up, to order anything, or to read anything a role could not show it.
Once both seats have committed there is nothing left for anybody to decide:
the game is resolved to its end by the last commit, and the harness reads
what the record says.

#### Scenario: A setup goes through the prompt

- **WHEN** a doctrine fields a type with a program
- **THEN** the harness types `add type` and `set program` at that seat's client, the client reads the program file and sends its text, and the game accepts or refuses it as it would for a person

#### Scenario: A refusal is the game's, not the harness's

- **WHEN** a doctrine's setup names a square outside its half, a program the game will not run, or a carrier it has not deployed
- **THEN** the refusal is the one the client prints, is logged against that seat, and the harness adds no check of its own in front of it

#### Scenario: The turns are the game's turns

- **WHEN** both seats have committed
- **THEN** every turn that follows was decided by the units' controllers and resolved by the game, and the harness gave no order and resolved nothing

### Requirement: A Bot Is Given Its Own View And Nothing Else

A doctrine SHALL be handed what its own client can show it of the seat it
is setting up - the board, its units, its types, the players, the flags and
where it may deploy - and nothing else; its setup SHALL be written as data
before the game is created, so nothing about the other seat can reach it.
The record SHALL be read only once the game is resolved, and what it holds
SHALL be written to the log and given to nobody who could still act on it.

#### Scenario: The setup is written in advance

- **WHEN** a doctrine file is read
- **THEN** it names its types, their programs, where its units stand by depth from its own edge, and which carries the flag, and nothing in it depends on the opposing seat

#### Scenario: The record is read when nothing can act on it

- **WHEN** the harness reads a turn of the record
- **THEN** the game is already resolved, and the turn's traces and board go into the log and the history and nowhere else

#### Scenario: A doctrine is a function of its file

- **WHEN** the same doctrine file sets up the same seat twice
- **THEN** it types the same commands in the same order

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

A game SHALL end when the game declares an outcome: a decision, a repeated
state or the turn cap, which are the game's to decide and not the harness's.
Whether a seat is still in the game SHALL be read from what the game
publishes about the players, not inferred by counting units.

#### Scenario: A flag falls

- **WHEN** the record shows a carrier destroyed
- **THEN** the log says its owner was eliminated from that turn, read from the record, and the outcome line is the one the game published

#### Scenario: Nothing changes

- **WHEN** neither army's controllers order anything
- **THEN** the game stops undecided on its first repeated state, and the log says so with the turn it repeated

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
