## 1. The cost itself

- [x] 1.1 Replace `UnitType.MOVE_COST` with a read-only `move_cost` property on
  `UnitType` returning `self.type_health`, carrying a comment in the style of
  the neighbouring `cost` property on why it is computed rather than stored;
  verify by asserting `UnitType('T','T',3,4,50).move_cost == 4` and that
  `MOVE_COST` no longer exists on the class.
- [x] 1.2 Change `UnitType.planMove` to refuse on `self.energy < self.move_cost`
  and `Board._move` to charge `unit.energy -= unit.move_cost`; verify by
  grepping that no reference to `MOVE_COST` remains in `src/` and that the two
  call sites now read the per-unit cost.
- [x] 1.3 Verify with a new test that a unit of health 4 loses 4 energy to one
  move, a unit of health 1 loses 1, and a unit whose energy is one below its
  health does not move, keeps its energy, and is reported refused for want of
  energy.
- [x] 1.4 Verify with a new test that a unit damaged to 1 health still pays its
  type's health for a move — the fare does not fall as the unit is worn down.

## 2. Type validation

- [x] 2.1 Add the `energy >= health` assert to `UnitType.__init__`, guarded by
  `attack != 0` and placed after the existing wall assert so a wall is exempt
  and a broken wall still gets the wall message; the message names the health,
  the energy and the rule. Verify by constructing (1, 6, 5) and expecting the
  failure, and (1, 6, 6) and expecting success.
- [x] 2.2 Verify with a test that a wall (attack 0, health 7, energy 0) is still
  created, and that attack 0 with energy 5 still fails with the wall message
  rather than the new one.
- [x] 2.3 Verify at the CLI that `add type Heavy H 3 6 5` is refused through the
  existing `GameError` wrapping in `service/games.define_type`, and that the
  printed message names the rule — extend the client surface test that already
  covers a refused `add type`.

## 3. Loading a game that predates the rule

- [x] 3.1 Wrap the `UnitType` construction in `Game._load_players` so an illegal
  stored type raises `UnreadableGame` naming the type and the rule instead of
  escaping as a bare `AssertionError`; verify with a test that loads a player
  file holding a type with energy below health and asserts the error type and
  that the message names the type.
- [x] 3.2 Apply the `energy = max(energy, health)` floor to the fallback branch
  of `Game._typeFor`, where an enemy type is rebuilt from a record carrying no
  `type_*` fields, with a comment on why the reconstruction must not fail;
  verify with a test that a unit record without `type_*` fields whose current
  energy is below its current health is reconstructed rather than raising.
- [x] 3.3 Verify that a record that does carry `type_*` fields is unaffected by
  3.2 — the floor applies only to the fallback.

## 4. Fixtures the new rule makes illegal

- [x] 4.1 Redesign the twelve type definitions that now break the rule so each
  still exercises what its test is for: `tests/test_turn_events.py:62-63`,
  `tests/test_combat_stalemate.py:39-40, 103-104, 126, 329-332`, and the
  `max(energy, 1)` helper in `tests/test_attack_cost.py:19`. Prefer lowering
  health to raising energy, so the low-energy boundary each test is about is
  kept. Verify by re-running those files.
- [x] 4.2 Re-check `tests/player_1.yaml`, `tests/player_2.yaml`,
  `tests/game_harness.py` and `src/board_game_concept/test_suite.py` for stored
  or built types with energy below health, and fix any found; verify with a
  scan for `attack != 0 and energy < health` across `tests/` and `src/` that
  comes back empty.
- [x] 4.3 Re-run the whole suite (`pytest`) and the standalone harness
  (`python -m board_game_concept.test_suite`); verify both pass, and that
  `tests/test_determinism.py` and `tests/test_simultaneous_movement.py` in
  particular still pass, since head-on collisions now charge two different
  amounts.

## 5. Rules and coverage documents

- [x] 5.1 Rewrite `GAME_RULES.md` R4.3 so a move costs the unit's maximum
  health, and follow the consequence through R4.5, the R2.10 wall rationale
  ("a move costs 1 energy it does not have"), the statistic descriptions around
  lines 87-89, and the energy discussion around lines 226-252 and 374-377;
  verify by grepping `GAME_RULES.md` for "1 energy" and confirming every
  remaining occurrence is about rest or attack, not movement.
- [x] 5.2 Add the new type rule (a non-wall type's energy is at least its
  health) to `GAME_RULES.md` alongside the existing ranges under `add type`,
  and note the wall exemption; verify the table and the wall rule read
  consistently.
- [x] 5.3 Update `SPEC_COVERAGE.md` if this change closes or opens any
  divergence it records; verify by re-reading its movement and unit-type
  entries against the new specs.

## 6. Sign-off

- [x] 6.1 Verify the delta specs and the code agree: walk every scenario in
  `openspec/changes/move-costs-max-health/specs/unit-movement/spec.md` and
  `.../unit-types/spec.md` and name the test that covers it, adding a test for
  any scenario nothing covers.
- [x] 6.2 Run `openspec validate --strict` on the change and confirm it passes.
