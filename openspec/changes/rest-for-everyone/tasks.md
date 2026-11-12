# Tasks

## 1. The rule

- [x] 1.1 In `domain/unit.py`, set `REST_GAIN` to 2 and rewrite its comment; in `domain/board.py`, replace the rest step and the `resting` bookkeeping that fed it with one pass over the standing units that adds `REST_GAIN` up to `type_energy` and emits `rested` only where the energy rose, and remove the off-the-board exception with the condition it served; verify `tests/test_energy_regeneration.py`, rewritten to the delta's scenarios (two a turn for a unit that did nothing, for one that moved, for one that fought, for one whose meter charged, for a sleeper; capped at the type's energy and one short of it; a Wall at 0; a destroyed unit nothing; no `rested` line at full energy), passes.
- [x] 1.2 Bring the fixtures that counted on a unit not resting, or on resting one point, to the new arithmetic: `tests/test_think_phase.py` (the meter-charged and halted-controller energies), `test_sleep.py` (the struck sleeper), `test_walls.py`, `test_turn_events.py` and `test_turn_feed.py` (the `rested` lines), `test_resolve_game.py` (the tenth-turn blow and the quiet sleepers) and any other that asserts an energy after a turn; verify each file passes on SQLite.
- [x] 1.3 Verify the catalogue and the harness through the game: `tests/test_default_army.py` (the mirror, the whole army out, the caps, the restated programs) and `tests/test_match_harness.py` pass, and note in the tasks file any doctrine test whose expectation had to move and why.
  - No doctrine or harness expectation moved: `test_default_army.py` and `test_match_harness.py` passed as they were.
  - Fixtures outside the proposal's list that counted on the old arithmetic and were brought to the new: `test_movement_cost.py` and `test_simultaneous_movement.py` (their `board_with` now designs each type `REST_GAIN` above the unit's starting energy so the fare can be read back; units that started at a hundred start at ninety), `test_attack_arithmetic.py`, `test_nobody_shares_a_square.py` (a Heavy now lands its second blow on a wall the turn after the first, ordered in every turn or not), `test_game_outcome.py`, `test_turn_reporting.py` and `test_walls.py` (a unit can no longer be walked to zero, so "spent" is now "below its fare"), and `test_cost_table.py`.

## 2. The documents

- [x] 2.1 Rewrite `GAME_RULES.md` R3.9 as "Every unit recovers 2 energy a turn" and bring every rule that cites it to the new rule: R2.5's account of energy, R2.10's floor reasoning, R3.4's phase list, R7.1's reason an exhausted unit still counts, the R9 rows for resting and for a turn with an order, and R10.6's line on sleep; verify by grep for `R3.9` that every citation reads true.
- [x] 2.2 Update `README.md` and `MODULE_DESCRIPTION.md` wherever resting is described, and `SPEC_COVERAGE.md` with a row for the requirement and where it is held; verify by grep for "rest" in each.
  - `README.md` describes the feed and the statistics without ever stating the rest rule, so nothing in it needed to move; `MODULE_DESCRIPTION.md` now names `REST_GAIN` in the domain layer's description.
- [x] 2.3 Add a superseded notice at the head of `matches/RESULTS-PROGRAMMED.md` and `matches/RESULTS-ARMY-THAT-PLAYS.md` saying the games were played when a unit recovered one energy only on a turn it did nothing; verify both read correctly.

## 3. Closing

- [x] 3.1 Run `pytest` on both backends and `pytest -m slow`; verify all green.
  - SQLite: 1860 passed, 105 skipped. YAML: 1719 passed, 246 skipped. Slow: 2 passed. Run one backend at a time: the CLI surface tests share `tests/games/_test-01` and a port, and three suites at once fail each other.
