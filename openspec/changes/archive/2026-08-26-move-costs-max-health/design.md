## Context

See proposal.md — Why. The state this design has to work with:

- `UnitType.MOVE_COST = 1` is a class constant read in exactly two places:
  `UnitType.planMove`, which refuses a move the unit cannot pay for, and
  `Board._move`, which charges every planned move once, before any of them is
  applied.
- A unit is a copy of its type, and the design it was made from is already kept
  alongside the values play wears down: `type_attack`, `type_health`,
  `type_energy`. The `cost` property (deployment price) is already computed
  from those rather than stored, on the stated grounds that a second copy of a
  number can only ever disagree with the first.
- Type validation is a run of `assert`s in `UnitType.__init__`, and
  `service/games.define_type` already catches them and re-raises as a
  `GameError`, so an assertion message is what a player sees at the prompt.
- `UnitType.__init__` is called from three places: defining a type
  (`service/games.define_type`), loading a player's own types
  (`service/game.py` around line 282), and reconstructing an **enemy** type
  from a unit record seen in contact (`service/game.py:_typeFor`).
- The project invariant: resolution is a pure function of the board and the
  orders. Nothing here may make a turn depend on anything else.

## Goals / Non-Goals

**Goals:**

- One source of truth for what a move costs, derived from the type's design.
- Validation that fails at the moment a type is defined, with a message that
  says which rule was broken.
- Leave `Board._move`'s single charging point single: the cost varies per unit,
  but it is still paid once per planned move, in the same place.

**Non-Goals:**

- No change to rest (`REST_GAIN` stays 1), to attack cost, to the deployment
  point formula, or to what a refused order reports.
- No storage format version or automatic migration of games saved before this
  change (see Migration Plan).
- No new balance knob: the cost is the health, not a multiple of it.

## Decisions

### Cost is read from `type_health`, not from current health

A move costs the health the type was designed with. Reading current health
instead would make a wounded unit cheaper to move, so taking damage would buy
tempo and a player could farm chip damage on their own front line to speed it
up — backwards, and it makes the fare a thing a player has to recompute after
every contest. `type_health` is fixed at construction, never written by
resolution, and already serialised, so the cost is legible from the type sheet
alone.

### The cost becomes a per-unit property, and `MOVE_COST` goes

Replace the class constant with a read-only `move_cost` property returning
`self.type_health`, mirroring the existing `cost` property and its rationale:
computed, not stored, so it cannot drift from the design it comes from.
`planMove` compares `self.energy < self.move_cost`; `Board._move` charges
`unit.energy -= unit.move_cost`.

Alternatives considered: keeping `MOVE_COST` as a multiplier
(`type_health * MOVE_COST`) was rejected as a knob nobody would turn that
invites a non-integer value into a deterministic rule; storing a `move_cost`
field on the unit was rejected for the reason the `cost` comment already gives.

### Validation lives in `__init__`, after the wall check

The new assert is `energy >= health` guarded by `attack != 0`, placed after the
existing wall assert so that a wall (attack 0, energy 0) is already established
and exempt by the time it runs. Order matters for the message a player gets:
a type with attack 0 and energy 5 should still be told it is a broken wall, not
that its energy is fine.

The message names both numbers and the rule, e.g. *"a type that can move must
have at least as much energy as health: health 6 needs energy 6 or more"*,
because `define_type` shows it verbatim.

### The enemy-type reconstruction path gets a floor

`_typeFor` rebuilds an enemy's type from a unit record, and when the record
carries no `type_*` fields it falls back to the unit's **current** attack,
health and energy. Current energy is routinely below current health — that is
what spending looks like — so this path would construct types the new rule
refuses and turn a legitimate sighting into a crash. On that fallback branch
only, take `energy = max(energy, health)`. A record without `type_*` fields has
already lost the design values; the reconstruction exists to describe an enemy
that was seen, not to price one, and it must not fail on a unit that was
perfectly legal when its owner defined it. Records that do carry `type_*`
fields are unaffected, and they are what the current writer emits.

### Spec-visible arithmetic stays in whole numbers

Health is 1–10 and energy 0–100, so a move costs between 1 and 10 and a type
that can move always affords at least one. No rounding, no division, nothing
for the determinism suite to catch.

## Risks / Trade-offs

- **Every existing type with energy below health becomes illegal, in the test
  fixtures as much as in saved games.** → The suites define such types
  deliberately (a 1-energy unit testing the refusal path). Those fixtures move
  to a low-health, low-energy design that still exercises the same boundary —
  a health-1 type with energy 1 is refused on its second move as surely as the
  old fixture was on its first.
- **Heavy units may be too slow to be worth designing.** A health-10 unit with
  energy 100 gets ten moves a game, and rest returns 1 a turn. → That is the
  point of the change, and the point budget already charges for the energy that
  buys the moves. If play shows the slope is too steep, the lever is the rest
  rate, which this change deliberately leaves alone so the effect can be read
  on its own.
- **A wall is now defined by two rules that could drift apart.** → The wall
  exemption is written into the same assert as the rule it exempts, and the
  Walls requirement states it, so neither can be changed without the other
  being read.
- **A game saved before this change may hold an illegal type and fail to
  load.** → See Migration Plan.

## Migration Plan

There is no storage version and no migration machinery, and a game is short.
The plan is to fail loudly rather than to rewrite a player's design:

1. Loading a player file whose type has energy below health must not kill the
   role with a bare `AssertionError` — `_load_players` does not wrap the
   construction the way `define_type` does, and SPEC_COVERAGE records that
   class of escape as a defect. Wrap it and raise `UnreadableGame` naming the
   type and the rule, which is what `_load_players` already does for a game
   whose contents cannot be trusted.
2. The fix is one edit to the player's YAML — raise that type's energy to at
   least its health — or a fresh game. Both are cheap; silently raising the
   energy for them would change a design the player chose and the budget they
   paid, without telling them.
3. Rollback is reverting the change: nothing is written in a new shape, so a
   game saved under the new rule loads unchanged under the old one.
