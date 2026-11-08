# Tasks

## 1. The army

- [ ] 1.1 In `domain/army.py`, swap the Lines and the Walls between the ranks of `ARRAY` (front: Pawn Pawn Line Heavy Heavy Line Pawn Pawn; back: Runner Scout Wall Keep Keep Wall Scout Runner) and update the comments that describe it; verify `tests/test_default_army.py`'s array tests (symmetry, both rows filled, seven of eight types, placement) pass and `test_the_array_costs_what_is_published` is updated to 308.
- [ ] 1.2 Give the Pawn compute 3 and a `VANGUARD` program: the harness's `advance2.asm` with its comments rewritten for the catalogue, the enemy's row kept in r6; verify `test_every_default_program_parses` and `test_each_default_program_fits_its_cap_on_every_turn` pass and the Pawn's `EXPECTED` row reads compute 3, cost 10.
- [ ] 1.3 In `HUNTER`, make `stay:` sleep a turn instead of holding, and say why in its comment; verify the cap test still passes and a new test in `tests/test_program_executor.py` or `test_default_army.py` shows a hunter blocked both ways ending its turn asleep.
- [ ] 1.4 Add a test to `tests/test_default_army.py` that plays the mirror of two unchanged arrays in process and asserts every unit with a controller except the Keeps stands off its seeded square at some turn in the first twenty turns of play; verify it passes on SQLite.
- [ ] 1.5 Add a test that plays the unchanged array against the same sixteen units with every program `HALT` and asserts the default wins within a hundred turns; verify it passes.
- [ ] 1.6 Bring `tests/test_match_harness.py`'s canned views, `tests/test_seeding_the_default_army.py`, `tests/test_full_game.py` and any fixture that names the array's squares or its 304 points to the new layout and 308; verify the whole suite passes on both backends.

## 2. The quiet stop

- [ ] 2.1 In `service/turn.py`, add `QUIET_CAP = 50` and have `resolve_game` keep the last turn whose events held a `moved`, `attacked`, `destroyed` or `flag_fallen` kind, stopping the game undecided with reason `quiet` and `since` that turn when fifty turns pass without one; verify with tests in `tests/test_resolve_game.py` for two sleeping Keeps stopping fifty turns after the last blow, a mover on turn 41 resetting the count, a blow every tenth turn keeping the game alive, and a repeat on turn 30 winning over quiet since turn 5.
- [ ] 2.2 Give the reason its words in `cli/session.py`'s `describe_outcome` and `http/static/play.js`'s `outcomeText` ("nothing happened for fifty turns (since turn n)"); verify `tests/test_cli_outcome_surface.py` and `tests/test_static_serving.py` cover the new wording.
- [ ] 2.3 Add the rule to `GAME_RULES.md` as R7.7 beside R7.5 and R7.6, and to R3.10's account of how a game ends; verify by reading the three back together.

## 3. The documents

- [ ] 3.1 Update `GAME_RULES.md` R2.13: the Pawn's row, the array drawing, 308 of 320, and the paragraph on why the slow rank stands in front, which now says why the Walls stand beside the Keeps; verify every number against `domain/army.py`.
- [ ] 3.2 Update `README.md` (the stock army costs 308 of 320) and `MODULE_DESCRIPTION.md`'s `army.py` entry; verify by grep for `304`.
- [ ] 3.3 In `SPEC_COVERAGE.md`, move the two findings under "Unspecified, and worth deciding" to a note that this change settled them, and add rows for the new scenarios and where they are held; verify the section reads as current.
- [ ] 3.4 Update the comments in `matches/bots/*.yaml` and `matches/bots/programs/screen.asm` that describe the stock array's rows, and `matches/bots/advance.yaml`, whose Pawn program is now the catalogue's; verify `tests/test_match_harness.py` passes.

## 4. Evidence

- [ ] 4.1 Replay games 221, 222, 223, 224 and 239 under the new default with `matches/arena.py` into games 241-245 (draw: garrison v garrison, advance v garrison, flag_hunt v garrison, screen v garrison, flag_hunt v flag_hunt), adding them to `matches/series.sh`; verify `matches/check_records.py 241 242 243 244 245` reports each complete.
- [ ] 4.2 Append an addendum to `matches/RESULTS-PROGRAMMED.md` saying what the five replayed games did under the new array, the vanguard and the quiet stop - whether the whole army got out, how each ended and on what turn, what the tariff cost - with a note at the head saying games 221-224 and 239 were played under the old array; verify every turn named is in its log.

## 5. Closing

- [ ] 5.1 Run `pytest` on both backends and `pytest -m slow`; verify all green.
