## ADDED Requirements

### Requirement: A Program May Call A Subroutine

A program SHALL be able to run the code at a label as a subroutine and come
back: `CALL label` (1 tick) continues at the label and remembers the line
after the call; `RET` (1 tick) continues at the most recently remembered
line. Calls SHALL nest to a depth of sixteen. A `RET` with no call to
return to SHALL end the run, as `HALT` does. A seventeenth nested `CALL`
SHALL halt the controller for the turn, as reaching the cap does, with the
unit left without an order and the halt recorded in its trace at the
`CALL`. The return stack SHALL belong to one run of the program and SHALL
be empty when the next run begins.

#### Scenario: A call and a return

- **WHEN** a program runs `CALL step`, and the code at `step` ends in `RET`
- **THEN** the instructions at `step` run and the program continues at the line after the `CALL`
- **AND** the `CALL` and the `RET` cost 1 tick each, and what runs between them costs what it costs

#### Scenario: Calls nest

- **WHEN** a subroutine calls another subroutine
- **THEN** each `RET` returns to the line after the call that reached it

#### Scenario: A stray return

- **WHEN** a program runs `RET` with no call to return to
- **THEN** the run ends, as at `HALT`, keeping whatever order it had set

#### Scenario: Calls too deep

- **WHEN** a program's seventeenth nested `CALL` is reached
- **THEN** the controller halts at that `CALL`, the unit has no order this turn, and the trace records the halt

#### Scenario: The stack does not outlive the run

- **WHEN** a program ends a run inside a subroutine, by `HALT` or `SLEEP`
- **THEN** the next run begins with nothing to return to

## MODIFIED Requirements

### Requirement: A Program Is Checked When It Is Set

A program SHALL be checked when it is set: an instruction that is not in the
set, a malformed operand, or a jump or call to a label that does not exist
SHALL be refused, naming the line, and the type's program SHALL be unchanged.
A program SHALL NOT be refused for what it would do.

#### Scenario: A program with an unknown instruction

- **WHEN** a player sets a program containing a line that is not an instruction
- **THEN** it is refused, naming the line
- **AND** the type's program is as it was

#### Scenario: A jump to nowhere

- **WHEN** a program jumps to a label it does not define
- **THEN** it is refused, naming the line

#### Scenario: A call to nowhere

- **WHEN** a program calls a label it does not define
- **THEN** it is refused, naming the line

#### Scenario: A sleep longer than the longest

- **WHEN** a program runs `SLEEP` with a number above 100, or below 1
- **THEN** it is refused when it is set, naming the line

#### Scenario: A program that would loop

- **WHEN** a program's only path is a loop with no exit
- **THEN** it is accepted; the cap stops it when it runs

### Requirement: Every Instruction Has One Published Cost

The system SHALL execute exactly the instructions the scenarios below name,
each costing the ticks they state, and SHALL charge no instruction by what it
returns, by the turn, or by the board. Register operands are `r0` to `r7`;
numeric operands are integers. Nothing in the set SHALL read anything but the
board as the turn began, the army's map, the flags, and the unit's own
registers, memory and inbox; nothing SHALL yield a random number or the clock.

#### Scenario: The sensors

- **WHEN** a program runs a sensor
- **THEN** `SELF` (1 tick) sets r0, r1 to my square, r2 health, r3 energy, r4 to 1 if I carry the flag, r5 to my number among my type's units
- **AND** `TURN` (1) sets r0 to the turn being resolved; `EXTENT` (1) sets r0, r1 to the board's size
- **AND** `FLAG mine` (2) and `FLAG enemy` (2) set r0, r1 to my flag's square, or the nearest standing enemy flag's, or -1, -1 if none
- **AND** `CONTACT` (2) sets r0, r1 to the square of the enemy I myself fought last turn and r2, r3 to its attack and health, or r0 to -1 if none

#### Scenario: The map

- **WHEN** a program reads the map
- **THEN** `MAP ra, rb` (3 ticks) sets r0 to 0 unknown, 1 known empty, 2 friend, 3 enemy or 4 off the board for square (ra, rb), r1 to the turn it was last known, and for an enemy r2, r3 to its attack and health as designed
- **AND** `NEAREST friend`, `NEAREST enemy` and `NEAREST unknown` (4) set r0, r1 to the nearest such square to mine and r2 to its distance, or -1, -1, -1 if none

#### Scenario: Arithmetic, memory and flow

- **WHEN** a program computes
- **THEN** `SET r, n`, `MOV r, r`, `ADD r, r|n`, `SUB r, r|n`, `ABS r`, `SIGN r` and `DIST ra, rb` (which sets r0 to the Manhattan distance from my square to (ra, rb)) cost 1 tick each
- **AND** `LOAD r, a` and `STORE r, a`, with `a` a number or a register naming a memory word, cost 1 each
- **AND** `JMP label` and `JIF cond, label`, with `cond` one of `zero r`, `notzero r`, `neg r`, `pos r`, `eq r, r`, `lt r, r`, cost 1 each; `CALL label` and `RET` cost 1 each; `HALT` costs 0

#### Scenario: The actuators

- **WHEN** a program acts
- **THEN** `MOVE dir` (1 tick), with `dir` `north`, `east`, `south`, `west` or a register holding 1 to 4, sets this turn's order, a later `MOVE` replacing an earlier; `HOLD` (1) sets the order to hold
- **AND** `SAY to, w, w, w` (5) sends three words, numbers or registers, to the friend named `to` or to `all`
- **AND** `RECV` (2) sets r0 to 1 and r1, r2, r3 to the next unread message's words, or r0 to 0 if none; `FLUSH` (1) discards every unread message
- **AND** `SLEEP n` (1), with `n` a number from 1 to 100, ends the run and switches the controller off for `n` turns

#### Scenario: Nearest is settled by position

- **WHEN** two squares are equally near
- **THEN** every `NEAREST` and `FLAG enemy` answers the one in the row nearer the seat's own edge of the board - row 0 for the player placed nearer it, the last row for the other - then the one with the lower x, so that the two seats of a mirror make mirrored choices

#### Scenario: A sensor's cost does not depend on its answer

- **WHEN** `NEAREST enemy` is run with twelve enemies on the map and again with none
- **THEN** it costs 4 ticks both times

#### Scenario: The same board gives the same orders

- **WHEN** the same program is run twice against the same snapshot, memory and inbox
- **THEN** it gives the same order, says the same words, and spends the same ticks

#### Scenario: A loop costs what it runs

- **WHEN** a program jumps backwards ten times before falling through
- **THEN** the ten jumps and everything inside them are counted in its ticks

### Requirement: Thinking Is Paid For Through The Meter

The system SHALL keep, for each unit with a controller, a tick meter of
capacity a hundred times the type's compute. Ticks a program spends SHALL be
added to it; each time it reaches capacity the unit SHALL pay 1 energy and
the meter SHALL be reduced by its capacity, carrying the remainder across
turns, so that no tick is free and a small program's cost is spread over
turns. The energy SHALL be charged in the think phase, before movement. The
point price of compute is not changed by what a point buys: a type costs the
sum of its four statistics as before.

#### Scenario: A small program over several turns

- **WHEN** a unit with compute 2 spends 60 ticks on each of four turns
- **THEN** it pays 1 energy on the fourth turn, when the meter reaches 200
- **AND** 40 ticks carry into the fifth turn

#### Scenario: Thinking leaves less for the fare

- **WHEN** a unit with 1 energy pays 1 energy to the meter and has ordered a move whose fare is 1
- **THEN** the move is refused for want of energy, as a move the unit cannot pay for is

#### Scenario: Compute buys ticks

- **WHEN** two units run the same 300-tick program every turn, one with compute 3 and one with compute 6
- **THEN** the first pays 1 energy a turn and the second 1 energy every two turns

### Requirement: A Controller Halts At The Cap

A controller SHALL halt for the turn when its program has spent a hundred
times the type's compute in ticks within that turn, so that thinking never
costs more than 1 energy in one turn, and SHALL halt when the meter would
charge energy the unit does not have. A halted controller SHALL leave the
unit with no order for the turn, whatever `MOVE` it had run, and the halt
SHALL be recorded in the unit's trace with the instruction it stopped at.

#### Scenario: Thinking within a turn

- **WHEN** a unit with compute 5 spends 500 ticks in one turn
- **THEN** it pays 1 energy and halts at the five-hundredth tick

#### Scenario: Thinking when the energy is gone

- **WHEN** a unit with 0 energy runs a program whose ticks would fill the meter
- **THEN** it halts at the instruction that would have filled it
- **AND** it gives no order this turn

#### Scenario: A halted program's order is dropped

- **WHEN** a program runs `MOVE north` and then halts at the cap
- **THEN** the unit holds this turn
- **AND** its trace says it halted and at which instruction
