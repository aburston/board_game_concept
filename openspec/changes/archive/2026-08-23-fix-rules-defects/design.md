## Context

See `proposal.md` — Why, and `GAME_RULES.md` Part 2 for the catalogue this
change works from.

Three properties of the current code shape everything below.

**A unit is a shallow copy of its type.** `UnitType` is both the template and,
once copied by `Board.add`, the unit. A copy therefore carries the type's
`state`, which is `INITIAL` — the state that means *waiting to be deployed*.
Every path that creates a unit has to set the state deliberately, and the
restore path does not. That single omission is the root of `Q1`: a restored
destroyed unit stays `INITIAL`, is republished as a deployment order, and is
deployed again.

**A turn is one pass over `Board.units` in registration order.** `Board.commit`
calls `preCommit` on each unit in turn, and each one reads and writes the live
board as it goes. What a unit finds at its destination therefore depends on who
has already moved. That is `Q3`.

**The client holds a full `Board` built from `data/units.yaml`.** Visibility is
applied by `serialise_units` and `render.square_character` at the point of
display. The unfiltered board is in memory and the file is on disk, which is
`Q5`; and because that board holds every player's units, `getUnitByName` can
return an opponent's unit, which is `Q6`. One structural change closes both.

## Goals / Non-Goals

**Goals:**

- Turn resolution that produces the same result whatever order units are held
  in, and that can be asserted as such by a test that shuffles them.
- Destruction that is final by construction, not by a check that can be missed.
- A client that cannot see what it is not entitled to, because it was never
  given it.
- One channel that reports everything the server would not do for a player,
  covering the movement phase as well as the apply phase.
- A game that can be won, drawn, and left.

**Non-Goals:**

- Balance. Energy regeneration (`Q8`) and simultaneous mutual destruction
  (`Q10`) are deliberate and stay as they are; see Decisions 7 and 8.
- The `cell`/`square` terminology sweep (`Q15`), which is its own change.
- Backwards compatibility with saved games. See Migration Plan.
- Splitting `UnitType` into a type and a unit. It is the right refactor and it
  would make most of this easier, but it touches everything and would hide the
  behavioural changes inside it. Decision 9 records what is done instead.

## Decisions

### 1. Movement becomes plan-then-apply, in the board rather than the unit

`Board.commit` gains an explicit movement phase that runs in three steps over a
snapshot of the board as the turn began:

1. **Plan.** For each unit with a `MOVING` order, compute its target cell and
   decide whether the move can be carried out at all — on the board, and
   affordable. Produce a list of `(unit, origin, destination)` and a list of
   refusals. Nothing is written to the board.
2. **Detect collisions.** Two planned moves whose origin and destination are
   each other's are a head-on pair (`unit-movement` — Two Units Trading Cells
   Collide). Remove both from the plan, charge both, and record the pair.
3. **Apply.** Vacate every mover's origin, then place every mover at its
   destination, charging the cost. Vacating before placing is what makes a
   chain of units advancing together work without an ordering rule.

Contention is then read off the result: every cell holding more than one unit,
plus each head-on pair.

*Why here.* `preCommit` today is a unit deciding its own move against a live
board, which is exactly the thing that cannot be made order-independent. Only
the board sees all the orders at once, so the plan has to be built there.
`UnitType.preCommit` shrinks to "what would this unit like to do", with no board
writes.

*Alternative considered:* keep per-unit resolution and sort the units into a
canonical order (by player then name) before resolving. It makes the outcome
reproducible without restructuring, but it does not make it *fair* — it just
picks a different fixed winner — and it leaves the pass-through in place.

### 2. A head-on collision is fought in place, and the winner completes the move

Neither unit moves before the fight. Both pay. They exchange attacks under the
existing contest rules. If exactly one survives it completes its move into the
cell the loser held; if neither does, both cells empty; if both do, both stay
where they started.

*Why.* It is the only symmetric answer. Putting the pair in one cell requires
choosing whose cell, and any choice reintroduces an ordering rule — which is the
defect being fixed. Fighting in place needs no tiebreak.

*Alternative considered:* refuse the swap outright, so neither unit moves and no
fight happens. Simpler, but two adjacent units ordered at each other would then
stall forever, and closing to combat from an adjacent cell would be impossible.

### 3. Entering an occupied cell no longer requires energy to attack

The precondition "the mover must have energy at least equal to its attack value"
is removed. A move costs 1 and is legal if the unit can pay.

*Why.* Under plan-then-apply there is no order-independent moment at which
"occupied" can be evaluated: whether the occupant is still there depends on
orders that have not been applied yet. Keeping the rule would mean deciding
which units count as "standing", which is a second ordering problem. And the
outcome is already covered without it — a unit that cannot pay for an attack is
inert in the contest it walked into (`combat-resolution` — Inert Units), so it
arrives and loses rather than being held back.

This is a real change in play: a spent unit can now walk into a fight it will
lose. It is marked **BREAKING** in the proposal.

### 4. Movement costs a flat 1

`energy // 100 + 1` is replaced by the constant. Given the 1–100 energy cap the
formula only ever yields 1, except 2 from exactly 100, so this changes one
number in the whole game — a unit built with full energy gets one more move —
and removes a formula that reads as though it scales.

The vestigial `speed` comment in `domain/unit.py` goes with it.

### 5. Destruction is made final at three points, not one

A check in one place would be another thing to forget. Instead:

- **Restore** sets a unit's state explicitly, and never to `INITIAL`. A restored
  unit is one the board already has, not one waiting to arrive.
- **Publish** filters destroyed units out of a player's order file. A dead unit
  is not an order.
- **Apply** refuses any order naming a unit the server holds as destroyed,
  including a deployment, and records the refusal.

Each alone would fix the observed bug; together they mean no single path can
resurrect a unit.

Separately, `Board.add` is reordered to validate everything — bounds, cell
occupancy, duplicate name — *before* it appends to `units` or `unit_dict`. Today
the append happens first and the duplicate-name assertion fires after it,
leaving a phantom unit that the next `commit` deploys. This is what
`board-model` — A Refused Placement Registers Nothing is written against.

### 6. The client is given a view, not a board

`Game.load` branches on the session's role:

- **Observer and server** read `data/units.yaml` and every player file, as now.
- **A player's client** reads only `players/<n>_units_seen.yaml` and its own
  `players/<n>.yaml`. It builds one board from that view. `seen_board` and the
  full `board` collapse into one.

Enemy unit *types* then arrive the same way the units do: the view already
carries each unit's type name and statistics, so `show types` is derived from
the view rather than from other players' files. The client stops enumerating the
players directory for anything but player numbers.

With one board per client, `order_move` looks a unit up in a board that holds
only that player's units — and it passes the player to `getUnitByName` anyway,
which is the direct fix for `Q6`.

*Consequence to watch.* `SPEC_COVERAGE.md` item 7 records why the view is
preferred over the local board: a unit deployed during setup exists only
locally, and is mirrored into the view so its owner can see it. With one board
that mirroring becomes the ordinary case rather than a special one — a deployed
unit goes into the client's board, which *is* the view.

### 7. Energy regeneration is not added

`Q8` — a unit below its attack value can never fight again, and two inert units
can hold a cell against each other forever. Left alone deliberately: attrition
to exhaustion is a coherent design, and the win condition landing in this change
gives such a game somewhere to end. Adding regeneration changes every game and
should be proposed on its own merits.

### 8. Combat stays simultaneous

`Q10` — all attacks in a round land regardless of damage taken in that round, so
identical units annihilate each other. Left alone: it is specified deliberately
(`combat-resolution` — Attackers Are The Units Standing At The Start Of A
Round), it is what makes the outcome independent of who is listed first, and
changing it means inventing an initiative rule. Recorded in `GAME_RULES.md` as a
design choice rather than a defect.

### 9. `UnitType` is not split, but state is set explicitly everywhere

Splitting the template from the instance would make Decision 5 structural rather
than a matter of discipline. It is deliberately not done here: it touches every
module and would bury the behavioural changes. Instead every construction path
sets `state` explicitly, and a test asserts that no restored unit is ever left
in `INITIAL`. The split is worth its own proposal afterwards.

### 10. Outcome and turn number live in the shared data, computed at resolution

`turn.resolve` computes elimination after combat, from the board: a player is in
the game while they hold a unit that is on the board and not destroyed. The turn
number and, once decided, the outcome, are written to the shared data alongside
the board. The barrier reads elimination from the same place, so it cannot
disagree with the outcome.

The server exits its cycle on a decided game rather than raising, and reports
the result. Clients and the observer read the outcome on load.

*Why compute it rather than track it.* Elimination derived from the board each
turn cannot drift out of step with the units; a maintained flag can.

## Risks / Trade-offs

**Rewriting the movement phase is the largest change here, and combat depends on
its output** → Land it behind the existing engine tests first, with a new test
that resolves the same orders against boards whose units were registered in
different orders and asserts identical results. That test is the specification
of Decision 1 and should be written before the rewrite.

**Head-on collisions and the removed attack precondition change how games play,
not just what is correct** → Both are marked **BREAKING** and are visible in
`unit-movement`. `GAME_RULES.md` is updated in the same change so there is one
place that describes the game as it then is.

**Giving the client only its view may hide something a player needs** → The
per-player view is written every turn and already carries own units, seen
enemies, and their statistics. The risk is a display path that quietly depends
on the full board; the CLI surface suites cover each `show` subcommand and are
what that is checked against. A client with no view yet (before the first
resolution) is specified rather than left to fall back.

**Extending rejections to the movement phase crosses a layer boundary** —
`Board.commit` returns events and knows nothing about players or files, while
`turn.resolve` collects rejections → Carry movement refusals out as events of
their own, and let `turn.resolve` turn the ones that name a unit into rejection
entries. The engine keeps its rule about not knowing where things are stored.

**Reporting undecided contests could become noise** — a stand-off repeated over
many turns reports every turn → It is reported per turn like any other refusal
and is replaced rather than accumulated, so a player sees the current state, not
a history. If it proves noisy the remedy is a quieter presentation in the
client, not dropping the information.

**Elimination could fire on turn 1 before anyone has deployed** — a player whose
units are all still `INITIAL` holds nothing on the board → Elimination is
evaluated only after the first turn has been resolved, which is when deployment
happens; `game-outcome` states this as its own scenario.

## Migration Plan

The on-disk format gains a turn number and an outcome, and the client stops
reading `data/units.yaml`. Games saved before this change will not load
correctly, because their unit records were written by a client that republished
destroyed units.

No migration is written. Games are local directories under `games/_<gameno>/`,
this is a pre-release concept project, and a converter would have to guess which
units in an old save are phantoms left by a refused deployment. Games in
progress are abandoned; the loader reports a game it cannot read rather than
loading half of it, which `game-persistence` — Malformed Data Is Fatal already
requires.

Rollback is reverting the change: nothing outside the repository is written, and
no state survives that a previous version would misread beyond the game
directories, which are disposable.

## Open Questions

- **How should the server behave when the last two players are eliminated by a
  contest that also empties the board?** `game-outcome` says this is a draw. Left
  open is whether the server should keep the game directory as a record or say
  more about how it ended; either is a presentation choice that does not change
  the specs.
- **Whether the undecided-contest report belongs in the rejection file or a
  channel of its own.** It is specified as part of what the player is told; the
  file it travels in can change without changing behaviour.
