## Context

See proposal.md - Why. Three pieces of the engine are involved, in the order
the fault travels:

- combat records contact by appending to a per-unit list, once per attack, so
  two units that trade blows over several rounds record each other many times;
- the per-player view is written by walking every unit and emitting it once per
  contact entry that belongs to the reading player;
- restoring a view or a saved game calls the same board placement path a client
  uses to deploy, which refuses a name a player already holds.

Only the last of these is visibly fatal, but each of the three produces
duplicates on its own: several units of one player engaging the same enemy
duplicates the enemy in that player's view even with contact recorded once.

Views and saved games are plain YAML on disk. Games already in progress hold
files written by the current code, so whatever is written now, the loader has
to cope with a file that names the same unit repeatedly.

## Goals / Non-Goals

**Goals:**

- A client survives contact with an enemy unit, and shows it once.
- Files already on disk, duplicates and all, load.

**Non-Goals:**

- Changing the on-disk format, or the visibility rules themselves.
- The stale duplicate copies of the engine at `src/BoardGameConcept.py` and
  `src/GameData.py`, which the package does not import.

## Decisions

**Fix all three layers, not just the loader.** The loader has to tolerate
duplicates whatever else changes, because old files exist. But stopping there
would leave the server writing a view whose size grows with the length of a
fight, and would leave `show units` reporting one enemy twenty times. Each
layer is a separate defect and each is fixed where it happens.

Alternative considered: de-duplicating only when the view is written. Rejected
because it leaves an in-memory contact list that grows per attack and reads as
a record of encounters when it is a set of units.

**Restoring a known unit updates it in place.** The alternative was to ignore
the repeat outright. Updating means the last record wins, which matches how the
rest of a restore behaves — the file is the truth, applied in order — and keeps
the operation idempotent for identical repeats, which is the case in hand.

**A lookup that answers rather than asserts.** Board unit lookup by name
asserts when the unit is absent, which is right for an order naming a unit that
does not exist, but useless for asking whether one is known. Restoring needs a
question, so it gets one, and existing lookups keep their behaviour.

**Placement keeps refusing a reused name.** A player deploying two units with
one name is still an error and is still refused; only restoring is exempt. That
error's text is repaired as part of this change: it interpolates a player
attribute that does not exist, so reporting it raises a second, misleading
error over the top of the real one.

## Risks / Trade-offs

- A view that names a unit twice with *different* state now resolves to the
  last record rather than failing → the two records the server writes are
  copies of one unit, so there is no conflict to lose; a genuinely inconsistent
  file was previously fatal to the client, which is worse.
- Restoring no longer catches a duplicated name for the same player, so a
  corrupt saved game loads quietly → placement still catches it, which is the
  path player orders take; a restore is replaying state the server already
  accepted.
- Contact recording now scans the list before appending → the list holds the
  units in one cell, so this is bounded by the contestants in a single fight.

## Migration Plan

None. No format change, and the loader accepts both the old duplicated views
and the de-duplicated ones written from now on. A game in progress picks the
fix up as soon as its client and server are restarted.
