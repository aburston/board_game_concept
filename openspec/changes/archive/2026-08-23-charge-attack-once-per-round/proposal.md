## Why

A unit in a contested cell attacks every other unit in it, and is charged its
attack value in energy **for each of them**. In a three-way fight that is twice
the energy per round; in a four-way, three times. A unit that walks into a crowd
runs itself dry at a rate decided by how many opponents happen to be standing
there, which is not something it chose and not something it can see coming.

`combat-resolution` says "for each attack it makes", so the code matches the
spec. The rule itself is the thing being questioned: an attack is one swing, and
a unit should pay for swinging once a round, not once per opponent.

There is a second reason, found while checking the first. When a unit can afford
*some* but not all of its attacks in a round, **which opponents it hits is
decided by the order the cell happens to hold them in**. Three units with attack
2 and energy 2 — one strike each — produce six different damage distributions
across the six orderings of the cell:

```
cell order [a, b, c]: damage taken {a: 4, b: 2, c: 0}
cell order [b, c, a]: damage taken {a: 0, b: 4, c: 2}
```

That is the same order-dependence the `fix-rules-defects` change removed from
movement, still living in combat. Charging once a round removes it as a side
effect: a unit can afford the round or it cannot, so there is no partial round
left to distribute.

## What Changes

**BREAKING**: a unit is charged its attack value in energy **once per round of
a contest**, however many opponents it strikes in that round. It still deals its
attack value in damage to every one of them.

A unit whose energy is below its attack value still makes no attacks at all, so
inertness is unchanged. What changes is when a unit reaches it: a unit fighting
three opponents now lasts three times as many rounds as it used to.

The mid-round partial payment disappears with the per-opponent charge, so a
round is now all-or-nothing and no opponent is favoured by where it sits in the
cell.

### Consequence worth stating

Being outnumbered becomes energy-efficient: a unit facing three opponents deals
three times its attack in damage for one attack's worth of energy. It also takes
three attacks in return, so it is not a free ride — but the energy economics of
a crowd now favour the unit standing in it. That follows directly from "one
swing, one charge" and is the intended reading, not an oversight.

## The invariant this serves

**No randomness in the resolution of the rules.** A turn is a pure function of
the board and the orders given; the same orders on the same board always resolve
the same way. That is not a property of the current implementation to be
preserved by care — it is a rule of the game, and it constrains every rule added
to it.

Nothing in the engine reads a random number generator, a clock, or an object
identity, and nothing should. But determinism is not only about randomness: a
rule decided by where a unit sits in a list is unpredictable to a player in
exactly the way a die roll would be, while being harder to see. The `fix-rules-defects`
change removed one such rule from movement; the partial round above is the last
one left in combat.

This change therefore writes the invariant into `turn-commit`, where turn
resolution lives, with scenarios a test can hold it to.

## Capabilities

### New Capabilities

None.

### Modified Capabilities
- `combat-resolution`: attacking is charged once per round rather than once per
  opponent, and a round is all-or-nothing.
- `turn-commit`: resolution is deterministic, stated as an invariant of the game
  rather than left as a property of how it happens to be written.

## Impact

- **Engine**: `domain/unit.py` — `exchangeAttacks` alone.
- **Tests**: the energy arithmetic in `tests/test_combat_stalemate.py` and
  `tests/test_turn_events.py`, plus new scenarios for the per-round charge and
  for a round being all-or-nothing.
- **Docs**: `GAME_RULES.md` R5.3, which states the old arithmetic explicitly.
