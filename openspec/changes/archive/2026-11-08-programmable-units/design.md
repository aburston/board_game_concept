# Design

## Context

See `proposal.md` - Why. The game today is ordered by hand: a seat drafts
`move` orders, commits, and a barrier resolves the turn when the last seat
does. The engine already has every property a controller needs underneath
it: a turn is a pure function of the board and the orders (R1.2), movement is
planned against the board as the turn began (R3.4), combat is one simultaneous
exchange (R5.2), and the twenty games of `matches/RESULTS-DEFAULT-BOARD.md`
were played by bots outside the rules doing what a controller would do inside
them. What is missing is the controller, a way to pay for it, the record a
played-out game leaves, and the removal of everything that assumed a person
at a prompt each turn.

Decisions the exploration fixed, which this design takes as given: one
program per type; compute as a fourth bought statistic with no free
allowance; ticks accumulate on a meter of `10 × compute` so a small program
costs a fraction of an energy a turn; `SLEEP` is how a unit rests, lasts at most a hundred
turns, and a blow wakes it; one shared map per army, filled only by standing or fighting on a
square, held for free; a board-wide radio for three-word messages into an
inbox that persists; the game resolves to its end at the last setup commit
and is watched as a replay; assembly first.

## Goals / Non-Goals

**Goals:**
- A controller whose every instruction has one published cost, identical in
  the Python engine and, later, the browser.
- Resolution that stays a pure function of the committed setups: the same two
  setups give the same record, byte for byte, under either backend.
- A record rich enough that a player can see why their program did what it
  did, and poor enough to the other seat that nothing about a program leaks.
- The stock army plays itself sensibly with nothing changed.
- The CLI and web roles lose per-turn ordering without losing setup or the
  ability to watch.

**Non-Goals:**
- A surface language or compiler. The VM listing is what a player writes.
- Sizing memory or inboxes. Both are unbounded until a program wants to fill
  one.
- Tuning. The tick table and the catalogue's compute values are first guesses
  for the first series to argue with, as the fare and rest were.
- Keeping the hand-ordered game playable beside this one. It is replaced.
- Pacing on the server. The engine runs flat out; pacing is the replay's.

## Decisions

### 1. The VM is a small register machine in `domain/program.py`

A parser from text to a list of instructions, an instruction table that maps
each to its tick cost and a function, and an executor that runs one unit's
program against a snapshot and returns what it did: the order, the messages,
the sleep, the ticks, the trace. The executor owns the per-turn cap; the
meter lives on the unit and is advanced by the think phase from the ticks
the executor reports. Eight integer registers, a dictionary for memory,
labels resolved at parse time.

*Alternatives:* embedding Lua or a Python subset was rejected in the
exploration because neither has a cost per instruction a player can read;
WebAssembly has fuel but a toolchain nobody at a table has. A register
machine is ~300 lines in Python and the same again in JavaScript, and every
row of the tick table is one case in it.

### 2. Sensors answer from a snapshot built once per turn

The think phase builds, before any controller runs, one frozen snapshot per
army: the board as the turn began, the army's map as it stood after the last
turn, the flags, and each unit's inbox. Every controller of that army reads
the same snapshot. Nothing a controller does during the phase - an order, a
message, a `STORE` - is visible to any other controller until next turn. This
is the same discipline movement already keeps (destinations from the board
as the turn began), and it is what makes the order controllers run in
irrelevant, which `test_determinism.py` will hold by running every
permutation of a board's units.

### 3. The map is a per-army structure updated once, after combat

`domain/army_map.py` (name to settle) holds, per square, one of `unknown`,
`empty(turn)`, `friend`, `enemy(turn, attack, health)`, plus the flags. It is
updated at the end of the turn from the resolution's own record of who stood
where and who fought whom - the same facts the turn feed already computes per
seat - so no second visibility calculation is introduced. `NEAREST` and `MAP`
are queries on it; the engine's work for `NEAREST` varies with the board, the
player's cost does not, which decision 1's tick table states on purpose.

The published per-seat view is unchanged and still drives the "contact lost"
behaviour; the map is a second, cumulative structure the view does not expose.
A seat's map at each turn is stored with the record so the replay can show
"what my army knew".

### 4. The meter is on the unit; the tariff is one line

`unit.meter += ticks; while unit.meter >= 10 * compute: pay 1; meter -= cap`.
The executor stops at `10 × compute` ticks in a turn, and stops at the
instruction that would push the meter over capacity while energy is 0. Both
stops are "halted" in the trace, with the instruction index. Halting drops
the order, which is the simplest rule and the one that makes a runaway loop
a visible mistake rather than a free move.

*Alternative considered:* charge `ceil(ticks / compute)` per turn with no
carry. Rejected in the exploration: integer energy makes the floor 1 a turn,
which a 2-energy Pawn cannot survive.

### 5. Sleep and waking are unit state read by the think phase

`unit.asleep` is a countdown of at most a hundred, the parser refusing a larger
literal. The think phase skips a unit with a positive countdown and
decrements it; a unit that wants to stay dormant runs `SLEEP` again when it
wakes, paying a tick each time, which is the point of the bound. Combat sets `unit.woken = True` on any unit in
a contested square; the rest phase clears the countdown of a woken unit.
Combat itself is unchanged: a sleeper in a square strikes if it can pay, as
every unit does today.

### 6. The radio is a per-unit queue written in the think phase, read next turn

`SAY` appends to the recipients' *pending* inboxes; at the end of the think
phase the pending queues are sorted (turn, sender name, order said) and
appended to the live inboxes, so no controller reads a message sent this
turn. `RECV` pops; `FLUSH` clears. Dropped messages (bad recipient) go to the
sender's trace. Inboxes are unbounded, per the exploration.

### 7. Resolution to the end is one held act, with a state hash per turn

`service/turn.py` gains `resolve_game`, called by the commit that completes
setup (locally by the server's wait, over HTTP inline as today). It loops
`resolve_turn` under one hold, writes each turn's record, and after each turn
computes a hash of the whole state - every unit's square, health, energy,
memory, meter, sleep, inbox, and every army's map - and stops when a hash
repeats or at `TURN_CAP = 500`. The hash is over a canonical serialisation,
so the same state hashes the same under both backends.

*Alternative:* resolve turn by turn on the old cycle with no barrier.
Rejected: it leaves a half-played game on disk between turns for no reason
and makes "a game is a record" true only eventually.

### 8. The record is the existing turn feed widened, not a new store

`turn_events` and `player_events` already keep every turn's events by number.
The record adds, per turn: the board and units after the turn (today only the
latest is kept), the flags, each army's map, and the traces. Both repositories
gain a `turns` table or directory keyed by turn number. The replay reads one
turn's row. Storage grows linearly with turns, which at 500 turns of 32 units
is small.

### 9. What each role shows

- **Client**: `set program`, `show program` (the listing with ticks), the
  setup commit, then the replay: `show turn <n>`, `show turn <n> known`,
  `next`, `prev`. `move` and `hold` go, with their grammar, completion and
  help. The rejected-orders report becomes per turn, read from the record, and
  is filtered by owner, which also closes divergence 32 in
  `SPEC_COVERAGE.md`.
- **Server**: unchanged setup; after its commit it waits for the seats'
  commits, resolves the game and exits; replay commands for the
  administrator.
- **Observer**: replay commands, every seat's traces and programs.
- **Web**: the armoury gains a compute field and a program editor whose
  listing shows ticks per line and the energy-per-tick the type's compute
  buys; the orders board becomes a replay with a scrubber, a speed control,
  play and pause, step forward and back, a "what my army knew" toggle, and a
  trace panel for the seat's own units. Box selection, drag-to-order, the
  compass and the arrow keys go; drag-to-deploy stays.

### 10. The default programs are the doctrines, shrunk

Garrison is the Keep's warden (`SLEEP 100`, repeated on waking). The hunter is Flag
Hunt's `flag_step` with the sidestep: `FLAG enemy`, `SELF`, two `SUB`s and
two `SIGN`s, `MAP` on the square ahead, a `JIF friend` to try the other axis,
a check that energy covers fare plus attack else `SLEEP 1`, `MOVE`. The sentry
is `CONTACT`, `JIF none`, step at it if affordable, `SLEEP 2`. The explorer is
`NEAREST unknown`, step, `SLEEP 1` when none. Each is written to fit its
type's cap on every turn, which the tests check by running each against the
stock opening.

### 11. The matches harness becomes a reader

`arena.py` no longer types orders. It sets the two seats up from two type
files (statistics, programs, placements, flag), commits, and reads the record
into the same `game_<n>.log` and `history.json` shapes, so `check_records.py`
and the write-up format carry over. The `match-series` capability's
requirements still hold: every command goes through a role's prompt, a bot
(now a program) is given only its own army's map, the outcome is the game's.

## Risks / Trade-offs

- [The tick table or compute prices make every sensible program unaffordable,
  or every program free] → Both are constants in one table and one formula;
  the first series on the new rules is the tuning run, and the stock army's
  default programs are checked against their caps in tests before any game.
- [A controller's behaviour differs between Python and a later JavaScript VM]
  → Not in this change: the browser sends programs to the server and reads
  the record; no JavaScript executes a program. When a browser-side VM
  arrives it is held to the same listing test suite.
- [State hashing misses a field and a repeating game runs to the cap] → The
  hash is built from the same serialisation the record writes, so a field the
  record keeps is a field the hash covers; a test resolves two Garrisons and
  requires a stop on turn 2.
- [A program that never sleeps and never charges the meter rests every turn
  while thinking] → Deliberate under the exploration's rest decision; a unit
  thinking under one meter-fill a turn is cheap to run and not free. If the
  first series shows it to be exploited, the single sentence in `Energy
  Regeneration` is where it changes.
- [The replay record is large for a long game] → Linear in turns × units;
  500 turns is a hard cap. Measured, not guessed, in the first series.
- [Removing hand ordering strands the web interface's largest feature set]
  → The requirements are removed deliberately in the `web-interface` delta,
  with the deploy-board drag kept. The selection and ordering code goes with
  them; it has no second use.
- [A seat's inbox grows without bound in a long game of chatter] → Accepted
  for now by decision; `FLUSH` exists, and the cap bounds the game.

## Open Questions

None that change the specs or the approach. The tick values and the
catalogue's compute values are the first series' to argue with.
