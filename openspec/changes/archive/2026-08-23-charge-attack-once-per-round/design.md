## Context

See `proposal.md` — Why.

`exchangeAttacks` in `domain/unit.py` runs the attack rounds. Each round it
takes the units undestroyed at the start of the round, and for every ordered
pair of them charges the attacker and damages the target:

```
for unit in standing:
    for target in standing:
        if unit is target: continue
        energy = unit.energy - unit.attack
        if energy < 0: continue          # <- decided per target, mid-round
        unit.energy = energy
        target.incomingAttack(unit.attack, events)
```

The charge and the affordability test are both inside the inner loop, which is
what makes the cost per opponent and what lets a round be half-paid.

## Goals / Non-Goals

**Goals:**

- A unit pays its attack value once per round it attacks in.
- A round is all or nothing, so no opponent is favoured by list position.
- The game stays fully deterministic.

**Non-Goals:**

- Changing how much damage is dealt. A unit still hits every opponent for its
  attack value; only the charge changes.
- Changing what inertness is, or when a unit reaches it within a round. A unit
  with energy below its attack value still makes no attack, exactly as now.
- An initiative statistic, or sequencing attacks within a round. That is `Q2`
  in `GAME_RULES.md` and is deliberately untouched.

## Decisions

### 1. Determinism is a goal of this change, not a risk of it

The engine contains no randomness at all — no random number generator, no
shuffle, no clock read, no identity-derived ordering. A turn is a pure function
of the board and the orders, which is what lets a test resolve the same orders
twice and compare.

This change makes combat *more* deterministic, not less. Today, a unit that can
afford some but not all of its attacks in a round strikes whichever opponents
come first in the cell's list, and that list order comes from the order units
were registered and moved. From a player's side that is unpredictable: the same
three units in the same cell distribute damage differently depending on
something they cannot see and did not choose.

Charging once a round deletes that case rather than choosing a rule for it. A
unit can pay for the round or it cannot; if it can, every opponent is struck; if
it cannot, none is. There is no partial round left to distribute and therefore
no tiebreak to arbitrate.

*Alternative considered:* keep the per-opponent charge and pick a deterministic
target order — by player number then unit name. It removes the unpredictability
too, but it replaces it with an arbitrary rule a player would have to learn
("you hit the lowest-numbered player first"), and it keeps the cost that
prompted this change. Rejected on both counts.

*Alternative considered:* keep the per-opponent charge and make the round all or
nothing — a unit that cannot pay for every attack makes none. Also
deterministic, but it makes a unit in a crowd go inert sooner rather than later,
which is the opposite of what was asked for.

### 2. The charge moves out of the inner loop

The affordability test and the charge both move up to the per-unit level: pay
once, then strike every opponent. The inner loop keeps only the damage, the
event, and the visibility record.

`attacked` events are still emitted one per target, because they describe
damage landing and a player reads them to see what was hit. The energy is
charged once regardless of how many events a round produces.

## Risks / Trade-offs

**Fights last longer, so a contest could run for many more rounds** → The
termination guarantee does not depend on energy: rounds stop when at most one
unit is undestroyed *or* when a round lands no attacks. Damage per round is
unchanged, so a contest that was decided by health is decided in exactly the
same number of rounds. Only a contest that used to end by exhaustion runs
longer, and it still ends — `tests/test_combat_stalemate.py` bounds it with a
timeout.

**Being outnumbered becomes energy-efficient** → Stated in the proposal as the
intended reading. A unit facing three opponents deals three times its attack for
one attack's worth of energy, and takes three attacks in return.

**Existing tests encode the old arithmetic** → Several assert energy after a
multi-round fight. Each is a deliberate update, not a rewrite: the damage
numbers they check are unchanged, only the energy is.
