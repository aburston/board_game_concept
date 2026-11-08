# Spec Delta

## Purpose

The controller a unit runs: a program its type carries, executed every turn
by each unit of the type against what its army knows, paying for every
instruction in energy by a published tariff. This is what makes a unit a robot
rather than a piece - it senses, thinks, orders itself, talks to its friends
and sleeps - and it is what the game was named for.

## ADDED Requirements

### Requirement: A Type Carries A Program

The system SHALL let a unit type with compute above 0 carry a program, set
during setup and fixed when its owner's setup is committed, and SHALL run it
for every unit of the type on every turn the unit is on the board, awake and
not destroyed. A program SHALL be a sequence of instructions from the set
below, one per line, with optional labels and comments, and MAY be empty. A
type with compute 0 SHALL carry no program, having no controller to run one.

#### Scenario: Setting a program on a type

- **WHEN** a player sets a program on one of their types during setup
- **THEN** every unit of that type runs it from the first turn of play

#### Scenario: A type with a controller and no program

- **WHEN** a type with compute above 0 carries no program
- **THEN** its units are legal and do nothing of their own accord

#### Scenario: A program on a type with no controller

- **WHEN** a player sets a program on a type with compute 0
- **THEN** it is refused, saying the type has no controller

#### Scenario: A program is fixed at commit

- **WHEN** a player's setup has been committed
- **THEN** setting a program on any of their types is refused, as redefining a type is

#### Scenario: Redefining a type replaces its program

- **WHEN** a player redefines a type under its own name during setup
- **THEN** its units run the program the redefinition carries, or none if it carries none

### Requirement: Units Of One Type Share Code And Nothing Else

Every unit of a type SHALL run the same program, and each unit SHALL have its
own registers, memory, meter, sleep state and inbox, none of which another
unit can read or write. A program SHALL be able to tell which unit is running
it, by the unit's number among the units of its type, so that one program can
give different units different roles.

#### Scenario: Two units of one type

- **WHEN** two units of one type run their program in the same turn
- **THEN** each reads its own registers, memory, meter, sleep state and inbox
- **AND** neither can read or write the other's

#### Scenario: A unit knows which it is

- **WHEN** the third unit of a type, in name order, runs `SELF`
- **THEN** it reads 2 as its number, and the first reads 0

### Requirement: A Program Is Checked When It Is Set

A program SHALL be checked when it is set: an instruction that is not in the
set, a malformed operand, or a jump to a label that does not exist SHALL be
refused, naming the line, and the type's program SHALL be unchanged. A
program SHALL NOT be refused for what it would do.

#### Scenario: A program with an unknown instruction

- **WHEN** a player sets a program containing a line that is not an instruction
- **THEN** it is refused, naming the line
- **AND** the type's program is as it was

#### Scenario: A jump to nowhere

- **WHEN** a program jumps to a label it does not define
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
- **AND** `JMP label` and `JIF cond, label`, with `cond` one of `zero r`, `notzero r`, `neg r`, `pos r`, `eq r, r`, `lt r, r`, cost 1 each; `HALT` costs 0

#### Scenario: The actuators

- **WHEN** a program acts
- **THEN** `MOVE dir` (1 tick), with `dir` `north`, `east`, `south`, `west` or a register holding 1 to 4, sets this turn's order, a later `MOVE` replacing an earlier; `HOLD` (1) sets the order to hold
- **AND** `SAY to, w, w, w` (5) sends three words, numbers or registers, to the friend named `to` or to `all`
- **AND** `RECV` (2) sets r0 to 1 and r1, r2, r3 to the next unread message's words, or r0 to 0 if none; `FLUSH` (1) discards every unread message
- **AND** `SLEEP n` (1), with `n` a number from 1 to 100, ends the run and switches the controller off for `n` turns

#### Scenario: Nearest is settled by position

- **WHEN** two squares are equally near
- **THEN** every `NEAREST` and `FLAG enemy` answers the one with the lower y, then the lower x

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
capacity ten times the type's compute. Ticks a program spends SHALL be added
to it; each time it reaches capacity the unit SHALL pay 1 energy and the
meter SHALL be reduced by its capacity, carrying the remainder across turns,
so that no tick is free and a small program's cost is spread over turns. The
energy SHALL be charged in the think phase, before movement.

#### Scenario: A small program over several turns

- **WHEN** a unit with compute 2 spends 6 ticks on each of four turns
- **THEN** it pays 1 energy on the fourth turn, when the meter reaches 20
- **AND** 4 ticks carry into the fifth turn

#### Scenario: Thinking leaves less for the fare

- **WHEN** a unit with 1 energy pays 1 energy to the meter and has ordered a move whose fare is 1
- **THEN** the move is refused for want of energy, as a move the unit cannot pay for is

#### Scenario: Compute buys ticks

- **WHEN** two units run the same 30-tick program every turn, one with compute 3 and one with compute 6
- **THEN** the first pays 1 energy a turn and the second 1 energy every two turns

### Requirement: A Controller Halts At The Cap

A controller SHALL halt for the turn when its program has spent ten times the
type's compute in ticks within that turn, so that thinking never costs more
than 1 energy in one turn, and SHALL halt when the meter would charge energy
the unit does not have. A halted controller SHALL leave the unit with no
order for the turn, whatever `MOVE` it had run, and the halt SHALL be
recorded in the unit's trace with the instruction it stopped at.

#### Scenario: Thinking within a turn

- **WHEN** a unit with compute 5 spends 50 ticks in one turn
- **THEN** it pays 1 energy and halts at the fiftieth tick

#### Scenario: Thinking when the energy is gone

- **WHEN** a unit with 0 energy runs a program whose ticks would fill the meter
- **THEN** it halts at the instruction that would have filled it
- **AND** it gives no order this turn

#### Scenario: A halted program's order is dropped

- **WHEN** a program runs `MOVE north` and then halts at the cap
- **THEN** the unit holds this turn
- **AND** its trace says it halted and at which instruction

### Requirement: Sleep Is How A Unit Rests

The system SHALL switch a unit's controller off for `n` turns, `n` being 1 to
100, when its program runs `SLEEP n`; no sleep SHALL last longer. A sleeping
unit SHALL give no order, spend no ticks, and recover energy under the rest
rule like any unit that did nothing. Being in a fight SHALL wake it: the
exchange is fought on the ordinary terms, and its controller runs again on
the next turn, whatever `n` remained. Nothing else SHALL wake a sleeper; a
message SHALL NOT.

#### Scenario: Sleeping and resting

- **WHEN** a unit runs `SLEEP 3` on a turn and is not attacked
- **THEN** its controller does not run on the next three turns
- **AND** it recovers 1 energy on each of them, up to the energy its type was designed with

#### Scenario: The longest sleep

- **WHEN** a unit runs `SLEEP 100` and is never attacked
- **THEN** its controller runs again on the hundred-and-first turn, so no unit is dormant for free
- **AND** sleeping again costs it the tick of another `SLEEP`

#### Scenario: Woken by a blow

- **WHEN** a sleeping unit's square is contested
- **THEN** it strikes every other unit in the square if it can pay its attack, as a waking unit would
- **AND** its controller runs on the next turn

#### Scenario: A message does not wake a sleeper

- **WHEN** a friend sends a sleeping unit a message
- **THEN** the sleeper's controller does not run until its sleep ends
- **AND** the message waits in its inbox

#### Scenario: A sleeping unit pays nothing to its meter

- **WHEN** a unit sleeps for three turns
- **THEN** its meter is unchanged by them

### Requirement: The Army Shares One Map

The system SHALL keep, for each player, one map of the board as that player's
army knows it, and SHALL give every unit of the army with a controller the
same map to read. The map SHALL be updated when the turn resolves, from every
friendly unit's contact at once, and read by every controller as it stood
when the turn began. Holding it SHALL cost nothing; reading it SHALL cost the
ticks the instruction set says. A type with compute 0 SHALL contribute to the
map and read nothing from it.

#### Scenario: An enemy met by one unit is known to all

- **WHEN** one unit of an army fights an enemy on a square
- **THEN** on the next turn every controller of that army reads that square as holding that enemy, with its design and the turn it was met

#### Scenario: The map is read as the turn began

- **WHEN** a unit walks onto a square this turn
- **THEN** no controller reads the square as known until the next turn

#### Scenario: A turret feeds the map

- **WHEN** a unit of a type with compute 0 fights an enemy
- **THEN** its army's map holds that enemy from the next turn
- **AND** the turret itself reads nothing

### Requirement: A Square Is Known Only By Standing Or Fighting On It

The map SHALL hold, for each square: that it is unknown; that it was known
empty, with the last turn a friendly unit stood on it; that a friend stands
on it; or that an enemy was met on it, with the turn it was met and the
attack and health its type was designed with. It SHALL hold the square of
every standing flag. A square SHALL become known only by a friendly unit
standing or fighting on it: nothing is sensed from a distance.

#### Scenario: A square walked on

- **WHEN** a friendly unit ends a turn on a square where it met nothing
- **THEN** every controller of that army reads the square as known empty, as of that turn, from the next turn on

#### Scenario: The map is not a sensor

- **WHEN** an enemy stands on a square no friendly unit has stood on or fought on
- **THEN** every controller of that army reads the square as unknown

#### Scenario: Stale knowledge stays stamped

- **WHEN** an enemy was met on a square five turns ago and nothing has stood there since
- **THEN** the map still reads the square as holding that enemy, met five turns ago
- **AND** a program can tell how old the sighting is from the turn it reads

#### Scenario: Friends are always on the map

- **WHEN** a controller reads the square of any of its army's units
- **THEN** it reads a friend there, as of the turn being resolved

### Requirement: The Radio Carries Three Words

The system SHALL deliver a message a program sends with `SAY` to the named
friendly unit, or to every friendly unit with a controller when sent to
`all`, anywhere on the board, at the start of the next turn's think phase. A
message SHALL be three integers and nothing else. A message to a unit that is
not the sender's, or does not exist, SHALL be dropped and recorded in the
sender's trace.

#### Scenario: A targeted message

- **WHEN** a unit's program runs `SAY runner1, 7, 3, 5` on turn 4
- **THEN** on turn 5 the friendly unit `runner1` reads 7, 3, 5 from its inbox
- **AND** no other unit does

#### Scenario: A broadcast

- **WHEN** a unit's program runs `SAY all, 1, 0, 0`
- **THEN** on the next turn every friendly unit with a controller has that message in its inbox
- **AND** no enemy unit does

#### Scenario: A message to an enemy

- **WHEN** a program names an enemy unit as the recipient
- **THEN** nothing is delivered
- **AND** the sender's trace records the message as dropped

### Requirement: The Inbox Persists And Is Ordered

Each unit's inbox SHALL hold every message delivered to it until it is read
with `RECV` or discarded with `FLUSH`, without limit and without expiry.
Messages SHALL be delivered in a settled order: by the turn they were sent,
then by the sender's name, then in the order the sender's program said them.

#### Scenario: The inbox persists

- **WHEN** a unit is sent four messages over four turns and reads none of them
- **THEN** on the fifth turn `RECV` returns them one at a time, oldest first

#### Scenario: Messages arrive in a settled order

- **WHEN** two friends each send a unit a message on the same turn
- **THEN** the unit reads the one from the sender with the lower name first, whichever program ran first

#### Scenario: A sleeper's inbox fills

- **WHEN** a unit sleeps three turns and is sent a message on each
- **THEN** on waking it reads all three, oldest first

### Requirement: The Controller Trace Is Kept For Its Owner

The system SHALL record, for every unit with a controller on every turn, what
its controller did, as part of the game's record, readable by the unit's
owner and by the observer and by no other seat. Neither a type's program nor
its compute SHALL be readable by another seat: contact discloses a type's
attack, health and energy, and nothing discloses how it thinks.

#### Scenario: Reading a unit's trace

- **WHEN** a seat reads the record of a turn
- **THEN** for each of its own units it reads the ticks spent, the energy charged, the order given, the messages said and any dropped, whether it slept and for how long, whether it was woken, and whether it halted

#### Scenario: A halt is traced

- **WHEN** a controller halts at the cap
- **THEN** its owner reads, against that turn, that it halted and at which instruction

#### Scenario: Another seat's trace is withheld

- **WHEN** a seat reads the record of a turn
- **THEN** nothing of any other seat's controllers is in it: not their ticks, their orders, their words or their programs
