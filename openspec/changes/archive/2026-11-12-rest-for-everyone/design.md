# Design

## Context

See proposal.md - Why. What the approach rests on:

- `Board.commit` records, before the think phase, every standing unit's
  energy in a `resting` map, and after combat gives `UnitType.REST_GAIN`
  (1) to each unit whose energy is unchanged from that record, below its
  type's energy, standing and not destroyed. "Unchanged energy" is how the
  board tells a unit that did nothing from one that paid; a unit ordered off
  the board pays nothing and is kept out of `resting` separately, and the
  meter's charge is subtracted from the unit's energy in the think phase, so
  a charged unit reads as having acted.
- The `rested` event is emitted once per resting unit, with the energy it
  reached, and the feed, the browser and the record print it.
- The hunter sleeps when it cannot afford a step and a strike, the vanguard
  likewise, and the explorer when it cannot afford a step. Those sleeps are
  how the programs wait for energy, and with two energy a turn for everyone
  they are shorter, not gone.
- R7.1 keeps a player in the game while any unit of theirs could act again,
  and names resting as the reason an exhausted unit still counts.

## Goals / Non-Goals

**Goals:**

- Two energy a turn to every standing unit, unconditionally, within its
  type's energy.
- No other rule moves: the fare, the strike's price, the meter and the cap
  are what they were, and so is when regeneration happens in the turn.
- A feed that still reads: a `rested` line only where energy changed.

**Non-Goals:**

- Rebalancing the catalogue, the array or the programs for the richer
  economy. The series that follows is for seeing what this does; a unit
  that attacks every turn for its attack and gets two back is a different
  game, and that is the point of a series.
- Changing what sleep is for. A sleeping controller still costs nothing;
  what it no longer buys is a rest nobody else gets.

## Decisions

**Drop the `resting` bookkeeping rather than widen it.** The map of energies
before the turn existed only to tell acting from resting. With every unit
resting, the rest step walks the standing units once: skip the destroyed and
the off-board, add `REST_GAIN` up to `type_energy`, emit `rested` where the
energy rose. The "ordered off the board" exception and its comment go with
the condition they served. Alternative: keep the map and ignore it, which
leaves dead code with a live-looking name.

**`REST_GAIN` stays the one constant, set to 2.** The spec names it, the
rules quote it, and the tests import it.

**Report a rest only where energy rose.** The old rule emitted the event
only for units that rested, which excluded units at full energy by the
condition `energy >= type_energy`; the new step keeps that exclusion, so a
seeded army at rest produces no lines, and a unit climbing back from a
fight produces one a turn until it is full. Alternative: a line per unit
per turn, which is thirty-two lines of nothing in the mirror's quiet turns.

**Walls recover nothing without a special case.** `type_energy` is 0 and
`min(0, 0 + 2)` is 0; the `energy >= type_energy` skip means no event
either, which is what `test_a_wall_never_rests` already holds.

**The write-ups are marked, not replayed.** Both programmed series were
played under the old rule and say so at their head once this lands, as the
earlier write-ups do. Replaying is a series of its own, if wanted.

## Risks / Trade-offs

- [Cheap units become perpetual: a Pawn pays one to step and one to strike,
  and gets two back] → that is the rule as asked for, and it is what the
  series will show; the catalogue's prices are not this change's to move.
- [The hunter's `SUB r3, need; JIF neg, rest` sleeps are now mostly
  one-turn pauses] → they are still the right guard against stepping into a
  fight it cannot pay for, and cost nothing.
- [The quiet stop and the repeated-state stop see more energy changes] →
  only until units are full; a static board reaches full energy in a few
  turns and is then as static as before.
- [Tests that counted on a unit *not* resting are the bulk of the work] →
  they are listed in the proposal; each becomes an assertion of the new
  arithmetic rather than being deleted, so the rule's edges stay held.

## Migration Plan

No stored data changes. Energy is a number on a unit, and the next turn
resolved applies the new step. A game half-resolved under the old rule
cannot exist: a game is resolved to its end in one sitting.

## Open Questions

None that change the specs or the tasks.
