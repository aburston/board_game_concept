## 1. The fare itself

- [ ] 1.1 Change `UnitType.move_cost` to return `(self.type_health + 3) // 4`,
  extending its comment with why the ceiling is taken with integer arithmetic
  rather than `math.ceil` and why it is rounded up rather than down; verify by
  asserting the fare for every health from 1 to 10 is `1,1,1,1,2,2,2,2,3,3` and
  that no float appears in the expression.
- [ ] 1.2 Verify that `UnitType.planMove` and `Board._move` are untouched — both
  already read `unit.move_cost` — by grepping `src/` for any literal movement
  fare and confirming the property is the only place the number is decided.
- [ ] 1.3 Verify with a test that a unit of health 4 loses 1 energy to a move, a
  unit of health 5 loses 2, a unit of health 10 loses 3, and a unit of health 1
  loses 1.
- [ ] 1.4 Verify with a test that a unit damaged to 1 health still pays its
  type's fare — the fare does not fall as the unit is worn down.
- [ ] 1.5 Verify with a test that no permitted health produces a fare of 0, so
  that no unit moves for nothing.

## 2. Type validation

- [ ] 2.1 Move the `type_attack` / `type_health` / `type_energy` assignment
  block above the energy-floor assert in `UnitType.__init__`, leaving the range
  asserts and the wall assert in their current order and position, and note in
  a comment why the assignments have to come first.
- [ ] 2.2 Change the floor assert from `energy >= health` to
  `energy >= self.move_cost`, so the constructor enforces the same expression
  movement charges rather than a second copy of it; update the message to name
  the movement cost and the energy. Verify by constructing (1, 6, 1) and
  expecting failure, (1, 6, 2) and expecting success.
- [ ] 2.3 Verify with a test that a type the old floor refused is now accepted —
  health 10 with energy 3 — and that no type legal under the old floor is
  refused by the new one.
- [ ] 2.4 Verify with a test that a wall (attack 0, health 7, energy 0) is still
  created, and that attack 0 with energy 5 still fails with the wall message
  rather than the floor message.
- [ ] 2.5 Verify at the CLI that `add type Heavy H 3 6 1` is refused through the
  existing `GameError` wrapping in `service/games.define_type` and that the
  printed message names the rule.

## 3. Reading a stored or reconstructed type

- [ ] 3.1 Lower the reconstruction floor in `Game._typeFor` from
  `max(energy, health)` to the minimum the assert now requires, and extend the
  comment with why the floor is the movement cost rather than the health: the
  reconstruction is what a player is shown about an enemy, so an unnecessary
  floor overstates what that enemy has left. Verify with a test that a seen unit
  record with health 8 and energy 2 reconstructs with energy 2, not 8.
- [ ] 3.2 Redesign the `test_a_stored_type_that_cannot_afford_a_move_is_refused`
  fixture in `tests/test_type_rule_loading.py` — health 6 with energy 5 is legal
  under the new floor — so that it is still refused, and verify it raises
  `UnreadableGame` naming the type.
- [ ] 3.3 Verify that a record carrying `type_*` fields is still unaffected by
  the reconstruction floor.

## 4. The tests that assert the old fare

- [ ] 4.1 Rewrite `tests/test_movement_cost.py` for the new fare: its module
  docstring, the parametrised fare-per-health test, the lightest/heaviest test,
  the exact-fare and one-short tests, the wounded-unit tests, and the head-on
  collision test that asserts 2 and 9 are charged. Add the fare-is-never-zero
  and equal-mobility cases. Verify by running the file.
- [ ] 4.2 Re-scan `tests/` for any other assertion that a move costs the health
  — `test_basic.py`, `test_simultaneous_movement.py`, `test_turn_events.py`,
  `test_walls.py`, `test_attack_cost.py` all reference the fare — and move each
  with the rule; verify by running the whole suite on both backends.
- [ ] 4.3 Verify `tests/test_determinism.py` still passes, since head-on
  collisions now charge two amounts that may be equal where they could not be
  before.

## 5. Rules and the cost table

- [ ] 5.1 Rewrite `GAME_RULES.md` R4.3 so a move costs a quarter of the unit's
  maximum health rounded up, state the fare's floor of 1, and follow the
  consequence through R4.5, the `add type` energy floor, and the R2.10 wall
  rationale; verify by grepping `GAME_RULES.md` for "maximum health" and
  confirming every remaining occurrence is correct under the new fare.
- [ ] 5.2 Rewrite the R9 cost table's movement rows and its "health is paid for
  three times" consequence, and add the fare-per-health table (1–4 → 1, 5–8 →
  2, 9–10 → 3) so a player can see the step function and the health-5 edge
  before buying; verify against the code.
- [ ] 5.3 Update `tests/test_cost_table.py` to hold R9 to the new fare, keeping
  its three failure modes (change the code and it fails, cite a rule that does
  not exist and it fails, delete the section and it fails); verify by breaking
  each one deliberately and confirming the failure.
- [ ] 5.4 Update `SPEC_COVERAGE.md` if this change closes or opens any
  divergence it records.

## 6. The match harness

- [ ] 6.1 Move `matches/bots/common.py::fares` to the new fare so every doctrine
  budgets against what movement actually charges, and update its docstring;
  verify by checking a health-10 bot now plans a step at 3 rather than 10.
- [ ] 6.2 Re-check `matches/bots/base.py::orders` and every doctrine's `floor`
  for arithmetic that assumed the health fare, and verify each doctrine still
  deploys within 200 points and is legal under the relaxed floor.

## 7. Sign-off

- [ ] 7.1 Verify the delta specs and the code agree: walk every scenario in
  `openspec/changes/move-costs-a-quarter-of-health/specs/unit-movement/spec.md`
  and `.../unit-types/spec.md` and name the test that covers it, adding a test
  for any scenario nothing covers.
- [ ] 7.2 Run the whole suite on both backends and the standalone harness
  (`python -m board_game_concept.test_suite`); verify all pass.
- [ ] 7.3 Replay the twenty-game series against the new fare and write the
  result up beside `matches/RESULTS-MOVE-COSTS-HEALTH.md`, so the evidence that
  motivated the change is answered by evidence.
