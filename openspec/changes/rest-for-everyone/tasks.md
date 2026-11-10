# Tasks

## 1. The rule

- [ ] 1.1 In `domain/unit.py`, set `REST_GAIN` to 2 and rewrite its comment; in `domain/board.py`, replace the rest step and the `resting` bookkeeping that fed it with one pass over the standing units that adds `REST_GAIN` up to `type_energy` and emits `rested` only where the energy rose, and remove the off-the-board exception with the condition it served; verify `tests/test_energy_regeneration.py`, rewritten to the delta's scenarios (two a turn for a unit that did nothing, for one that moved, for one that fought, for one whose meter charged, for a sleeper; capped at the type's energy and one short of it; a Wall at 0; a destroyed unit nothing; no `rested` line at full energy), passes.
- [ ] 1.2 Bring the fixtures that counted on a unit not resting, or on resting one point, to the new arithmetic: `tests/test_think_phase.py` (the meter-charged and halted-controller energies), `test_sleep.py` (the struck sleeper), `test_walls.py`, `test_turn_events.py` and `test_turn_feed.py` (the `rested` lines), `test_resolve_game.py` (the tenth-turn blow and the quiet sleepers) and any other that asserts an energy after a turn; verify each file passes on SQLite.
- [ ] 1.3 Verify the catalogue and the harness through the game: `tests/test_default_army.py` (the mirror, the whole army out, the caps, the restated programs) and `tests/test_match_harness.py` pass, and note in the tasks file any doctrine test whose expectation had to move and why.

## 2. The documents

- [ ] 2.1 Rewrite `GAME_RULES.md` R3.9 as "Every unit recovers 2 energy a turn" and bring every rule that cites it to the new rule: R2.5's account of energy, R2.10's floor reasoning, R3.4's phase list, R7.1's reason an exhausted unit still counts, the R9 rows for resting and for a turn with an order, and R10.6's line on sleep; verify by grep for `R3.9` that every citation reads true.
- [ ] 2.2 Update `README.md` and `MODULE_DESCRIPTION.md` wherever resting is described, and `SPEC_COVERAGE.md` with a row for the requirement and where it is held; verify by grep for "rest" in each.
- [ ] 2.3 Add a superseded notice at the head of `matches/RESULTS-PROGRAMMED.md` and `matches/RESULTS-ARMY-THAT-PLAYS.md` saying the games were played when a unit recovered one energy only on a turn it did nothing; verify both read correctly.

## 3. Closing

- [ ] 3.1 Run `pytest` on both backends and `pytest -m slow`; verify all green.
