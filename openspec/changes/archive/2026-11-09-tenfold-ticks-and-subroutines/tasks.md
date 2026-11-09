# Tasks

## 1. The machine

- [x] 1.1 In `domain/program.py`, set `TICKS_PER_COMPUTE` to 100 and update its comment and the module docstring; verify `tests/test_program_executor.py`'s meter and cap tests are rewritten to the scenarios' new numbers (60 ticks on each of four turns pays on the fourth at 200; compute 5 halts at the 500th tick; a 300-tick program on compute 3 and 6) and pass.
- [x] 1.2 Add `CALL label` and `RET` to `TICKS` at 1 tick each and to `_check` (`CALL` takes a label that must exist, `RET` takes nothing), and a `CALL_DEPTH` of 16; verify `tests/test_program_parser.py` holds a call to a missing label refused naming the line, `RET` parsing, and the listing pricing both at 1.
- [x] 1.3 In `run`, keep a return stack for the run: `CALL` pushes the next program counter and jumps, `RET` pops and jumps, `RET` on an empty stack breaks out keeping the order so far, and a push beyond `CALL_DEPTH` sets `halted` to the `CALL`'s line and breaks; verify with tests in `tests/test_program_executor.py` for a call and return with its ticks, nested calls, a stray return keeping a `MOVE` already set, a recursive program halting at the seventeenth call with no order, and the stack being empty on the next run after a `SLEEP` inside a subroutine.
- [x] 1.4 Verify `GET /_/program` publishes `ticks_per_compute` 100 and `CALL` and `RET` in `ticks`, and that `POST /_/program/check` prices a program with a subroutine and refuses a call to nowhere naming the line, with tests in `tests/test_http_api.py`.

## 2. The catalogue

- [x] 2.1 Restate the hunter in `domain/army.py` with one subroutine for the step check (candidate square in, kind-is-passable out) called four times, and the explorer with one for its four candidates, leaving the vanguard's single check inline; keep the old text of each in `tests/test_default_army.py` and add a test that runs old and new against a set of snapshots - open board, friend ahead, enemy ahead, both ways blocked, no target - and requires the same order and sleep from each; verify it passes.
- [x] 2.2 Verify the restated programs through the game: `test_the_mirror_comes_out_a_mirror`, `test_each_default_program_fits_its_cap_on_every_turn`, `test_the_whole_army_gets_out` and the harness's `TestTheProgramsRunWithinTheirCaps` pass unchanged.
- [x] 2.3 Regenerate the four doctrine hunters under `matches/bots/programs/` from the catalogue and verify `tests/test_match_harness.py` passes.

## 3. The browser

- [x] 3.1 Change the two fallbacks of 10 for `ticks_per_compute` in `http/static/program.js` and `armoury.js` to 100; verify `tests/test_static_serving.py`'s listing-agreement test still prices a program with `CALL` and `RET` line for line with the server, and add that program to its cases.

## 4. The documents

- [x] 4.1 Update `GAME_RULES.md`: R2.4's account of what compute buys, the R9 rows for thinking and the meter, R10's cap and meter paragraphs and the instruction tariff table with `CALL` and `RET`, and a short paragraph on subroutines; verify every number against `domain/program.py`.
- [x] 4.2 Update `README.md`'s mention of the cap and `MODULE_DESCRIPTION.md`'s `program.py` entry (the return stack); verify by grep for "ten ticks" and "10 ×".
- [x] 4.3 In `SPEC_COVERAGE.md`, add rows for the subroutine requirement and the new meter numbers and where each is held; verify the section reads as current.

## 5. Closing

- [x] 5.1 Run `pytest` on both backends and `pytest -m slow`; verify all green. (SQLite 1851 passed, YAML 1710 passed, slow 2 passed.)
