## Context

See `proposal.md` — Why. Two rules from the owner shape everything below:

1. **Energy exhaustion makes a unit inert, never dead. Only health destroys a unit.** An
   inert unit stays on the board and holds its cell until an opponent kills it.
2. **When units contest a square and exhaust themselves, they all retreat and nobody wins.**
   The move is undone rather than settled.

There is also **friendly fire**: units do not tell their own side from anyone else's. Every
unit in a contested cell attacks every other unit in it. The engine already behaves this
way; the specs now say so.

Three properties of the current engine were verified against the code rather than assumed:

- Movement costs `energy // 100 + 1`, which is `1` even at zero energy. A unit needs at
  least 1 energy to move, but a unit too spent to *attack* can usually still *move*. So an
  inert unit is not permanently stuck: it can walk away next turn.
- A cell holds an `Empty`, a single unit, or a list. The list was only ever meant to exist
  transiently during turn resolution.
- Combat is the only thing that reduces health, and it only happens between units sharing a
  cell.

## Goals / Non-Goals

**Goals:**

- Turn resolution terminates in a bounded number of rounds, always.
- No unit is destroyed by running out of energy.
- An undecided contest leaves the board as it was, with the movers back where they started.

**Non-Goals:**

- Energy regeneration. Energy remains non-renewable.
- A win condition. Still unimplemented; see `SPEC_COVERAGE.md`.
- Fixing issue #1 as such. This change relaxes the placement assertion that makes issue #1
  crash, but does not otherwise address how deployment conflicts are reported.
- Deduplicating the stale `src/BoardGameConcept.py` and `src/GameData.py` copies.

## Decisions

### Terminate combat on a round that deals no damage

Track whether any attack landed during a round. If none did, combat for that cell ends. This
is the narrowest possible termination condition: it fires exactly when the loop would
otherwise spin, and never when combat is still progressing. Because the loop only exits with
more than one survivor when *no* contestant could pay for an attack, the outcome is
unambiguous — nobody could win.

*Alternative considered:* a fixed round cap. Rejected — it would truncate long but legitimate
attrition between high-health units, and the cap would be arbitrary.

### Count survivors afresh each round

Replace the running `unit_count` decrement with a recount of undestroyed contestants at the
top of each round. The old code subtracts one for every destroyed unit it finds, every round,
so a unit destroyed in round 1 is counted again in round 2. With three contestants and two
rounds the count reaches zero while a unit is still standing, and the cell is then wrongly
emptied — a live unit vanishes from the board.

### Attacks in a round are drawn from the units standing at the start of that round

A unit destroyed mid-round still lands its own attack that round, preserving the
simultaneous-exchange semantics the existing tests pin down. A unit destroyed in an *earlier*
round no longer attacks at all, which the old code got wrong: it iterated the whole cell
every round, so corpses kept fighting.

### An undecided contest retreats the movers

Each unit records the cell it vacated during `preCommit`. When combat ends with more than one
survivor, every survivor that has such a record is put back there and the contested cell is
handed to whoever is left — the defender who never moved, or `Empty` if nobody stayed.

The retreat is the move being undone, so it costs no further energy. The energy already spent
moving in and attacking is *not* refunded: the unit made the attempt.

Two units cannot collide while retreating, because distinct units left distinct cells. If a
unit's origin was taken by a third unit during the same turn, there is nowhere to go back to
and it stays in the contested cell.

*Alternatives considered:*

- *Destroy the exhausted units.* Kills by energy, which rule 1 forbids.
- *Leave the survivors stacked in the contested cell.* Rejected under rule 2, and it created
  a permanent obstacle no one could clear: stacked inert units can neither die nor separate.

### Shared cells remain legal, as a residual case

Retreat empties the contested cell in the ordinary case, but not always. A unit deployed onto
an occupied cell never moved, so it has nothing to fall back to; nor does a unit whose origin
was taken. Those survivors share the cell, so every path that reads a cell must still cope
with one:

- `Board.print` renders a shared cell via a representative unit — the player's own unit under
  a player view, otherwise any occupant — instead of raising or printing an object repr.
- Placement and the load path no longer assert the cell is empty.
- The server applies a move order to the unit it names, looked up by name and owning player,
  rather than to `getUnitByCoords(x, y)`, which returns a list for a shared cell and has no
  `move` method.
- Leaving a cell removes only the departing unit. The old code assigned `Empty()` over the
  whole cell, which took any unit sharing it off the board.

## Risks / Trade-offs

- **Retreating hands the square back to a defender that could not fight either.** → Intended:
  nobody wins, and the status quo is the defender's. An attacker that wants the square must
  come back with enough energy.
- **Relaxing the placement assertion removes a guard that currently catches genuine bugs.** →
  The assertion never reported cleanly anyway — it crashed the session, which is issue #1.
  Regression tests cover the paths it used to guard.
- **A shared cell of mutually inert units is still possible.** → Rare, and no longer a
  deadlock: a unit with any energy at all can move away next turn.
- **Existing saved games are unaffected**, since no file format changes. A save written before
  this change loads identically after it.
