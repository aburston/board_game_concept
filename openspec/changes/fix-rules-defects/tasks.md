## 1. Reproduce the defects before fixing them

The gap that let `Q1` survive 227 passing tests is that nothing plays a game on
past a unit's death. Close that first, so every fix below has a test that was
red before it.

- [ ] 1.1 Add `tests/test_full_game.py` that plays a two-player game through server and client sessions until a unit is destroyed and on for two further turns; verify it fails today by resurrecting the destroyed unit
- [ ] 1.2 Add a test that a deployment refused for a duplicate name leaves `Board.units` unchanged; verify it fails today on the phantom unit `Board.add` registers before the name check
- [ ] 1.3 Add a test that resolves the same orders against boards whose units were registered in different orders and asserts identical final positions, health, energy and contested cells; verify it fails today
- [ ] 1.4 Add a test that two units ordered into each other's cells do not swap; verify it fails today
- [ ] 1.5 Add a test that a client session holds no record of an enemy unit it has not seen, and that `show types` lists no enemy type before contact; verify both fail today
- [ ] 1.6 Add a test that a player can order their own unit when an opponent registered the same unit name first; verify it fails today

## 2. Make placement validate before it registers

- [ ] 2.1 Reorder `Board.add` so bounds, cell occupancy and duplicate-name checks all run before anything is appended to `units` or `unit_dict`, and before the type is recorded against the player; verify 1.2 passes
- [ ] 2.2 Add a test that a cell named by a refused deployment is still free for another unit that turn; verify it passes

## 3. Make destruction final

- [ ] 3.1 Set a unit's state explicitly on the restore path in `Game._restore` / `Board.add(restoring=True)` so a restored unit is never left in `INITIAL`; verify a test asserting no restored unit is in `INITIAL` passes
- [ ] 3.2 Filter destroyed units out of the order file `turn.publish` writes; verify a test reading a committed player's order file finds no destroyed unit
- [ ] 3.3 Refuse any order in `turn._apply_orders` naming a unit the server holds as destroyed, recording the refusal; verify a test asserting the refusal and that no unit is created passes
- [ ] 3.4 Add a test that a destroyed unit does not reappear when the cell it died on falls empty, and that a living unit can take that cell; verify 1.1 now passes
- [ ] 3.5 Add a test that a player is told nothing about a destroyed unit on the turns after it died (`Q2`); verify it passes

## 4. Rewrite the movement phase as plan-then-apply

Design decisions 1 to 4. Land this behind the existing engine tests.

- [ ] 4.1 Reduce `UnitType.preCommit` to computing a target cell and reporting whether the move can be carried out, with no writes to the board; verify the existing engine tests still pass
- [ ] 4.2 Add a planning step to `Board.commit` that builds `(unit, origin, destination)` for every `MOVING` unit against the board as the turn began, plus a list of refusals; verify a unit test of the planner covers on-board, off-board and unaffordable moves
- [ ] 4.3 Detect head-on pairs in the plan — two moves whose origin and destination are each other's — and remove them from it; verify a unit test identifies a pair and leaves a chain of same-direction moves alone
- [ ] 4.4 Apply the plan by vacating every mover's origin and then placing every mover at its destination, charging one energy each; verify 1.3 passes
- [ ] 4.5 Change the movement cost to a flat 1 and delete the vestigial `speed` comment in `domain/unit.py`; verify a test that a unit with 100 energy has 99 after one move passes
- [ ] 4.6 Remove the energy-at-least-attack precondition on entering an occupied cell; verify a test that a unit with energy below its attack value still arrives and deals no damage in the contest passes
- [ ] 4.7 Resolve a head-on pair as a contest fought in place, with the survivor completing its move and an undecided pair staying put; verify 1.4 passes and tests for the one-survivor, no-survivor and undecided outcomes pass
- [ ] 4.8 Gather contested cells from the applied board — every cell holding more than one unit, plus each head-on pair — and hand them to the combat phase; verify the existing combat tests still pass

## 5. Report everything the server would not do

- [ ] 5.1 Emit an event from the movement phase for each move not carried out, naming the unit and the reason; verify a test of `Board.commit`'s returned events covers the unaffordable and off-board cases
- [ ] 5.2 Emit an event when a contest ends undecided, naming the contestants and the cell; verify a test asserting the event on a stand-off passes
- [ ] 5.3 Turn those events into rejection entries in `turn.resolve`, keeping the engine free of any knowledge of players' files; verify a test that a refused move appears in `players/<n>_rejected.yaml` with its reason passes
- [ ] 5.4 Report the new entries in the client's rejection summary; verify the CLI client surface test for each new reason passes
- [ ] 5.5 Refuse both deployments when two contend for one cell in the same turn, and publish the rejection to both players; verify the integration test asserting neither unit is placed and both players are told passes

## 6. Number the turns and decide the game

- [ ] 6.1 Persist a turn number with the game's shared data, set on each resolution and read on load; verify a test that a loaded game reports the last resolved turn number passes
- [ ] 6.2 Name the turn number in each published board, per-player view and rejection file; verify tests reading each file find it
- [ ] 6.3 Compute elimination in `turn.resolve` from the board after combat — a player is in the game while they hold a unit on the board and not destroyed — evaluated only from the first resolved turn onward; verify tests for the last-unit, inert-unit and never-deployed cases pass
- [ ] 6.4 Decide the game when at most one player is left, recording the winner or the draw and the deciding turn; verify tests for a win and for a mutual wipe-out pass
- [ ] 6.5 Persist the outcome and read it back on load; verify a test that every role opening a decided game reports the same result passes
- [ ] 6.6 Stop waiting on eliminated players in `turn.wait_for_all_commits`; verify a test that a turn resolves while an eliminated player has not committed passes
- [ ] 6.7 End the server's unattended cycle on a decided game, reporting the result and exiting with success, and report and exit when started against a game already decided; verify the CLI server surface tests for both pass

## 7. Give the client only what it may see

Design decision 6. Do this after section 6 so the outcome is already readable
from the shared data the client still reads.

- [ ] 7.1 Branch `Game.load` on the session's role so a player's client reads only its own view file and its own player file, and the observer and server read the shared record as now; verify 1.5 passes
- [ ] 7.2 Collapse `board` and `seen_board` into one board for a client session, and mirror a unit deployed during setup into it; verify the existing test that a just-deployed unit appears in `show board` and `show units` still passes
- [ ] 7.3 Derive `show types` from the client's view rather than from other players' files, so an enemy type is listed only after contact and drops out when contact lapses; verify the CLI client surface tests for both pass
- [ ] 7.4 Pass the ordering player to `getUnitByName` in `games.order_move`; verify 1.6 passes
- [ ] 7.5 Specify and implement what a client shows before any view has been published; verify a test of a client opened between setup and the first resolution passes

## 8. Report the outcome in the three roles

- [ ] 8.1 Report the winner or draw and refuse orders and commits in the client when the game is decided; verify the CLI client surface tests pass
- [ ] 8.2 Report elimination and refuse orders and commits for an eliminated player, leaving display and exit working; verify the CLI client surface test passes
- [ ] 8.3 Report the outcome and the last resolved turn number in the observer, including after `reload`; verify the CLI observer surface tests pass
- [ ] 8.4 Mark eliminated players in `show players` for every role that lists them; verify the surface tests pass

## 9. Write down the rules that were true but unstated

- [ ] 9.1 Add tests asserting the coordinate system — `(0, 0)` is the north-west cell, rendering draws `y = 0` first, and each direction moves the axis the spec says; verify they pass
- [ ] 9.2 Make destroyed units a marked casualty record: listed for their owner, marked destroyed and off the board, never drawn on a cell, and an enemy casualty visible only for the turn contact was made; verify tests for each pass

## 10. Reconcile the documents

- [ ] 10.1 Update `GAME_RULES.md` Part 1 to the rules this change lands, and cut Part 2 down to what is still open — `Q8`, `Q10` and `Q15` — recording the first two as design choices; verify the file names no defect this change fixed
- [ ] 10.2 Correct `README.md` so unit programming, the REST API and automatic winner resolution are described as not built; verify the file matches `MODULE_DESCRIPTION.md`'s "Not built yet"
- [ ] 10.3 Update `openspec/config.yaml`'s context, which still names `BoardGameConcept.py` and `GameData.py` removed by `split-into-layers`; verify it describes the current `domain`/`service`/`storage`/`cli` layout
- [ ] 10.4 Add the defects this change fixes to `SPEC_COVERAGE.md` under Known divergences, each with its reproduction; verify every `Q` number resolved here is accounted for
- [ ] 10.5 Update `MODULE_DESCRIPTION.md` — "How a turn goes", and remove the win condition from "Not built yet"; verify it matches the turn the code now resolves

## 11. Verify the whole change

- [ ] 11.1 Run `pytest` and verify the full suite passes, including every test added in section 1
- [ ] 11.2 Play a full two-player game to a decided outcome through the console scripts and verify the server exits reporting the winner, the client reports it, and the observer agrees
- [ ] 11.3 Run `openspec validate fix-rules-defects --strict` and verify it reports the change valid
