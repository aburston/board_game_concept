# Spec Delta

## ADDED Requirements

### Requirement: Setting A Type's Program

The system SHALL let a player set the program of one of their own types
during setup via `set program <type> <file>`, reading it from the named file,
and SHALL list it back with `show program <type>` with each line's tick cost.
A program the instruction set refuses SHALL be refused naming the line, with
the type's program unchanged. Setting a program on a type that is not the
player's, or has compute 0, or after the setup is committed, SHALL be refused
saying why.

#### Scenario: Setting a program

- **WHEN** the player runs `set program Runner hunter.asm` during setup and the file holds a legal program
- **THEN** the type `Runner` carries that program
- **AND** the client lists it with the tick cost of each line

#### Scenario: A program with a bad line

- **WHEN** the file holds a line the instruction set does not accept
- **THEN** the client refuses, naming the line
- **AND** the type's program is as it was

#### Scenario: A program on a type with no controller

- **WHEN** the player sets a program on a type with compute 0
- **THEN** the client refuses, saying the type has no controller

#### Scenario: After commit

- **WHEN** the player runs `set program` after committing their setup
- **THEN** the client refuses, saying their setup is committed

#### Scenario: Reading a program back

- **WHEN** the player runs `show program Keep`
- **THEN** the program is listed line by line with each line's ticks and the total of a straight run
- **AND** the listing says the type's compute, how many ticks an energy buys it, and the per-turn cap

### Requirement: Watching The Replay

The system SHALL let a player read the record of a resolved game via
`show turn <n>`, `next` and `prev`, and the board as their army knew it via
`show turn <n> known`. The client SHALL open a resolved game at its final
turn, reporting the result, and SHALL refuse these commands, saying the game
has not been resolved, while any player's setup is uncommitted.

#### Scenario: Reading a turn

- **WHEN** the player runs `show turn 12` on a resolved game
- **THEN** the board after turn 12 is drawn with every unit on it
- **AND** what turn 12 did to the player's units is listed
- **AND** each of the player's controllers' traces for turn 12 is listed

#### Scenario: Stepping through

- **WHEN** the player runs `next` after `show turn 12`
- **THEN** turn 13 is shown
- **AND** `prev` then shows turn 12 again

#### Scenario: What my army knew

- **WHEN** the player runs `show turn 12 known`
- **THEN** the board is drawn from the player's map as it stood after turn 12

#### Scenario: Before the game is resolved

- **WHEN** the player runs `show turn 1` while another player has not committed their setup
- **THEN** the client refuses, saying the game has not been resolved

#### Scenario: Opening a resolved game

- **WHEN** the player opens a game that has been resolved
- **THEN** the client reports the result and shows the final turn

## MODIFIED Requirements

### Requirement: Committing A Turn

The system SHALL let a player commit their setup via `commit`, after which
their setup is fixed and the client shows them the game: the record, if every
player has committed, or that it is waiting for the other players' setups.

#### Scenario: Committing

- **WHEN** the player runs `commit` and the save succeeds
- **THEN** the client confirms the commit
- **AND** if the player's was the last setup outstanding, the game is resolved and the client shows its result and final turn
- **AND** otherwise the client says whose setups are still to come

#### Scenario: Commit refused

- **WHEN** `commit` is run and the game cannot be saved
- **THEN** the client reports the problem and returns to the prompt

#### Scenario: Reloading after resolution

- **WHEN** the game has been resolved since the player committed
- **THEN** the client reloads the game and shows the result and the final turn

#### Scenario: Committing a setup with no flag

- **WHEN** the player runs `commit` during setup and no unit of theirs carries
  the flag
- **THEN** the client reports that a unit must carry the flag
- **AND** returns to the prompt with the setup unchanged

### Requirement: Reporting Rejected Orders

The system SHALL show the player, for any turn of the record they read,
everything of theirs the turn would not carry out: orders refused while being
applied, moves that could not be carried out while the turn was resolved, and
contests of theirs that ended undecided. Each SHALL name the unit, its square
and the reason, and SHALL be the player's own unit and nobody else's of the
same name.

#### Scenario: An order was rejected

- **WHEN** the player reads a turn on which one or more of their units' orders were refused
- **THEN** the client reports how many were rejected
- **AND** names the unit, its coordinates, and the reason for each

#### Scenario: A move that could not be carried out

- **WHEN** one of the player's moves was not carried out for want of energy, or because it would have left the board
- **THEN** the client reports it with that reason

#### Scenario: A contest that ended undecided

- **WHEN** one of the player's units was in a contest that ended undecided
- **THEN** the client reports it, naming the unit and the square

#### Scenario: Nothing was rejected

- **WHEN** the player reads a turn on which none of their units' orders were refused
- **THEN** nothing is reported under rejections

#### Scenario: Rejections describe only the last resolved turn

- **WHEN** the player reads a turn of the record
- **THEN** the rejections shown are that turn's alone
- **AND** no earlier turn's rejections are shown with them

#### Scenario: A destroyed unit is not reported every turn

- **WHEN** the player reads turns after one of their units was destroyed
- **THEN** nothing is reported about that unit on any of them

#### Scenario: Another player's unit of the same name

- **WHEN** another player's unit of the same name as one of the player's was in a contest
- **THEN** nothing about it is reported to the player

## REMOVED Requirements

### Requirement: Ordering Movement

**Reason**: A player gives no orders. Every move comes from a unit's
controller, running its type's program.

**Migration**: Remove `move` from the client's grammar, completion and help.
Programs are set with `set program`.

### Requirement: An Order Given And Not Committed Can Be Taken Back

**Reason**: There are no orders of the player's to take back.

**Migration**: Remove `hold` from the client's grammar, completion and help.
Programs may run `HOLD`, which is the controller's business.
