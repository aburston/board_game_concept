# Tasks

## 1. The controller

- [x] 1.1 Add `domain/program.py`: a parser from text to instructions (labels, `;` comments, operand checking, `SLEEP` 1-100) raising a `ProgramError` that names the line; verify with `tests/test_program_parser.py` that every instruction in the `unit-program` spec parses, that an unknown instruction, a bad operand, a jump to a missing label and `SLEEP 0` or `SLEEP 101` are refused naming the line, and that an empty program parses.
- [x] 1.2 Add the executor to `domain/program.py`: eight registers, a memory dictionary, the tick table as one dict, a `Snapshot` interface the sensors read (self, turn, extent, flags, map, contact, inbox), a per-turn tick cap of `10 × compute`, and a result holding the order, messages said and dropped, sleep, ticks and halt; verify with `tests/test_program_executor.py` that each instruction does what the spec's scenarios say and costs its ticks, that a later `MOVE` replaces an earlier, that a loop is counted and halts at the cap dropping its order, and that running the same program twice on the same snapshot gives identical results.
- [x] 1.3 Add `nearest` tie-breaking (distance, then lowest y, then lowest x) to the snapshot queries and verify with a test that two equidistant squares resolve to the lower y then lower x, for `NEAREST` and `FLAG enemy`.

## 2. Compute, the meter, sleep, the map and the radio in the domain

- [x] 2.1 Give `UnitType` a fourth statistic `compute` (0-10) and a `program`, widen `cost` to the four, refuse a program on compute 0, exempt compute-0 types from the energy floor, and refuse energy 0 with compute above 0; verify in `tests/test_unit_levels_compute.py` the scenarios of the `unit-types` delta: a wall, a scout, a turret, a wall with compute, a controllerless type below the fare, and the price of each.
- [x] 2.2 Add to a unit its meter, sleep countdown, woken flag, registers, memory and inbox, and a `think(snapshot)` step that runs the type's program, advances the meter, charges energy and records the trace; verify with `tests/test_meter.py` the meter scenarios: 6 ticks a turn on compute 2 pays on the fourth turn with 4 carried, 50 ticks on compute 5 pays once and halts, a unit at 0 energy halts at the filling instruction, and the fare is refused after the meter takes the last energy.
- [x] 2.3 Add `domain/army_map.py`: per player, per square `unknown | empty(turn) | friend | enemy(turn, attack, health)` plus flags, updated from the turn's record of standing and fighting, with `MAP` and `NEAREST` queries; verify with `tests/test_army_map.py` that a square walked on is known empty next turn, an enemy fought by one unit is known to all next turn, an unvisited enemy square is unknown, a stale sighting keeps its stamp, friends are always present, and a compute-0 unit's fight feeds the map.
- [x] 2.4 Add the think phase to `Board.commit` before `_deploy`: build one snapshot per army, run every awake controller, collect orders, deliver messages into pending inboxes sorted by (turn, sender name, order said), drop messages to non-friends into the sender's trace, decrement sleeps, skip eliminated players' controllers; verify with `tests/test_think_phase.py` that controllers see the board as the turn began, that a message sent this turn is read next turn in the settled order, that `SAY all` reaches every friendly controller and no enemy, and that an eliminated player's controllers do not run.
- [x] 2.5 Make combat set `woken` on every unit in a contested square and the rest phase clear a woken unit's sleep, and make rest apply to a sleeper and to a unit whose meter did not charge; verify with `tests/test_sleep.py` the sleep scenarios: three resting turns, a blow wakes and the controller runs next turn, a message does not wake, a sleeper's meter is untouched, `SLEEP 100` wakes on the hundred-and-first turn, and a thinking unit whose meter charged does not rest while one whose meter did not does.
- [x] 2.6 Extend `tests/test_determinism.py` to run the think phase under every permutation of a board's units with programs that read the map, say messages and sleep, requiring one record; and extend its source scan to `domain/program.py` and `domain/army_map.py`; verify by running it.

## 3. Resolution to the end and the record

- [x] 3.1 Add `resolve_game` to `service/turn.py`: under one hold, loop `resolve` from the first turn, write each turn's record, hash the whole state (units' square, health, energy, memory, meter, sleep, inbox; every army's map) after each turn, stop on a repeated hash, on a decision, or at `TURN_CAP = 500`, and record why; verify with `tests/test_resolve_game.py` that two unchanged stock armies stop undecided on the turn the state first repeats, that a decided game records its deciding turn, and that a game whose state never repeats stops at 500.
- [x] 3.2 Make the commit that completes setup call `resolve_game` (the last player's, locally through the server's wait and over HTTP inline) and remove the per-turn barrier, `wait_for_turn`, `publish` of movement orders and the per-turn commit marks; verify with `tests/test_two_player_commit.py` reworked that the second player's setup commit leaves the game resolved, and with `tests/test_server_client_integration.py` reworked that `bgcserver` resolves and exits after the last client commits.
- [x] 3.3 Add `read_turn(n)` / `write_turn(n, record)` to the repository port and both backends (a `turns` table; a `turns/` directory), the record holding board, units, flags, events, each army's map and every trace; verify with `tests/test_repository.py` and `tests/test_sqlite_repository.py` that a record round-trips byte-identically under both backends and that turn 7 of a 40-turn game reads as it was after turn 7.
- [x] 3.4 Persist `compute` and `program` on unit types in both backends, refuse opening a game whose stored types have no compute with an error naming the game, and extend `tests/test_type_rule_loading.py` and the storage tests to cover the round trip and the refusal; verify by running them.
- [x] 3.5 Make the per-seat rejection record carry the owner and filter by it, closing divergence 32; verify with a test that a player holding `pawn1` is told nothing about the other player's `pawn1`, and update `SPEC_COVERAGE.md` to mark 32 fixed.

## 4. The default army

- [x] 4.1 Add compute to every catalogue type in `domain/army.py` per the `default-army` delta, and the default programs (warden, sentry, hunter, explorer) as program text beside the catalogue; verify in `tests/test_default_army.py` the new costs (array 304, 16 left on 320), that every default program parses, and that each fits its type's per-turn cap on every turn of a stock-army game.
- [x] 4.2 Move the default budget to 320 in `domain/player.py` and the rules; verify in `tests/test_point_budget.py` and `tests/test_seeding_the_default_army.py` that a seat registered without a budget holds 320 and is seeded.
- [x] 4.3 Verify with `tests/test_full_game.py` reworked that two unchanged stock armies, resolved to the end, reach an outcome or an undecided stop with at least one unit of each army having moved on the first turn of play.

## 5. The command-line roles

- [x] 5.1 Add `set program <type> <file>` and `show program <type>` (listing with ticks, total, compute, ticks per energy, cap) to the client grammar, parser, completion, help and `service/games.py`; remove `move` and `hold`; verify with `tests/test_cli_client_surface.py` and `tests/test_grammar.py` reworked for the `player-client` delta's scenarios, and `tests/test_completion.py` for the new words.
- [x] 5.2 Add `show turn <n>`, `show turn <n> known`, `next` and `prev` to all three roles, reading the record and filtering traces by entitlement; make the client open a resolved game at its final turn with the result and refuse the replay while setups are outstanding; verify with the three `tests/test_cli_*_surface.py` suites reworked for the `player-client`, `game-server` and `game-observer` deltas.
- [x] 5.3 Rework `bgcserver`'s unattended cycle to wait for the last setup commit, resolve the game, report the result (or the undecided stop and why) and exit; verify with `tests/test_cli_server_surface.py` and `tests/test_server_over_http.py`.
- [x] 5.4 Rework the rejected-orders report to read from the record per turn; verify with `tests/test_turn_reporting.py` and `tests/test_cli_outcome_surface.py`.

## 6. The HTTP API and the web interface

- [ ] 6.1 Add endpoints for setting and reading a type's program with its listing, for reading a turn's record (board, units, flags, events, traces filtered by seat, a seat's map), and remove the order and hold endpoints; verify with `tests/test_http_api.py` and `tests/test_client_over_http.py` reworked, including that a seat's request for another seat's trace gets nothing.
- [ ] 6.2 Add compute and a program editor with a per-line tick listing to `armoury.js`, refusing a program on compute 0 and marking bad lines; verify with `tests/test_static_serving.py` source-level checks and a `node` run of the listing function against the tick table exported from the server.
- [ ] 6.3 Replace the ordering board in `play.js` and `board.js` with the replay: scrubber, play, pause, step, speed, movement between turns, the army-knew toggle, the trace panel, the setup wait, and the outcome at the final turn; remove box selection, drag-to-order, the compass, order arrows and the ordering keyboard; keep drag-to-deploy; verify with `tests/test_board_selection.py`, `tests/test_order_arrow.py` and `tests/test_web_flow.py` reworked to the `web-interface` delta.
- [ ] 6.4 Verify keyboard reach of setup and replay with a source-level test that every replay control has a key and the editor is focusable.

## 7. Rules, coverage and documentation

- [ ] 7.1 Rewrite `GAME_RULES.md`: compute in R2.4, R2.5 and R2.9; a new R10 for the controller (program, instruction set and ticks, meter, cap, sleep and waking, map, radio, trace); R3 for the think phase and resolution to the end; R6 for the map; R7 for the undecided stops; R8 for the new and removed commands; R9's cost table gains the meter row; verify by grepping for `commit` and `move` in R3 and R8 and finding only the setup commit and the controller's `MOVE`.
- [ ] 7.2 Update `SPEC_COVERAGE.md` (the `unit-program` row and where each requirement is held, divergence 32 fixed), `MODULE_DESCRIPTION.md` (programming no longer "not built"; the new modules) and `README.md` (writing a program, watching a replay); verify the documented commands run as written.
- [ ] 7.3 Run `openspec validate --specs --strict` after syncing; verify it passes.

## 8. The match harness and the first series

- [ ] 8.1 Rework `matches/arena.py` to set two seats up from two type files (statistics, compute, programs, placements, flag), commit, and read the record into `game_<n>.log` and `history.json`; rework `matches/bots/` into type files for the ten doctrines as programs; verify with `tests/test_match_harness.py` reworked that the record checker passes and a Garrison-against-Garrison game stops undecided on its first repeated state.
- [ ] 8.2 Play games 221-240 on the default board under the new rules with `matches/series.sh`, and write `matches/RESULTS-PROGRAMMED.md` with the rules table, results, what decided them, what the tariff cost each doctrine, and what it does not show; mark `RESULTS-DEFAULT-BOARD.md` superseded; verify every turn named is in its log.

## 9. Integration

- [ ] 9.1 Run `pytest` on both backends and `pytest -m slow`; verify all green.
