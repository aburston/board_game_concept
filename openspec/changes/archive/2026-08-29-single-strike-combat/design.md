## Context

See `proposal.md` — Why.

Combat lives in one function, `domain/unit.py`'s `exchangeAttacks`. It held a
`while True` loop: each pass recomputed who was standing, charged everyone who
could pay, applied their blows, and repeated until fewer than two stood or a
pass landed nothing. `resolveContest` and `resolveCollision` call it once and
settle the square from the survivors it returns — sole survivor holds, none
means empty, more than one means undecided and the movers fall back.

The determinism invariant (`tests/test_determinism.py`) forbids any outcome
depending on the order a list holds its members. The round loop already
honoured it by charging and striking from a snapshot of who stood at the start
of each round.

## Goals / Non-Goals

**Goals:**

- One strike per unit per turn in a contested square.
- The change confined to `exchangeAttacks`; the square-settlement code above
  it is left exactly as it is.

**Non-Goals:**

- Changing how a settled square is left. Sole survivor, empty, and
  undecided-so-fall-back are unchanged — there are simply more undecided
  contests now.
- Any new way to press a fight harder in one turn. Pressing is ordering the
  unit back in next turn.

## Decisions

**`exchangeAttacks` resolves one exchange and returns.** The `while` loop
becomes a single pass: snapshot who is standing, and for each unit that can pay
its attack value, charge it once and record a blow against every other unit in
the snapshot. All blows are gathered before any damage is applied, then applied
together. That the blows are gathered first is what keeps them simultaneous —
charging one unit cannot spare another, and destroying one cannot stop its own
blow, exactly as the round loop guaranteed within a round.

*Alternative considered:* cap the loop at one iteration with a counter. Same
behaviour, but it leaves a loop that reads as if it might run more than once,
which is the opposite of the rule it now enforces.

**The settlement code is untouched.** `resolveContest`/`resolveCollision`
already handle any survivor count. With one exchange, more contests end with
several survivors, so more end undecided and more movers fall back — but that
path already existed and is already tested, so nothing there changes.

**Determinism is unchanged and re-checked.** Blows are gathered from a snapshot
and their damage is commutative (summed onto health), so the order the square
holds its units in cannot change the result. `test_determinism.py` runs over
the new function.

## Risks / Trade-offs

- **A running game plays differently from its next turn** → Intended. There is
  no stored combat state; every turn is resolved fresh, so a game in progress
  simply resolves its next contest under the new rule.
- **Fights rarely end in one turn now** → Also intended: a contest that kills
  nothing is undecided and the movers fall back. Taking a defended square is a
  campaign of several turns rather than one grinding turn.
- **Two identical units no longer annihilate** → A stated consequence of the
  old model that many players relied on. It is called out in the proposal and
  rewritten in `GAME_RULES.md`; mutual destruction now needs a lethal single
  strike.
