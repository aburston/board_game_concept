# Spec Delta

## Purpose

The controller a unit runs: a program its type carries, executed every turn
by each unit of the type against what its army knows, paying for every
instruction in energy by a published tariff. This is what makes a unit a robot
rather than a piece - it senses, thinks, orders itself, talks to its friends
and sleeps - and it is what the game was named for.

## ADDED Requirements

### Requirement: A Type Carries A Program

The system SHALL let a unit type carry a program, set during setup and fixed
when its owner's setup is committed, and SHALL run that program for every
unit of the type on every turn the unit is on the board, awake and not
destroyed. A program SHALL be a sequence of instructions from the instruction
set below, one per line, with optional labels and comments. A type with
compute 0 SHALL carry no program, because it has no controller to run one. A
type with compute above 0 and no program SHALL be legal: its units do nothing
of their own accord.

Every unit of a type SHALL run the same program, and each unit SHALL have its
own registers, memory, meter, sleep state and inbox. The program SHALL be able
to tell which unit is running it, by the unit's number among the units of its
type, so that one program can give different units different roles.

A program SHALL be checked when it is set: an instruction that is not in the
set, a malformed operand, or a jump to a label that does not exist SHALL be
refused, naming the line. A program SHALL NOT be refused for what it would do.

#### Scenario: Setting a program on a type

- **WHEN** a player sets a program on one of their types during setup
- **THEN** every unit of that type runs it from the first turn of play

#### Scenario: Two units of one type

- **WHEN** two units of one type run their program in the same turn
- **THEN** each reads its own registers, memory, meter, sleep state and inbox
- **AND** neither can read or write the other's

#### Scenario: A program on a type with no controller

- **WHEN** a player sets a program on a type with compute 0
- **THEN** it is refused, saying the type has no controller

#### Scenario: A program with an unknown instruction

- **WHEN** a player sets a program containing a line that is not an instruction
- **THEN** it is refused, naming the line

#### Scenario: A program is fixed at commit

- **WHEN** a player's setup has been committed
- **THEN** setting a program on any of their types is refused, as redefining a type is

#### Scenario: Redefining a type replaces its program

- **WHEN** a player redefines a type under its own name during setup
- **THEN** its units run the program the redefinition carries, or none if it carries none

### Requirement: The Instruction Set And Its Tick Table

The system SHALL execute exactly the instructions below, each costing the
ticks beside it, and SHALL charge no instruction by what it returns, by the
turn, or by the board. Register operands are `r0` to `r7`; numeric operands
are integers; where an operand may be either, the table says so.

| Instruction | Does | Ticks |
|---|---|---|
| `SELF` | r0, r1 = my square; r2 = health; r3 = energy; r4 = 1 if I carry the flag else 0; r5 = my number among my type's units | 1 |
| `TURN` | r0 = the turn being resolved | 1 |
| `EXTENT` | r0, r1 = the board's size | 1 |
| `FLAG mine` | r0, r1 = my flag's square, or -1, -1 if it has fallen | 2 |
| `FLAG enemy` | r0, r1 = the nearest standing enemy flag's square, or -1, -1 if none | 2 |
| `MAP ra, rb` | what my army knows of square (ra, rb): r0 = 0 unknown, 1 known empty, 2 friend, 3 enemy, 4 off the board; r1 = the turn it was last known; for an enemy r2, r3 = its attack and health as its type was designed | 3 |
| `NEAREST friend` / `NEAREST enemy` / `NEAREST unknown` | r0, r1 = the nearest such square to mine, r2 = its distance; -1, -1, -1 if none | 4 |
| `CONTACT` | the enemy I myself fought last turn: r0, r1 = its square, r2, r3 = its attack and health; -1 in r0 if none | 2 |
| `RECV` | the next unread message: r0 = 1 and r1, r2, r3 = its three words; r0 = 0 if none | 2 |
| `FLUSH` | discards every unread message | 1 |
| `SET r, n` / `MOV r, r` | assign | 1 |
| `ADD r, r\|n` / `SUB r, r\|n` | arithmetic | 1 |
| `ABS r` / `SIGN r` | absolute value; -1, 0 or 1 | 1 |
| `DIST ra, rb` | r0 = the Manhattan distance from my square to (ra, rb) | 1 |
| `LOAD r, a` / `STORE r, a` | memory word `a` (a number or a register) | 1 |
| `JMP label` | jump | 1 |
| `JIF cond, label` | jump if `zero r`, `notzero r`, `neg r`, `pos r`, `eq r, r` or `lt r, r` | 1 |
| `MOVE dir` | this turn's order; `dir` is `north`, `east`, `south`, `west` or a register holding 1 to 4; a later `MOVE` replaces an earlier | 1 |
| `HOLD` | this turn's order is to hold | 1 |
| `SAY to, w, w, w` | three words (numbers or registers) to the friend named `to`, or to `all` | 5 |
| `SLEEP n` | ends this turn's run; the controller does not run for the next `n` turns | 1 |
| `HALT` | ends this turn's run | 0 |

Every instruction that answers "nearest" SHALL break ties by the lowest y,
then the lowest x, so the same board gives the same answer. Nothing in the
set SHALL read anything but the board as the turn began, the army's map, the
unit's own registers, memory and inbox, and the flags. There SHALL be no
instruction that yields a random number, the clock, or anything that differs
between two runs of the same game.

#### Scenario: Every instruction costs what the table says

- **WHEN** a program runs `SELF`, `FLAG enemy`, `SUB r0, r2`, `SIGN r0`, `MOVE r0`
- **THEN** its run cost 1 + 2 + 1 + 1 + 1 = 6 ticks, on every board and every turn

#### Scenario: A sensor's cost does not depend on its answer

- **WHEN** `NEAREST enemy` is run with twelve enemies on the map and again with none
- **THEN** it costs 4 ticks both times

#### Scenario: The same board gives the same orders

- **WHEN** the same program is run twice against the same snapshot, memory and inbox
- **THEN** it gives the same order, says the same words, and spends the same ticks

#### Scenario: A later order replaces an earlier

- **WHEN** a program runs `MOVE north` and later `MOVE east` in one turn
- **THEN** the unit's order for the turn is east

#### Scenario: A loop costs what it runs

- **WHEN** a program jumps backwards ten times before falling through
- **THEN** the ten jumps and everything inside them are counted in its ticks

### Requirement: Thinking Is Paid For Through The Meter

The system SHALL keep, for each unit with a controller, a tick meter of
capacity ten times the type's compute. Each tick a program spends SHALL be
added to the meter; each time the meter reaches its capacity the unit SHALL
pay 1 energy and the meter SHALL be reduced by its capacity, carrying the
remainder. The meter SHALL persist across turns, so that a small program's
cost is spread over several turns and no tick is ever free.

A controller SHALL halt for the turn when its program has spent ten times the
type's compute in ticks within that turn, so that thinking never costs more
than 1 energy in one turn, and SHALL halt when the meter would charge energy
the unit does not have. A controller that halts SHALL leave the unit with no
order for the turn, whatever `MOVE` it had run, and the halt SHALL be
recorded in the unit's trace.

Energy the meter charges SHALL be charged in the think phase, before movement,
so that a unit's fare is paid from what thinking left it.

#### Scenario: A small program over several turns

- **WHEN** a unit with compute 2 spends 6 ticks on each of four turns
- **THEN** it pays 1 energy on the fourth turn, when the meter reaches 20
- **AND** 4 ticks carry into the fifth turn

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
- **AND** its trace says it halted

#### Scenario: Thinking leaves less for the fare

- **WHEN** a unit with 1 energy pays 1 energy to the meter and has ordered a move whose fare is 1
- **THEN** the move is refused for want of energy, as a move the unit cannot pay for is

### Requirement: Sleep Is How A Unit Rests

The system SHALL switch a unit's controller off for `n` turns when its program
runs `SLEEP n`. A sleeping unit SHALL give no order, SHALL spend no ticks,
and SHALL recover energy under the rest rule like any unit that did nothing.
A sleeping unit SHALL be woken by being in a fight: the exchange is fought on
the ordinary terms - it strikes back if it can pay its attack - and its
controller runs again on the next turn, whatever `n` remained. Nothing else
SHALL wake a sleeper; in particular a message SHALL NOT.

#### Scenario: Sleeping and resting

- **WHEN** a unit runs `SLEEP 3` on a turn and is not attacked
- **THEN** its controller does not run on the next three turns
- **AND** it recovers 1 energy on each of them, up to the energy its type was designed with

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

The system SHALL keep, for each player, a map of the board as that player's
army knows it, and SHALL give every unit of the army with a controller the
same map to read. The map SHALL hold, for each square: that it is unknown;
that it was known empty, and the last turn a friendly unit stood on it; that
a friend stands on it; or that an enemy was met on it, with the turn it was
met and the attack and health its type was designed with. It SHALL hold the
square of every standing flag. A square SHALL become known only by a friendly
unit standing on it or fighting on it: nothing is sensed from a distance.

The map SHALL be updated when the turn resolves, from every friendly unit's
contact at once, and SHALL be read by every controller as it stood when the
turn began. Holding the map SHALL cost nothing; reading it SHALL cost the
ticks the instruction set says.

A type with compute 0 SHALL contribute what its units fight to the map and
SHALL read nothing from it, having no controller.

#### Scenario: A square walked on

- **WHEN** a friendly unit ends a turn on a square where it met nothing
- **THEN** every controller of that army reads the square as known empty, as of that turn, from the next turn on

#### Scenario: An enemy met by one unit is known to all

- **WHEN** one unit of an army fights an enemy on a square
- **THEN** on the next turn every controller of that army reads that square as holding that enemy, with its design and the turn it was met

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
`all`, anywhere on the board, at the start of the next turn's think phase.
A message SHALL be three integers and nothing else. Each unit's inbox SHALL
hold every message delivered to it until it is read with `RECV` or discarded
with `FLUSH`, without limit and without expiry. Messages SHALL be delivered in
a settled order: by the turn they were sent, then by the sender's name, then
in the order the sender's program said them. A message to a unit that is not
the sender's, or does not exist, SHALL be dropped and recorded in the
sender's trace.

#### Scenario: A targeted message

- **WHEN** a unit's program runs `SAY runner1, 7, 3, 5` on turn 4
- **THEN** on turn 5 the friendly unit `runner1` reads 7, 3, 5 from its inbox
- **AND** no other unit does

#### Scenario: A broadcast

- **WHEN** a unit's program runs `SAY all, 1, 0, 0`
- **THEN** on the next turn every friendly unit with a controller has that message in its inbox
- **AND** no enemy unit does

#### Scenario: The inbox persists

- **WHEN** a unit is sent four messages over four turns and reads none of them
- **THEN** on the fifth turn `RECV` returns them one at a time, oldest first

#### Scenario: Messages arrive in a settled order

- **WHEN** two friends each send a unit a message on the same turn
- **THEN** the unit reads the one from the sender with the lower name first, whichever program ran first

#### Scenario: A message to an enemy

- **WHEN** a program names an enemy unit as the recipient
- **THEN** nothing is delivered
- **AND** the sender's trace records the message as dropped

### Requirement: The Controller Trace Is Kept For Its Owner

The system SHALL record, for every unit with a controller on every turn, what
its controller did: the ticks spent, the energy the meter charged, the order
it gave, the messages it said and any that were dropped, whether it slept and
for how long, whether it was woken, and whether it halted and at which
instruction. The trace SHALL be part of the game's record and SHALL be
readable by the unit's owner and by the observer. It SHALL NOT be readable by
another seat, and neither SHALL a type's program or its compute: contact
discloses a type's attack, health and energy, and nothing discloses how it
thinks.

#### Scenario: Reading a unit's trace

- **WHEN** a seat reads the record of a turn
- **THEN** for each of its own units it reads the ticks spent, the energy charged, the order given and what was said

#### Scenario: A halt is traced

- **WHEN** a controller halts at the cap
- **THEN** its owner reads, against that turn, that it halted and at which instruction

#### Scenario: Another seat's trace is withheld

- **WHEN** a seat reads the record of a turn
- **THEN** nothing of any other seat's controllers is in it: not their ticks, their orders, their words or their programs
