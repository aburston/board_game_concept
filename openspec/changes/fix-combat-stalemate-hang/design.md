## Context

See `proposal.md` — Why. The constraint that shapes everything below is the
project's rule, confirmed by the owner: **energy exhaustion makes a unit inert,
never dead. Only health destroys a unit.** An inert unit stays on the board,
blocks its cell, and must be killed by damage.

Three properties of the current engine follow from that rule and were verified
against the code rather than assumed:

- Movement costs `energy // 100 + 1`, which is `1` even at zero energy. A unit at
  zero energy cannot move. **Inert units cannot retreat.**
- A cell holds an `Empty`, a single unit, or a list. The list was only ever meant
  to exist transiently during turn resolution.
- Combat is the only thing that reduces health, and it only happens between units
  sharing a cell.

Together these mean a stalemated set of inert units can neither die nor separate.
They must remain stacked. That is not a design choice available to us; it is what
the rule forces.

## Goals / Non-Goals

**Goals:**

- Turn resolution terminates in a bounded number of rounds, always.
- No unit is destroyed by running out of energy.
- A stacked cell is a legal, persistable state that the whole engine tolerates.

**Non-Goals:**

- Energy regeneration. Energy remains non-renewable, so an inert unit stays inert
  for the rest of the game unless killed.
- A win condition. Still unimplemented; see `SPEC_COVERAGE.md`.
- Fixing issue #1 as such. This change relaxes the placement assertion that makes
  issue #1 crash, because a stacked cell cannot otherwise be reloaded, but it does
  not address issue #1's reporting behaviour beyond that.
- Deduplicating the stale `src/BoardGameConcept.py` and `src/GameData.py` copies.

## Decisions

### Terminate combat on a round that deals no damage

Track whether any attack landed during a round. If none did, combat for that cell
ends. This is the narrowest possible termination condition: it fires exactly when
the loop would otherwise spin, and never when combat is still progressing.

*Alternative considered:* a fixed round cap. Rejected — it would truncate long but
legitimate attrition between high-health units, and the cap would be arbitrary.

### Count survivors afresh each round

Replace the running `unit_count` decrement with a recount of undestroyed
contestants at the top of each round. The existing code subtracts one for every
destroyed unit it finds, every round, so a unit destroyed in round 1 is counted
again in round 2. With three or more contestants the count can reach zero while a
unit still stands, and the cell is then wrongly emptied.

*Alternative considered:* decrementing only for newly destroyed units. Rejected —
recounting is simpler and cannot drift.

### Attacks in a round are drawn from the units alive at the start of that round

A unit destroyed mid-round still lands its own attack that round. This preserves
the existing simultaneous-exchange semantics that the current tests pin down, and
is the reason an attacker with health 5 finishes a fight with health 1 rather
than 3.

### Stalemated survivors stay stacked

The cell keeps every survivor. Rejected alternatives, both of which contradict the
inert-unit rule:

- *Destroy the exhausted units.* Kills by energy, which the rule forbids.
- *Push all but one back to where they came from.* Retreating is moving, and an
  inert unit cannot pay to move. It also has no defined outcome when the origin
  cell was taken by a third unit in the same turn.

### Make stacked cells legal everywhere, not just in combat

Because a stack now persists across turns, every path that reads a cell must cope
with one:

- `Board.print` renders a stacked cell via a representative unit — the player's own
  unit under a player view, otherwise any occupant — instead of raising
  `AttributeError` or printing an object repr.
- `Board.add` and the load path no longer assert the cell is empty. A unit placed
  onto an occupied cell joins it and the contest resolves on the next turn.
- The server applies a move order to the unit it names, looked up by name and
  owning player, rather than to `getUnitByCoords(x, y)`, which returns a list for a
  stacked cell and has no `move` method.

## Risks / Trade-offs

- **A stacked cell of mutually inert units is permanent without outside
  intervention.** → Intended under the rule: they are an obstacle other players
  must clear. Energy is non-renewable, so they cannot free themselves.
- **Relaxing the placement assertion removes a guard that currently catches genuine
  bugs.** → The assertion never reported cleanly anyway — it crashed the session,
  which is issue #1. Regression tests cover the stacked-cell paths it used to
  guard.
- **Repeated stalemates could accumulate inert stacks and stall a game.** →
  Visible to players and to the observer; a win condition, when it exists, will
  need to account for units that are alive but inert.
- **Existing saved games are unaffected**, since no file format changes. A save
  written before this change loads identically after it.
