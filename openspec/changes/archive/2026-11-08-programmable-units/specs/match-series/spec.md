## MODIFIED Requirements

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
