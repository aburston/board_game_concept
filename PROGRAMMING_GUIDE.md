# Programming Units: A Development Guide

This guide covers how to write the programs your unit types run. It explains
the machine, the syntax and the costs, gives a complete reference for every
instruction, and ends with worked examples, common patterns and a way to test
a program before you commit it.

Everything here was checked against the interpreter in
`src/board_game_concept/domain/program.py` and the think phase in
`src/board_game_concept/domain/board.py`. The rules behind it are
`GAME_RULES.md` **R10** and `openspec/specs/unit-program/spec.md`. If this
guide disagrees with the code, the code is right; please fix the guide.

---

## Contents

1. [What a program is](#1-what-a-program-is)
2. [Getting a program onto a type](#2-getting-a-program-onto-a-type)
3. [The machine](#3-the-machine)
4. [Source syntax](#4-source-syntax)
5. [How a run works](#5-how-a-run-works)
6. [Paying for thought: the cap and the meter](#6-paying-for-thought-the-cap-and-the-meter)
7. [Instruction reference](#7-instruction-reference)
8. [Quick reference card](#8-quick-reference-card)
9. [Determinism and tie-breaking](#9-determinism-and-tie-breaking)
10. [Patterns and idioms](#10-patterns-and-idioms)
11. [Worked examples](#11-worked-examples)
12. [Testing and debugging](#12-testing-and-debugging)
13. [Pitfalls](#13-pitfalls)

---

## 1. What a program is

Players give no orders during play. Once every setup is committed, the game
plays itself to the end, and every move a unit makes comes from its
**controller**: a small register machine that runs its type's **program** once
per turn.

- A program belongs to a **unit type**. Every unit of that type runs the same
  code, but each unit has its own registers, memory, inbox, meter and sleep
  state.
- Only a type with **compute above 0** has a controller. A compute-0 type
  (a wall or turret) has no program, and setting one on it is refused.
- A program runs in the **think phase**, the first of the six phases of a
  turn. It reads the board as the turn began and decides on one order for its
  unit: a step north, east, south or west, or nothing. It can also send
  messages to friendly units and put its unit to sleep.
- Thinking costs **energy**, from the same pool the unit spends on moving and
  striking. Every instruction has a fixed price in **ticks**, and ticks are
  converted to energy through a meter (see [section 6](#6-paying-for-thought-the-cap-and-the-meter)).

A turn, from a controller's point of view:

```
think    every awake controller runs once, against a snapshot of the board
         taken before any of them ran. Orders, messages, sleep, meter charge.
deploy   (setup turn only)
move     every order is applied at once
combat   every square holding more than one unit is fought out
map      each army's shared map is updated; struck sleepers are woken
rest     every standing unit recovers 2 energy, up to its design maximum
```

Messages sent this turn are delivered after every controller has run, so they
are read on the **next** turn. The map your program reads is the map as it was
at the end of the **previous** turn.

---

## 2. Getting a program onto a type

A program is plain text, conventionally saved with a `.asm` extension. You can
set it any time during setup, until you commit. After the commit it is fixed.

**Command line (`bgcclient`):**

```
bgcclient> add type Guard g 2 4 10 5
bgcclient> set program Guard guard.asm
bgcclient> show program Guard
```

`set program` reads the file on the machine where the client runs, checks it,
and lists it back with the tick cost of each line. `show program <type>` lists
any type you are allowed to read, with per-line ticks and the per-turn cap the
type's compute buys.

**Web interface:** the armoury has a program editor for each type with
compute. It prices every line as you type, using the same tariff the server
charges, and shows the total against the type's cap.

**Match doctrines (`matches/bots/*.yaml`):** a type's `program:` key names a
file, relative to the YAML file:

```yaml
types:
  - {name: Lance, symbol: '!', attack: 8, health: 2, energy: 10, compute: 4, program: programs/hunter9.asm}
```

**Checking happens when you set the program.** An unknown instruction, a
malformed operand, a `SLEEP` outside 1 to 100, or a jump or call to a label
that does not exist is refused with the line number, for example
`line 7: operand 2 of SET must be int, not '0x10'`. The type keeps its
previous program. A program is never refused for what it would *do*: an
infinite loop is accepted, and the cap stops it when it runs.

**Default programs.** Every type in the stock catalogue (`domain/army.py`)
ships with a program. These are good starting points to read and adapt:

| Program | Used by | What it does |
|---|---|---|
| `HUNTER` | Runner, Line, Lance, Heavy | Walks towards the nearest enemy flag, going round its own units. Sleeps if it can't afford a step and a strike. |
| `EXPLORER` | Scout | Walks towards the nearest unknown square, sidesteps obstacles, and gives up after 20 turns without progress. |
| `VANGUARD` | Pawn | Steps towards the enemy's edge of the board, never onto a friend. |
| `WARDEN` | Keep | `SLEEP 100`. It wakes only when struck. |

Run `show program Runner` (or any other type) in a session to see one.

---

## 3. The machine

| Part | Size | Lifetime | Notes |
|---|---|---|---|
| Registers `r0` to `r7` | 8 integers | **One run.** All are 0 at the start of every turn. | Many sensors write into `r0` to `r5`; see the [clobber table](#register-clobber-table). |
| Memory | Unbounded, integer address to integer value | **The unit's life.** Persists across turns. | Unwritten addresses read as 0. Any integer is a valid address, including negative ones. Holding memory is free. |
| Inbox | Unbounded queue of 3-word messages | **The unit's life.** | Filled by friends' `SAY`. Read oldest first with `RECV`; emptied with `FLUSH`. Messages never expire. |
| Return stack | Up to 16 entries | **One run.** | Used by `CALL` and `RET`. |
| Meter | 0 to `100 × compute − 1` ticks | **The unit's life.** | Converts ticks into energy. |
| Sleep counter | 0 to 100 turns | **Until it counts down or a blow wakes the unit.** | Set by `SLEEP`. |
| Program counter | | **One run.** | Every run starts at the first instruction. |

Values are integers with no overflow. There is no multiply, divide, bitwise
operation or random number. There is no clock, and nothing that differs
between two runs given the same board, memory and inbox.

**What a program can see:**

- its own unit (`SELF`): square, current health, current energy, whether it
  carries the flag, and its number among its type's units
- the turn number (`TURN`) and the board size (`EXTENT`)
- the flags' squares (`FLAG`). Every flag's square is public.
- the enemy its own unit fought last turn (`CONTACT`)
- the army's **shared map** (`MAP`, `NEAREST`)
- its own memory and inbox

The shared map is the army's knowledge of the board. A square becomes known
only when one of your units stands on it or fights on it. Nothing is sensed
from a distance. For each square the map holds one of:

| `MAP` code | Meaning | `r1` (turn) | `r2`, `r3` |
|---|---|---|---|
| `0` unknown | No unit of yours has stood or fought here | -1 | -1, -1 |
| `1` empty | A unit of yours stood here, and nothing was met since | last turn stood on | -1, -1 |
| `2` friend | One of your units stands here now | current turn | -1, -1 |
| `3` enemy | An enemy was met here | turn it was met | its **designed** attack, health |
| `4` off the board | The coordinates are outside the board | -1 | -1, -1 |

A remembered enemy stays on the map until one of your units stands on that
square, or meets that enemy somewhere else. The map is not told when an enemy
walks away, so check the turn stamp in `r1` to judge how stale a sighting is.

---

## 4. Source syntax

```
; a comment runs from ';' to the end of the line
label:  OPCODE operand, operand   ; a label can share a line with an instruction
other:                            ; or stand on a line of its own
        OPCODE operand operand    ; commas and spaces are interchangeable
```

- **One instruction per line.** Blank lines and comment-only lines are ignored.
  Error messages give the source line number, counting every line.
- **Opcodes are case-insensitive.** `MOVE`, `move` and `Move` are the same.
  This guide writes them in upper case.
- **Everything else is case-sensitive.** Registers must be lower-case `r0` to
  `r7` (`R1` is refused). The words `north`, `mine`, `enemy`, `zero`, `all`
  and so on must be lower case. Labels are case-sensitive.
- **Labels** match `[A-Za-z_][A-Za-z0-9_-]*`, followed by a colon at the start
  of a line. Each label may be defined only once. A label refers to the next
  instruction after it; a label at the end of the file refers to "the end",
  where the run stops.
- **Operands** are separated by commas, whitespace, or both. Each one is:
  - a **register**: `r0` to `r7`
  - an **integer**: decimal, optionally negative (`-1`, `42`). Hex and other
    bases are not accepted.
  - a **word**: anything else, such as a label, direction, condition or unit
    name.
- Each instruction accepts specific kinds of operand. For example,
  `MAP 1, 2` is refused because `MAP` takes registers only, and
  `DIST r1, 3` is refused for the same reason. See the
  [reference](#7-instruction-reference).

---

## 5. How a run works

Each turn, an awake unit with a controller and a program runs once:

1. Registers are set to 0, the return stack is cleared, and execution starts
   at the first instruction.
2. Instructions run in order. Jumps, calls and returns move the program
   counter.
3. Before each instruction, the machine checks two limits (see
   [section 6](#6-paying-for-thought-the-cap-and-the-meter)). If either would
   be exceeded, the controller **halts** at that instruction.
4. The run ends at the first of these:

| Ends by | Order for the turn | Messages said | Sleep | Trace |
|---|---|---|---|---|
| Running past the last instruction | **kept** | sent | none | normal |
| `HALT` | **kept** | sent | none | normal |
| `RET` with an empty return stack | **kept** | sent | none | normal |
| `SLEEP n` | **kept** | sent | `n` turns | records the sleep |
| Hitting the per-turn tick cap | **dropped** | sent | none | `halted` at that line |
| The meter needing energy the unit doesn't have | **dropped** | sent | none | `halted` at that line |
| A 17th nested `CALL` | **dropped** | sent | none | `halted` at the `CALL` |

**The order.** `MOVE` and `HOLD` set the turn's order. A later one replaces an
earlier one, and nothing is applied until the run ends. A `MOVE` through a
register that doesn't hold 1 to 4 does nothing, and any earlier order stands.
If the run ends without any `MOVE` or `HOLD`, the unit stays where it is. That
has the same effect as `HOLD`, but costs one tick less.

**Sleep keeps the order.** `MOVE north` followed by `SLEEP 3` moves north this
turn, then sleeps for the next three turns.

**A halt drops the order but not the bill.** Every tick spent before a halt is
still charged to the meter, and any `SAY` already executed is still delivered.

### Sleeping and waking

`SLEEP n` (1 to 100) turns the controller off for the next `n` turns. A
sleeping unit spends no ticks and gives no order, but it still recovers 2
energy a turn and still strikes back at whatever walks into it.

- **Only a blow wakes a sleeper.** If the unit was in a contest on its square,
  its sleep is cancelled at the end of that turn and its controller runs next
  turn. Use `CONTACT` then to see what hit it.
- **Messages do not wake a sleeper.** They wait in the inbox.
- `SLEEP 1` means "skip one turn", so a program that always ends in `SLEEP 1`
  runs every other turn.

### Unit numbers

`SELF` puts the unit's number among its type's units into `r5`, counting from
0. Units are numbered in **name order**, counting every unit of the type the
player deployed, destroyed or not, so a unit's number never changes.

The sort is by string, so `lance10` comes before `lance2`. If the numbering
matters, give the units names that sort the way you mean them to, such as
`lance01`, `lance02` and so on.

---

## 6. Paying for thought: the cap and the meter

Let `cap = 100 × compute`.

**The cap.** A run may spend at most `cap` ticks in one turn. The instruction
that would take it past the cap is not executed: the controller halts there,
and the order is dropped.

**The meter.** Every tick spent is added to the unit's meter. Each time the
meter reaches `cap`, the unit pays **1 energy** and the meter drops by `cap`.
The remainder carries over to the next turn. The charge is taken in the think
phase, before movement, so thinking can leave a unit unable to pay for the
move it just ordered. When that happens the move is refused and reported.

**Running out of energy.** If an instruction would fill the meter and the unit
doesn't have the energy to pay, the controller halts at that instruction. A
unit with 0 energy can still think until its meter is about to fill.

Some consequences:

- Thinking never costs more than **1 energy per turn**, because the cap is
  equal to the meter's size.
- A program that reaches the cap every turn pays 1 energy a turn and gives
  **no order** for it. That is the worst case.
- A program spending `t` ticks every turn on compute `c` pays 1 energy every
  `100c ÷ t` turns. For example, on compute 2 a 60-tick program pays on turn 4
  (meter 240, charge 1, carry 40), and the next charge comes sooner because
  of the carry.
- Ticks are charged **per instruction executed**, not per line. A loop body
  that runs ten times is paid for ten times.
- No instruction costs more or less depending on what it returns.
  `NEAREST enemy` costs 4 ticks whether the map holds twelve enemies or none,
  so a program's cost on a given path is the same on every board.

**Budgeting a program.** Work out your longest path through the code (the
default `HUNTER` is 33 ticks), then pick a compute value whose cap covers it
with room to spare. The armoury editor and `show program` show the
*straight-line* total, which is every instruction counted once. That is not
the same as the longest path when your code loops or skips sections. Loops
need counting by hand.

Remember that compute is also bought with points: a type costs
`attack + health + energy + compute`.

---

## 7. Instruction reference

Notation: `rA`, `rB` stand for registers (`r0` to `r7`). `n` is an integer
literal. `rB|n` means either a register or an integer literal. `label` is a
label defined somewhere in the program. **Writes** lists every register the
instruction changes. Registers not listed are left alone.

### 7.1 Sensors

#### `SELF` (1 tick)

Reads the running unit's own state.

| Writes | Value |
|---|---|
| `r0`, `r1` | my square, x and y |
| `r2` | my current health |
| `r3` | my current energy, as it stood when the run began (before this turn's meter charge) |
| `r4` | `1` if I carry my player's flag, otherwise `0` |
| `r5` | my number among my type's units, from 0, in name order |

`SELF` overwrites `r0` to `r5`. Save the values you need in `r6` or `r7` (or
in memory) before calling another sensor.

#### `TURN` (1 tick)

Writes `r0` = the number of the turn being resolved. Turns count from 1.

#### `EXTENT` (1 tick)

Writes `r0` = board width and `r1` = board height. The last column is
`width − 1` and the last row is `height − 1`.

#### `FLAG mine` / `FLAG enemy` (2 ticks)

| Form | Writes `r0`, `r1` |
|---|---|
| `FLAG mine` | the square of my own flag carrier |
| `FLAG enemy` | the square of the **nearest** standing enemy flag carrier, using the tie-break in [section 9](#9-determinism-and-tie-breaking) |

Writes `-1, -1` if there is no such flag (it has fallen). Flags are the one
thing every army can see without contact.

#### `CONTACT` (2 ticks)

Reads the enemy **this unit** fought last turn.

| Case | Writes |
|---|---|
| none | `r0` = `-1` only. Other registers are untouched. |
| one or more | `r0`, `r1` = the enemy's square now; `r2`, `r3` = its **designed** attack and health |

If the unit fought several enemies, `CONTACT` reports the nearest of them that
is still standing. To tell whether there was a contact, test `r0`
(`JIF neg r0, ...`). This is the natural first instruction for a unit that has
just been woken by a blow.

#### `MAP rA, rB` (3 ticks)

Looks up square (`rA`, `rB`) in the army's shared map. Both operands must be
registers.

| Writes | Value |
|---|---|
| `r0` | kind: `0` unknown, `1` known empty, `2` friend, `3` enemy, `4` off the board |
| `r1` | the turn the square was last known (current turn for a friend), or `-1` |
| `r2`, `r3` | for an enemy: its designed attack and health. Otherwise `-1`, `-1` |

`MAP` overwrites `r0` to `r3`, including the coordinates if you passed them in
those registers. That's fine for a single lookup, but copy them elsewhere if
you need them again.

#### `NEAREST friend` / `NEAREST enemy` / `NEAREST unknown` (4 ticks)

Finds the nearest square of a kind to my square, by Manhattan distance.

| Form | Considers |
|---|---|
| `NEAREST friend` | squares holding one of my army's units, not counting my own |
| `NEAREST enemy` | squares where the map holds an enemy (kind 3), however old the sighting |
| `NEAREST unknown` | squares the map calls unknown (kind 0) |

Writes `r0`, `r1` = the square and `r2` = its distance, or `-1, -1, -1` if
there is none. Ties are settled as in [section 9](#9-determinism-and-tie-breaking).

### 7.2 Radio

#### `SAY to, w1, w2, w3` (5 ticks)

Sends a three-word message. `to` is either the **name** of one friendly unit,
or `all`. Each `w` is a register or an integer literal, read when `SAY`
executes.

- `to` is always taken as a name, even if it looks like a register. A unit
  called `r1` is addressed as `r1`.
- `all` reaches every **other** standing friendly unit with a controller. It
  does not reach the sender.
- A message naming a unit that isn't one of yours, isn't standing, or has no
  controller is **dropped**, and the drop is recorded in your trace. A unit
  may name itself; the message reaches it next turn.
- Messages are delivered after every controller has run. They are read next
  turn, in a fixed order: the turn sent, then the sender's name, then the
  order the sender said them.
- A program may `SAY` any number of times in a run, at 5 ticks each.

Messages carry only what a program chooses to say. The map is shared for free,
so there's no need to broadcast what your units have seen. Use the radio for
**intent**: requests, roles, targets, timings.

#### `RECV` (2 ticks)

Takes the oldest message out of the inbox.

| Case | Writes |
|---|---|
| a message waiting | `r0` = `1`; `r1`, `r2`, `r3` = its three words |
| inbox empty | `r0` = `0` only |

The usual pattern is a loop that reads until `r0` is 0. See
[section 10](#10-patterns-and-idioms).

#### `FLUSH` (1 tick)

Discards every unread message in the inbox. Writes no register.

### 7.3 Data and arithmetic

| Instruction | Ticks | Effect |
|---|---|---|
| `SET rA, n` | 1 | `rA ← n`. The source must be a literal. |
| `MOV rA, rB` | 1 | `rA ← rB`. Both must be registers. |
| `ADD rA, rB\|n` | 1 | `rA ← rA + operand` |
| `SUB rA, rB\|n` | 1 | `rA ← rA − operand` |
| `ABS rA` | 1 | `rA ← |rA|` |
| `SIGN rA` | 1 | `rA ← −1, 0 or 1` according to the sign of `rA` |
| `DIST rA, rB` | 1 | `r0 ← |rA − my x| + |rB − my y|`, the Manhattan distance from my square to (`rA`, `rB`). Both must be registers. It reads my square directly, so you don't need `SELF` first. |

There is no `MUL` or `DIV`. To double, use `ADD rA, rA`. For anything else,
loop, or precompute values into memory.

### 7.4 Memory

| Instruction | Ticks | Effect |
|---|---|---|
| `LOAD rA, rB\|n` | 1 | `rA ← memory[address]`. An address never written reads `0`. |
| `STORE rA, rB\|n` | 1 | `memory[address] ← rA` |

The address is the second operand, either a literal or the value of a
register. Memory belongs to one unit and lasts for its life. It is the only
way to carry state from one turn to the next, apart from the inbox.

Since unwritten memory reads 0, choose your encodings so that 0 is a
sensible "not set yet" value.

### 7.5 Control flow

| Instruction | Ticks | Effect |
|---|---|---|
| `JMP label` | 1 | Continue at `label`. |
| `JIF zero rA, label` | 1 | Jump if `rA = 0` |
| `JIF notzero rA, label` | 1 | Jump if `rA ≠ 0` |
| `JIF neg rA, label` | 1 | Jump if `rA < 0` |
| `JIF pos rA, label` | 1 | Jump if `rA > 0` |
| `JIF eq rA, rB, label` | 1 | Jump if `rA = rB` |
| `JIF lt rA, rB, label` | 1 | Jump if `rA < rB` |
| `CALL label` | 1 | Push the address of the next instruction and continue at `label`. Calls nest up to **16** deep; a 17th halts the controller, drops the order, and is not charged. |
| `RET` | 1 | Pop the return stack and continue there. With nothing to return to, the run ends as at `HALT`. |
| `HALT` | **0** | End the run. The order stands. |

`JIF` compares registers only. To compare against a constant, load it first:

```
SET r4, 5
JIF lt r3, r4, low     ; r3 < 5
```

Other comparisons can be built from `lt` and `eq`:

| Want | Write |
|---|---|
| `a > b` | `JIF lt rB, rA, label` |
| `a ≥ b` | `JIF lt rA, rB, else` and fall through to the "≥" code |
| `a ≤ b` | `JIF lt rB, rA, else` and fall through |
| `a ≠ b` | `JIF eq rA, rB, else` and fall through |
| `a > n` | `SUB rA, n` then `JIF pos rA, label` (this changes `rA`) |

**Subroutines** share the eight registers and memory with their caller.
There are no arguments or local variables, so document which registers each
one reads and overwrites. A `SLEEP` or `HALT` inside a subroutine ends the
whole run, and the next turn starts at the top with an empty stack.

### 7.6 Actuators

#### `MOVE north|east|south|west` / `MOVE rA` (1 tick)

Sets this turn's order to a one-square step. Through a register, the
directions are numbered:

| Value | Direction | Effect |
|---|---|---|
| 1 | north | y − 1 |
| 2 | east | x + 1 |
| 3 | south | y + 1 |
| 4 | west | x − 1 |

`(0, 0)` is the top-left square, so north is up the screen. A register value
outside 1 to 4 sets nothing, and any earlier order stands. A later `MOVE` or
`HOLD` replaces an earlier one. The move is still subject to the movement
rules: the fare is a quarter of the designed health rounded up, a move off the
board is refused, and stepping onto any occupied square, friend or foe, starts
a fight.

#### `HOLD` (1 tick)

Sets the order to "stay put", replacing any earlier `MOVE`. Ending the run
without an order has the same effect on the board. `HOLD` is useful for
cancelling a `MOVE` set earlier in the run, and to show the intent in the
trace.

#### `SLEEP n` (1 tick)

`n` is a literal from 1 to 100. Ends the run, keeping the order already set,
and switches the controller off for the next `n` turns. See
[Sleeping and waking](#sleeping-and-waking).

---

## 8. Quick reference card

| Instruction | Ticks | Operands | Writes |
|---|---|---|---|
| `SELF` | 1 | | r0 x, r1 y, r2 health, r3 energy, r4 carries flag, r5 type number |
| `TURN` | 1 | | r0 turn |
| `EXTENT` | 1 | | r0 width, r1 height |
| `FLAG` | 2 | `mine`\|`enemy` | r0, r1 square or -1, -1 |
| `CONTACT` | 2 | | r0 -1, or r0, r1 square, r2 attack, r3 health |
| `MAP` | 3 | `rA, rB` | r0 kind, r1 turn, r2 attack, r3 health |
| `NEAREST` | 4 | `friend`\|`enemy`\|`unknown` | r0, r1 square, r2 distance; or -1 ×3 |
| `RECV` | 2 | | r0 0, or r0 1, r1-r3 words |
| `FLUSH` | 1 | | |
| `SAY` | 5 | `name`\|`all`, `w`, `w`, `w` | |
| `SET` | 1 | `rA, n` | rA |
| `MOV` | 1 | `rA, rB` | rA |
| `ADD` / `SUB` | 1 | `rA, rB`\|`n` | rA |
| `ABS` / `SIGN` | 1 | `rA` | rA |
| `DIST` | 1 | `rA, rB` | r0 |
| `LOAD` | 1 | `rA, rB`\|`n` | rA |
| `STORE` | 1 | `rA, rB`\|`n` | |
| `JMP` | 1 | `label` | |
| `JIF` | 1 | `cond, r[, r], label` | |
| `CALL` / `RET` | 1 | `label` / | |
| `HALT` | 0 | | |
| `MOVE` | 1 | `north`\|`east`\|`south`\|`west`\|`rA` | |
| `HOLD` | 1 | | |
| `SLEEP` | 1 | `n` (1-100) | |

Limits: 8 registers · call depth 16 · `SLEEP` 1-100 · cap `100 × compute`
ticks per turn · 1 energy per `100 × compute` ticks on the meter.

#### Register clobber table

| | r0 | r1 | r2 | r3 | r4 | r5 | r6 | r7 |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `SELF` | ✎ | ✎ | ✎ | ✎ | ✎ | ✎ | | |
| `TURN` | ✎ | | | | | | | |
| `EXTENT` | ✎ | ✎ | | | | | | |
| `FLAG` | ✎ | ✎ | | | | | | |
| `CONTACT` | ✎ | ✎¹ | ✎¹ | ✎¹ | | | | |
| `MAP` | ✎ | ✎ | ✎ | ✎ | | | | |
| `NEAREST` | ✎ | ✎ | ✎ | | | | | |
| `RECV` | ✎ | ✎¹ | ✎¹ | ✎¹ | | | | |
| `DIST` | ✎ | | | | | | | |

¹ only when there is something to report.

**No sensor writes `r6` or `r7`.** They are the safe place to keep values
across sensor calls, which is why the default programs keep the unit's own
square there.

---

## 9. Determinism and tie-breaking

The game has no randomness (R1.2). Programs fit that rule: the same program
with the same snapshot, memory and inbox always gives the same order, sends
the same messages and spends the same ticks. Some practical consequences:

- **"Nearest" ties are settled by position.** `NEAREST`, `FLAG enemy` and
  `CONTACT` pick the closest square. If two are equally close, they pick the
  one in the row nearer **your own edge** of the board: row 0 for the player
  deployed nearer row 0, the last row for the other. If that still ties, they
  pick the lower x. Both seats of a mirrored game therefore make mirrored
  choices.
- **Controllers run in a fixed order**, but none of them can see another's
  output from the same turn, so the order can't matter.
- **A game whose whole state repeats stops as undecided.** The state includes
  memory, meters, sleep counters and inboxes. A program that patrols a fixed
  loop will eventually repeat and end the game. A program that changes its
  memory every turn (a counter, for example) avoids that, but then the
  50-quiet-turns rule or the 500-turn cap will end the game instead.

If you want behaviour that varies between units, base it on something that
differs between them, such as `r5` (unit number), the square, or `TURN`.

---

## 10. Patterns and idioms

### Afford it before you order it

A move costs `ceil(designed health ÷ 4)` energy, and a strike costs the
attack value. A unit that arrives without energy for a strike is inert in the
fight it walked into. Check energy before moving:

```
SELF                 ; r3 = energy
SUB r3, 3            ; fare 1 + attack 2 for this type
JIF neg r3, rest     ; can't afford both: rest instead
...
rest: SLEEP 1        ; free: recovers 2 energy and costs 1 tick
```

### Test what the map says about a square

```
MAP r2, r3           ; r0 = kind
SUB r0, 2
JIF zero r0, friend  ; was 2
JIF neg r0, open     ; was 0 or 1: unknown or known empty
SUB r0, 1
JIF zero r0, enemy   ; was 3
JMP edge             ; was 4: off the board
```

### Turn a delta into a direction with arithmetic

With `dx` and `dy` reduced to -1, 0 or 1 by `SIGN`:

- east/west: `3 − sign(dx)` gives 2 (east) for dx > 0 and 4 (west) for dx < 0
- south/north: `2 + sign(dy)` gives 3 (south) for dy > 0 and 1 (north) for dy < 0

```
SIGN r2
SET r0, 3
SUB r0, r2
MOVE r0              ; east or west towards the target
```

Make sure the delta isn't zero first: `3 − 0` is 3, which means south.

### Read the whole inbox

```
drain: RECV
JIF zero r0, done
; ... look at r1, r2, r3; use word 1 as a message kind ...
JMP drain
done:
```

Each message costs at least 4 ticks to read (`RECV` + `JIF` + `JMP`), and the
inbox has no size limit. Either bound the loop with a counter, or `FLUSH`
once you have what you need.

### A message protocol

Three integers aren't much. A common convention is **word 1 = kind** and
words 2-3 = coordinates or a value. Agree the kinds across every type in your
army, for example:

| Kind | Meaning | w2, w3 |
|---|---|---|
| 1 | rally here | x, y |
| 2 | flag under attack from | x, y |
| 3 | I'm taking the target at | x, y |

Kind 0 is best left unused, so that a register you forgot to set is easy to
spot.

### State machines in memory

Keep a mode at a fixed address and dispatch on it at the top of the program:

```
LOAD r7, 0           ; mode: 0 = start, 1 = advancing, 2 = holding
JIF zero r7, start
SUB r7, 1
JIF zero r7, advancing
JMP holding
```

Number the modes so that 0, the value of unwritten memory, is a safe
starting state.

### Different roles from one program

```
SELF
JIF zero r5, leader  ; unit 0 of this type leads
SET r4, 1
JIF eq r5, r4, left  ; unit 1 takes the left flank
JMP right            ; everybody else goes right
```

### Counting and timers

```
LOAD r4, 5
ADD r4, 1
STORE r4, 5          ; a per-unit counter of turns awake
SET r0, 20
JIF lt r0, r4, giveup
```

`TURN` gives absolute time, and turns asleep keep counting. A memory counter
counts only the turns the program actually ran.

### Spend nothing when there's nothing to do

`SLEEP` is the cheapest action in the game: 1 tick, and the unit still
recovers energy and strikes back. A guard that sleeps 100 turns at a time
costs almost nothing and is woken by the first blow. The longer the sleep,
the slower the unit reacts to messages, since messages don't wake it.

---

## 11. Worked examples

All three examples parse, and were run against the interpreter while this
guide was written.

### 11.1 Patrol: memory as state

Walks its row from edge to edge, turning at each end. Memory address 0 holds
the heading. It uses 10 to 13 ticks a turn and fits compute 1.

```
; patrol: walk my row from edge to edge, turning at each end
SELF                 ; r0 = x, r3 = energy
MOV r6, r0
SUB r3, 1            ; the fare for health 1-4
JIF neg r3, rest
EXTENT               ; r0 = width
SUB r0, 1            ; r0 = the last column
LOAD r7, 0           ; heading: 0 east (the default), 1 west
JIF notzero r7, west
JIF eq r6, r0, turnw ; at the east edge: turn round
MOVE east
HALT
turnw: SET r7, 1
STORE r7, 0
west: JIF zero r6, turne
MOVE west
HALT
turne: SET r7, 0
STORE r7, 0
MOVE east
HALT
rest: SLEEP 1
```

Notes: `EXTENT` overwrites `r0`, so the x coordinate is saved in `r6` first.
Since unwritten memory reads 0, "east" needs no setup. The unit walks straight
into whatever is in its row, friends included, so use it on an empty back row
or add a `MAP` check before each step.

### 11.2 Keep and guard: the radio

A flag-carrying Keep sleeps, and when it is struck it calls for help. Guards
rest nearby, and when the call comes they walk to the attacker.

**Keep** (9 ticks when struck, 4 otherwise):

```
; keep: hold the flag's square, and call for help when struck
CONTACT              ; r0, r1 = whoever hit me last turn, or r0 = -1
JIF neg r0, nap
SAY all, 2, r0, r1   ; kind 2: "the flag is under attack at (x, y)"
nap: SLEEP 3
```

A blow wakes the Keep at the end of the turn it was struck. On the next turn
its controller runs, `CONTACT` reports the attacker, and the message reaches
the guards on the turn after that.

**Guard** (attack 2, health 4. About 27 ticks a turn while answering a call,
plus about 10 per message read. Compute 1 is enough):

```
; guard: rest near the flag, and answer the keep's call for help
drain: RECV                ; r0 = 1 and r1..r3 = the words, or r0 = 0
JIF zero r0, act
SET r4, 2
JIF eq r1, r4, call        ; kind 2: "the flag is under attack at (w2, w3)"
JMP drain                  ; ignore every other kind
call: STORE r2, 10         ; remember where...
STORE r3, 11
SET r4, 1
STORE r4, 12               ; ...and that there is a call to answer
JMP drain
act: LOAD r4, 12
JIF zero r4, idle          ; nothing to answer
SELF                       ; r0, r1 = my square, r3 = my energy
MOV r6, r0
MOV r7, r1
SUB r3, 3                  ; a step (fare 1) and a strike (attack 2)
JIF neg r3, idle
LOAD r2, 10
LOAD r3, 11
DIST r2, r3                ; r0 = how far away the call is
JIF zero r0, done
CALL toward
HALT
done: SET r4, 0
STORE r4, 12               ; answered
idle: SLEEP 1

; toward: one step from (r6, r7) towards (r2, r3), along the longer axis.
; Uses r0, r2-r5. The caller makes sure the two squares differ.
toward: SUB r2, r6         ; dx
SUB r3, r7                 ; dy
MOV r4, r2
MOV r5, r3
ABS r4
ABS r5
JIF lt r4, r5, vert
SIGN r2
SET r0, 3
SUB r0, r2                 ; 3 - sign(dx): 2 east, 4 west
MOVE r0
RET
vert: SIGN r3
SET r0, 2
ADD r0, r3                 ; 2 + sign(dy): 3 south, 1 north
MOVE r0
RET
```

Things to notice:

- Messages don't wake a sleeper, so the guard idles with `SLEEP 1` and checks
  its inbox every other turn. `SLEEP 5` would be cheaper but slower to
  respond.
- The call is kept in memory (addresses 10-12), so a guard that can't afford
  to move this turn still remembers it next turn.
- `toward` documents its inputs and the registers it overwrites. The caller
  checks `DIST` first, because a zero delta would make `toward` step south.
- The guard steps straight at the target and doesn't go round friends. The
  default `HUNTER` (`domain/army.py`) shows how to check the next square with
  `MAP` and try the other axis if it is blocked.

### 11.3 Reading the default hunter

`HUNTER` in `src/board_game_concept/domain/army.py` is the best complete
example in the codebase. It shows:

- saving `SELF`'s square into `r6`/`r7`, which no sensor touches
- deciding with `SUB r3, {need}` / `JIF neg` whether a step and a strike are
  affordable, and sleeping a turn if not
- picking an axis with `ABS` and `JIF lt`, and keeping the signs for direction
- a shared subroutine tail: `row` and `col` both fall into `look`, which does
  the `MAP` and normalises "friend" to 0 for its callers
- trying the other axis when the first is blocked, and sleeping if both are

---

## 12. Testing and debugging

### Before you commit

- `set program` / the armoury editor will catch syntax errors and show you
  ticks per line.
- Compare the straight-line total and your longest path against the cap
  (`100 × compute`). If a path can reach the cap, the unit will sometimes give
  no order at all.

### Run a program directly in Python

The interpreter is a pure function, so you can test a program without playing
a game. From the repository root:

```python
# PYTHONPATH=src python3 try_program.py
from board_game_concept.domain.program import Program, Snapshot, run
from board_game_concept.domain.army_map import ArmyMap

program = Program(open('guard.asm').read())     # raises ProgramError on bad syntax

# turn 5, an 8 x 8 board, I am player 1; friends by name -> square;
# flags by player number -> square; the army's map; my own edge row
snapshot = Snapshot(5, 8, 8, 1, {'guard1': (3, 3)}, {2: (4, 7)}, ArmyMap(), edge=0)

me = {'x': 3, 'y': 3, 'health': 4, 'energy': 10, 'flag': False, 'number': 0}
memory, inbox = {}, [(2, 6, 1)]                  # persisted between calls by you

result = run(program, snapshot, me, None, memory, inbox,
             compute=1, energy=me['energy'], meter=0)
print(result.order, result.said, result.sleep,
      result.ticks, result.charged, result.halted, memory)
```

`result.order` is `None`, `'hold'`, or a direction 1-4. `contact`, the fifth
argument, is `(x, y, attack, health)` or `None`. To put things on the map,
build an `ArmyMap` and fill in `visited[(x, y)] = turn` or
`enemies[(x, y)] = (turn, attack, health)`. Call `run` repeatedly, carrying
`memory`, `inbox` and `result.meter` forward, to simulate several turns.

`tests/test_program_executor.py` and `tests/test_program_parser.py` have many
more examples of driving the interpreter this way.

### Play it

- **One game:** `python matches/arena.py --game 900 --p1 my_doctrine.yaml --p2 matches/bots/flag_hunt.yaml`.
  The log in `matches/logs/game_900.log` has the board after every turn and
  every controller trace.
- **Single-handed:** take both seats as the administrator (see the README's
  "Playing a game single-handed"), set your program on one side, and commit
  both.

### Read the traces

After the game resolves, `show turn <n>` prints the board and **your**
controllers' traces for that turn: ticks spent, energy charged, the order
given, messages said and dropped, whether the unit slept, was woken, or
halted, and at which line. `show turn <n> known` draws the board as your army
knew it, which is exactly what your programs were reading. Use `next` and
`prev` to step through turns.

Things to look for:

| Trace shows | Likely cause |
|---|---|
| `halted` at a line, every turn | A loop that never exits, or a path longer than the cap |
| `halted`, and energy 0 | The unit thought itself out of energy. Rest more, or think less. |
| order given, but the unit didn't move | The meter charge left too little energy for the fare, or the move went off the board |
| a message `dropped` | The recipient's name is misspelled, it is destroyed, or it is a compute-0 type |
| a unit idles all game | A sensor overwrote a register you were relying on (see the [clobber table](#register-clobber-table)) |

---

## 13. Pitfalls

1. **Sensors overwrite registers.** `SELF` writes `r0`-`r5`, `MAP` writes
   `r0`-`r3`, and `DIST` writes `r0`. Keep long-lived values in `r6`, `r7` or
   memory.
2. **`MAP` and `DIST` take registers only.** Load coordinates with `SET`
   first.
3. **`JIF` compares registers only.** There is no `JIF eq r1, 5`. Use `SET` to
   load the constant first, or `SUB` and test against zero.
4. **A halted controller gives no order,** even if it already ran `MOVE`. Keep
   the longest path well under the cap.
5. **A zero delta is not "no move".** `3 − sign(0)` is 3, which is south.
   Check that you haven't arrived before computing a direction.
6. **Stepping onto a friend starts a fight.** Friendly fire is total. Check
   with `MAP` (kind 2) before stepping.
7. **Messages don't wake sleepers,** and they arrive a turn late. A long
   sleep means a slow response.
8. **Unit numbers follow string order,** so `x10` < `x2`. Zero-pad names when
   the numbering matters.
9. **`CONTACT` and `MAP` report designed statistics,** not the health an enemy
   has left.
10. **The map is memory, not sight.** An enemy stays where it was met until
    you stand on its square. Check `r1` from `MAP` for the age of a sighting.
11. **`NEAREST friend` excludes your own square;** `FLAG mine` does not care
    whether you are the carrier. Use `SELF`'s `r4` for that.
12. **Patrols that repeat end the game.** A whole-game state that has been
    seen before stops the game as undecided.
13. **Energy is shared.** Every tick is eventually paid for out of the same
    energy that buys moves and strikes. A unit that thinks every turn on a
    small compute pays for it in moves.
