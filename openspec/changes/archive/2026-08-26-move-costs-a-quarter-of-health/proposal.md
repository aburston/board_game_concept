## Why

Charging a move the unit's full maximum health made weight cost mobility, which
was the intent — but the slope is far too steep to play on. Twenty games under
the rule (`matches/RESULTS-MOVE-COSTS-HEALTH.md`) show what it does: a
ten-health unit pays 10 a square against a rest rate of 1 a turn, so it crosses
the board at **one square per ten turns**. Over a sixty-turn game that is six
squares on a board ten wide. Heavy units stopped being slow and became
furniture — in one game a player ordered `holds` on 59 of 60 turns because no
unit could afford a step, and neither army moved a square all game. Decisive
results fell from eight in twenty to five, and five of the draws are armies
that wanted to engage and could not afford to arrive.

The lesson is that the *direction* was right and the *rate* was wrong. A
quarter of maximum health keeps every property the change was made for — weight
costs mobility, armour is paid for in the field, a scout is quick where a brute
is ponderous — while compressing the fare from a 1–10 spread into a 1–3 one, so
a heavy unit is roughly three times the running cost of a scout rather than ten
times, and can still campaign.

## What Changes

- **BREAKING** A move costs the moving unit **a quarter of its maximum health**,
  rounded up: `ceil(health ÷ 4)`. Health is 1–10, so the fare is 1 for health
  1–4, 2 for health 5–8, and 3 for health 9–10.
- Rounding is **up**, so every unit that can move pays at least 1. Rounding down
  would make health 1–3 move for nothing, which would take movement out of the
  energy economy entirely for the cheapest units in the game.
- The cost is still read from the type's **design**, not from the health the
  unit has left: damage is not weight shed, a wounded unit pays what it paid
  while whole, and two units of the same type always pay the same.
- Every rule about paying stays exactly as it is, with "maximum health" replaced
  by "a quarter of maximum health": a unit that cannot pay does not move and is
  refused for want of energy; a mover entering a held square pays the fare and
  nothing more; both sides of a head-on collision pay their own.
- The constraint that a non-wall type is designed with **energy at least equal
  to its health** relaxes to **energy at least equal to its movement cost** —
  the same rule (a type must be able to afford one move) against the new fare.
  This is a pure relaxation: every type legal under the old rule is still legal,
  because `health >= ceil(health ÷ 4)` for every health in range.
- Rest is untouched (still 1 energy a turn), attack cost is untouched (still the
  attack value per round), and the deployment price is untouched
  (`attack + health + energy`).
- Walls are untouched. A wall is attack 0 and energy 0, exempt from the energy
  floor, and still cannot pay a fare of anything.

## Capabilities

### New Capabilities

None — this changes the number two existing capabilities require, not what the
system can do.

### Modified Capabilities

- `unit-movement`: the "Movement Costs Energy" requirement changes from the
  mover's maximum health to a quarter of it rounded up, and every requirement
  that restates the fare — entering a held square, the head-on collision —
  moves with it.
- `unit-types`: the energy floor for a non-wall type changes from its health to
  its movement cost, and the wall exemption is restated against the new fare.

## Impact

- Rules: `GAME_RULES.md` R4.3 (moving costs energy), R4.5, the `add type`
  energy floor, the R2.10 wall rationale, and the R9 cost table.
- Code: `domain/unit.py` — the `move_cost` property and the type-validation
  assert; `domain/board.py` is untouched, because it already charges
  `unit.move_cost` rather than a number.
- Tests: `tests/test_movement_cost.py` asserts the fare is the health at every
  health from 1 to 10; `tests/test_cost_table.py` holds `GAME_RULES.md` R9 to
  the code; `tests/test_type_rule_loading.py` has a fixture (health 6, energy 5)
  that the relaxed floor makes legal and which must be redesigned to still be
  refused.
- Existing saved games: **none break**. The floor only relaxes, so every stored
  type that loaded before still loads. The `UnreadableGame` path added by the
  previous change stays, because a type can still be stored below the floor.
- Match harness: `matches/bots/common.py::fares` computes the fare a bot budgets
  against and must be moved with the rule, or every doctrine misprices its own
  movement.
- Balance: this is the third setting of this dial (1, then health, now
  health ÷ 4). The series report is the evidence for the change and the series
  will be replayed against it.
