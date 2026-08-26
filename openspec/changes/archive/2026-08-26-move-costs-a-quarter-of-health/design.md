## Context

See proposal.md — Why. The state this design has to work with:

- The previous change already made the fare a per-unit property:
  `UnitType.move_cost` is a read-only property returning `self.type_health`,
  read in exactly two places — `UnitType.planMove`, which refuses a move the
  unit cannot pay for, and `Board._move`, which charges every planned move
  once. Neither call site names a number, so both are already correct for any
  fare the property returns.
- Type validation is a run of `assert`s in `UnitType.__init__`. The relevant one
  is `assert (attack == 0 or energy >= health)`, placed after the wall check so
  a wall is exempt and a broken wall still gets the wall message.
  `service/games.define_type` catches these and re-raises as `GameError`, so an
  assertion message is what a player reads at the prompt.
- `Game._typeFor` rebuilds an enemy type from a unit record seen in contact.
  When the record carries no `type_*` fields it falls back to the unit's current
  attack, health and energy, and applies `energy = max(energy, health)` so that
  a legitimately spent unit does not construct an illegal type and crash the
  sighting.
- `Game._load_players` wraps type construction and raises `UnreadableGame` when
  a stored type breaks a rule.
- `GAME_RULES.md` R9 is a cost table, and `tests/test_cost_table.py` holds it to
  the code so the summary cannot drift from the rules it summarises.
- The project invariant: resolution is a pure function of the board and the
  orders.

## Goals / Non-Goals

**Goals:**

- Change the fare in one place, and let every rule that quotes it follow.
- Keep the fare integer arithmetic, with no float anywhere near a resolution
  rule.
- Move the type-validation floor with the fare rather than leaving it stating a
  second, different rule.
- Leave every game that loads today loading.

**Non-Goals:**

- No change to rest (`REST_GAIN` stays 1), to attack cost, to the deployment
  point formula, or to what a refused order reports.
- No configurable divisor. The fare is a quarter, written as a quarter; a knob
  invites a value that reintroduces the rounding question at run time.
- No change to `Board._move` or `UnitType.planMove`, which already read the
  property.

## Decisions

### The fare is `(type_health + 3) // 4`, not `math.ceil(health / 4)`

Both give the ceiling for the range in play, but `//` on two integers is exact
and `/` produces a float. A float in a rule that decides a turn is the kind of
thing the determinism invariant exists to keep out: it is exact for these
values today and stops being obviously exact the moment anyone widens the health
range or changes the divisor. `(h + 3) // 4` is the standard integer ceiling and
needs no import.

The property keeps its comment's argument for reading `type_health` rather than
current health — a wounded unit that moved more cheaply would make taking damage
a way to buy tempo — since that argument is about which health, not how much of
it.

### Rounding is up, and that is a rule, not an implementation detail

Rounding down gives a fare of 0 for health 1, 2 and 3. A unit that moves for
nothing is outside the energy economy entirely: it can cross the board for ever,
never has to rest, and the only thing that limits it is attacking. That is a
strictly worse game than the flat fare of 1 this rule replaced, and it would
apply to the cheapest units on the board — exactly the ones a player can buy
most of. So the fare has a floor of 1, and the spec says so as a requirement in
its own right rather than leaving it to be inferred from an arithmetic choice.

### The fare is now a step function, and health 1–4 are equally mobile

`ceil(h/4)` over health 1–10 gives 1,1,1,1,2,2,2,2,3,3. Two types differing only
in health can now have the same fare, which was impossible when the fare was the
health. Consequences, taken deliberately:

- The `Statistic Semantics` scenario "Health is paid for twice over" weakens
  from *the heavier pays more per square* to *the heavier pays at least as much*.
  That is the honest statement and the spec now makes it.
- Health 4 is the value to buy: four times the durability of health 1 for the
  same fare. Health 5 is the worst, buying one more point of health for a 100%
  increase in running cost. That is a real edge in the design space and it is
  visible from the table rather than hidden.

This granularity is the price of a fare that fits in 1–3 while health fits in
1–10, and a fare that fine-grained enough to be strictly monotonic would have to
be the health again.

### The validation floor becomes the movement cost, not a second number

`energy >= health` becomes `energy >= move_cost`. Written against the property
rather than against a recomputed `(health + 3) // 4`, so the rule the
constructor enforces is by construction the same rule movement charges: there is
one expression for the fare in the code and the floor reads it.

This means the assert must run after `type_health` is assigned, since
`move_cost` reads it. Today the asserts run before the `type_*` fields are set,
so the assignment block moves above the floor check. The range asserts and the
wall assert stay where they are and keep their order, so a broken wall still
gets the wall message rather than the floor one.

The floor only ever relaxes: `health >= ceil(health / 4)` for every health from
1 to 10, so every type legal under the old rule is legal under this one. No
saved game that loads today stops loading, and there is nothing to migrate.

### `_typeFor`'s reconstruction floor comes down with it

The fallback branch raises a seen enemy's energy to `max(energy, health)` so the
reconstruction cannot fail the assert. With the assert relaxed, that floor is
now higher than it needs to be, and it is not a harmless overshoot: the
reconstructed type is what the player is shown about an enemy, so an
unnecessarily high floor overstates what that enemy has left. It comes down to
the minimum the assert requires, which is the movement cost for that health.

### R9 and its test move together, as designed

`tests/test_cost_table.py` exists precisely so this cannot be changed in the
code without being changed in the rules. It will fail on this change until R9 is
rewritten, which is the intended behaviour and the reason the test was written.

## Risks / Trade-offs

- **This is the third setting of this dial in three days** (1, then health, now
  health ÷ 4), and each setting invalidated a series of games. → The games are
  the evidence and replaying them is cheap; the harness exists for this. What
  is not cheap is the rules, specs and tests disagreeing about which setting is
  current, which is why the change goes through the same spec-first route as
  the last one and why R9's test is the gate.
- **A quarter may still be the wrong rate.** → It is a rate chosen from
  evidence: at 1 a turn of rest, a health-10 unit now buys a square every three
  quiet turns instead of every ten, and a health-4 unit is as mobile as a scout.
  The series will be replayed and the report will say whether it plays. The
  lever if it is still wrong is the divisor or the rest rate, and this change
  deliberately leaves rest alone so the two can be read apart.
- **Health 5 is a trap** — one point of durability for double the fare. → It is
  a legible trap: R9's table shows every fare, so a player can see it before
  buying rather than discovering it in play.
- **The match bots budget against the fare** and will misprice movement until
  `matches/bots/common.py::fares` is moved with the rule. → That is a task in
  this change, not a follow-up, because a bot that misprices its own movement
  makes the replayed series worthless as evidence.

## Migration Plan

Nothing to migrate. The type-validation floor only relaxes, so every stored
game that loads before this change loads after it, and nothing is written in a
new shape. `Game._load_players` keeps its `UnreadableGame` wrapping, because a
hand-edited file can still hold a type below the new floor.

Rollback is reverting the change: a game saved under this rule is in the same
shape as one saved under the old rule, but a type designed under this rule with
energy below its health — legal here, illegal there — would be refused on load
after a rollback. That is the one direction that does not round-trip, and it is
the same direction the previous change already documented.
