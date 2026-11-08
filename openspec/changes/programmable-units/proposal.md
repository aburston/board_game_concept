# Proposal

## Why

The repository's first line says what the game is for: building **and
programming** your own units. Everything else has been built; the programming
has not, and `MODULE_DESCRIPTION.md` still lists it as the one thing not
built. Every turn of every game so far has been ordered by a person at a
prompt or by a bot outside the rules, handed a seat's view by a harness. The
series in `matches/RESULTS-DEFAULT-BOARD.md` showed how much of play is
exactly the bookkeeping a program would do - find the flag, step round your
own, press a contact - and that a doctrine lives or dies on that bookkeeping.
It is time to put the controller inside the unit, under the rules, and price
it like everything else a unit is made of.

## What Changes

**A unit is a robot.** Each unit type carries a **program**, written during
setup and fixed at commit, and each unit runs its type's program every turn
with its own registers, memory, inbox and sleep state. A program senses,
thinks, and emits at most one order (`MOVE` or `HOLD`), messages to friends,
or a `SLEEP`. Striking is not an instruction: a unit fights because it ends a
turn on a contested square, as today.

**Thinking costs energy, by a published tariff.** A type gains a fourth
statistic, **compute** (0 to 10), priced into its cost like the other three.
Every instruction has a fixed tick cost, in one table. A unit's ticks
accumulate on a **meter** of capacity `10 × compute`; each time the meter
fills the unit pays 1 energy and the meter empties, so a cheap reflex costs a
fraction of an energy a turn and nothing is free. A controller halts at
`10 × compute` ticks in one turn, so thinking never costs more than one energy
a turn. A type with compute 0 has no controller: a wall, or a **turret** that
stands, strikes back and rests.

**Sleep is how a unit rests.** `SLEEP n` switches the controller off for `n`
turns; a sleeping unit gives no order, pays nothing, and recovers energy under
the existing rest rule. Being struck wakes it: the exchange is fought on the
ordinary terms, it strikes back if it can pay, and its controller runs again
next turn.

**The army shares one map, for free.** Every unit with a controller holds the
whole board as its army knows it - every friend's square, every square a
friend has stood on and when, every enemy a friend has fought and when, and
every flag - kept in step across the army automatically. Nothing is sensed at
a distance: a square is learned by moving onto it. Reading the map costs ticks;
holding it costs nothing. Memory and inboxes are unbounded for now.

**The radio carries intent.** `SAY` sends three words to one named friend or
to all, anywhere on the board, delivered next turn into an inbox that persists
until read. Facts travel by the map; orders travel by radio.

**BREAKING: fire and observe.** Once every seat's setup is committed the game
resolves **every turn at once**, as fast as the engine can, and stops when it
is decided, when the entire state of the game repeats (so nothing can ever
change), or at a generous turn cap. There is no per-turn commit, no pause and
no concession: there is a **record** of every turn, and every role watches it
as a replay - forward, back, at any speed. A seat sees the whole board in the
replay, may overlay what its own army knew at each turn, and reads a
**controller trace** for each of its own units: ticks, energy paid, the order
it gave, what it said, whether it halted. Nobody is shown another seat's
program, compute or trace. Games set up before this change cannot be played
on: their types carry no program and their turns were ordered by hand.

**The stock army gets programs.** Every catalogue type gains a compute value
and a default program, so a seat that changes nothing plays a sensible
doctrine. The default budget moves to cover the array's new price.

**Assembly first.** The program language is the instruction set itself, one
instruction a line, with every line's tick cost beside it in the listing. A
friendlier surface language is a later change; the cost table is defined at
this level and stays there.

## Capabilities

### New Capabilities

- `unit-program`: the controller a unit runs - the instruction set and its
  tick table, registers and memory, the meter and the energy tariff, the per-
  turn cap and halting, sleep and waking, the army's shared map and record as
  the sensors read them, the radio and the inbox, the order a program emits,
  and the controller trace the record keeps for its owner.

### Modified Capabilities

- `unit-types`: a fourth statistic, compute, 0 to 10; a program as part of a
  type's definition; a type with compute 0 has no controller and may carry no
  program, and need not afford a move; a turret is such a type with attack and
  energy.
- `point-budget`: compute is part of a type's price; the default budget rises
  to cover the stock array.
- `turn-commit`: a think phase before deployment in which every controller
  runs against the board as the turn began; the administrator's commit
  resolves the game to its end; the per-turn commit barrier is gone; every
  turn is recorded for replay.
- `game-outcome`: a game also stops, undecided, when its whole state repeats
  or at the turn cap; what a seat is told about a controller that halted.
- `visibility`: the army's shared map and stamped record of past contact,
  which the published view does not keep today; what the replay shows each
  seat once the game has resolved; programs, compute and traces are never
  disclosed to another seat.
- `default-army`: compute and a default program for each catalogue type.
- `game-persistence`: the record of every turn, with each seat's trace, kept
  so it can be replayed.
- `player-client`: setting a type's program during setup, the listing with its
  tick costs, and watching the replay - `show turn <n>`, `next`, `prev` - in
  place of ordering and committing turns.
- `game-server`: the commit that resolves the game to its end, and the replay
  commands.
- `game-observer`: the replay commands; the observer sees every seat's
  board but no seat's programs or traces.
- `web-interface`: a program editor with the listing and tick costs in the
  armoury; the replay with a scrubber and a speed control, the army-knew
  overlay and the controller trace, in place of the orders board.

## Impact

- **Domain**: a new `domain/program.py` (the VM: parser, instruction table,
  meter, execution against a snapshot), `domain/unit.py` (compute, program,
  memory, meter, sleep, inbox), `domain/board.py` (the think phase, the
  shared map, the record of a turn), `domain/army.py` (compute and programs
  for the catalogue). The determinism tests grow to cover the VM: the same
  program on the same snapshot gives the same orders, and no instruction
  reads anything but the snapshot, memory and inbox.
- **Service**: `service/turn.py` resolves to the end at the administrator's
  commit and stops on a repeated state or the cap; `service/games.py` gains
  `set program`; the turn feed becomes a per-turn record with a trace per
  seat.
- **Storage**: both repositories keep every turn's record rather than the
  latest state; a game written before this change is refused as unreadable,
  as games without budgets or flags already are.
- **CLI**: `set program <type> <file>`, `show program <type>` with the tick
  listing, `show turn <n>`, `next`, `prev`; `move`, `hold` and the per-turn
  `commit` are retired from the client. The grammar, completion and help move
  with them.
- **HTTP and web**: endpoints for the program and for the record; the
  armoury gains an editor and listing; the board becomes a replay.
- **Rules and docs**: `GAME_RULES.md` gains a section for the controller and
  the tariff, restates R2.4, R2.9, R3 and R6, and adds the meter to R9's cost
  table; `SPEC_COVERAGE.md` and `MODULE_DESCRIPTION.md` stop listing
  programming as not built.
- **Matches**: the doctrines in `matches/bots/` become programs on types, the
  harness shrinks to two type files and a commit, and a seventh series plays
  the game as it then stands. The `match-series` capability is unchanged.
