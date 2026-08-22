## 1. Characterisation tests

Written against the current code, before anything moves. See design.md —
Decision 11. A scenario that fails here has found a divergence, not a
regression: record it, do not fix it.

- [ ] 1.1 Add `tests/test_cli_server_surface.py` covering the `game-server`
      scenarios — blank input, unrecognised command, help, exit, board sizing
      and its refusals, adding players, loading board and player files, each
      `show` subcommand, incomplete `show`, commit and its refusal. Verify the
      new file passes, or record the failures under task 1.4.
- [ ] 1.2 Add `tests/test_cli_client_surface.py` covering the `player-client`
      scenarios — startup and argument handling, blank input, unrecognised
      command, help, exit, defining types, deploying units, ordering moves and
      every refusal each of those has, the `show` subcommands, commit, and
      rejected-order reporting. Verify as for 1.1.
- [ ] 1.3 Add `tests/test_cli_observer_surface.py` covering the `game-observer`
      scenarios — startup, argument handling, refusal of mutating commands,
      help, exit, every `show` subcommand, incomplete `show`, and reload. Verify
      as for 1.1.
- [ ] 1.4 Record every scenario that fails against the current code as a
      divergence in `SPEC_COVERAGE.md`, in the style of the existing entries,
      and mark the corresponding test `xfail` with a reason naming the
      divergence. Verify `pytest` is green with the xfails in place.

## 2. Remove the stale duplicates

- [ ] 2.1 Delete `src/BoardGameConcept.py` and `src/GameData.py`, left behind by
      the restructure in `7a26b26`. Verify nothing imports them
      (`grep -rn "^import GameData\|^from GameData\|^import BoardGameConcept"`)
      and that `pytest` stays green.

## 3. Package layout

- [ ] 3.1 Create the `domain`, `service`, `storage` and `cli` packages under
      `src/board_game_concept/` and move `BoardGameConcept.py` and `GameData.py`
      into them with no logic change, splitting `BoardGameConcept.py` into
      `domain/board.py`, `domain/unit.py` and `domain/player.py`. Verify
      `pytest` is green with no test file edited.
- [ ] 3.2 Keep `board_game_concept/__init__.py` exporting `UnitType`, `Board`,
      `Player`, `Empty` and `GameData` (design.md — Decision 2). Verify
      `python -c "from board_game_concept import UnitType, Board, Player, Empty, GameData"`
      succeeds and `board-game-test-suite` still runs.
- [ ] 3.3 Move `server.py`, `client.py` and `observer.py` under `cli/` and point
      the `pyproject.toml` console scripts at their new paths. Verify a
      `pip install -e .` exposes `board-game-server`, `board-game-client` and
      `board-game-observer`, and that the characterisation tests from task 1
      still pass.

## 4. Purify the engine

- [ ] 4.1 Add `cli/render.py` drawing the bordered grid (design.md — Decision
      12), reduce `Board.print` to a shim that renders and prints, and delete
      the `board` import, `_FallbackBoard` and the `board` line in
      `requirements.txt`. Verify the server characterisation tests still match
      the same board output and that `import board` appears nowhere.
- [ ] 4.2 Add `storage/serialise.py` holding the units and types YAML writers,
      and reduce `Board.listUnits` and `UnitType.dump` to shims over it
      (design.md — Decision 3). Verify a game saved before this task loads after
      it and `data/units.yaml` is byte-identical for the same board.
- [ ] 4.3 Add `domain/events.py` and have turn resolution return events instead
      of printing, with the CLI rendering them (design.md — Decision 4). Verify
      the unconditional narration reaching the terminal is unchanged and no
      `print` remains in `domain/`.

## 5. Grammar, parser and commands

- [ ] 5.1 Add `cli/grammar.py` and `cli/parser.py` — a hand-written recursive
      descent parser over the current grammar, structured for the nesting it
      does not yet have (design.md — Decision 5). Verify with a new
      `tests/test_parser.py` covering every production and every arity and
      keyword error, with no game state involved.
- [ ] 5.2 Add `service/commands.py` holding one command object per production,
      as a uniform tree with a visitor (design.md — Decision 6). Verify the
      parser tests assert on command objects rather than on strings.
- [ ] 5.3 Add `cli/roles.py` naming which commands each of the three roles may
      run, replacing the per-REPL role checks. Verify the observer
      characterisation test still refuses mutating commands with the same
      message.
- [ ] 5.4 Have all three CLIs parse to command objects and then run their
      existing code paths unchanged. Verify every characterisation test from
      task 1 passes with no edit, including the two divergences still marked
      xfail.
- [ ] 5.5 Generate each role's `help` output from the grammar and its role
      table, replacing the three hand-written strings. Verify the help
      scenarios in all three characterisation tests still pass.

## 6. Service layer

- [ ] 6.1 Add `service/errors.py` and replace the four `sys.exit` calls in
      `GameData.load` with raised errors the session loop catches and reports.
      Verify the messages reaching the terminal are unchanged and that
      `sys.exit` appears nowhere outside `cli/`.
- [ ] 6.2 Add `service/games.py` with one function per command object, moving
      the phase gating, ownership and occupancy rules out of the command loops
      (design.md — Decision 7). Verify the refusal scenarios in the
      characterisation tests pass with their current wording.
- [ ] 6.3 Reduce the three CLIs to parse → service → render over a shared
      session loop in `cli/session.py`. Verify all characterisation tests and
      `tests/test_server_client_integration.py` pass with no edit.

## 7. Repository port

- [ ] 7.1 Add `storage/repository.py` defining the `GameRepository` interface and
      `storage/yaml_repository.py` implementing it over the current file layout.
      Verify a game directory written before this task loads after it and that
      the files written are byte-identical.
- [ ] 7.2 Move the commit barrier and the order-consumption cycle into
      `service/turn.py`, leaving the repository holding only reads and writes
      (design.md — Decision 10). Verify
      `tests/test_server_client_integration.py` passes unedited.
- [ ] 7.3 Reduce `GameData` to a facade over the repository and the turn
      coordinator, keeping its current method names. Verify
      `tests/test_basic.py::test_game_data_initialization` passes unedited.
- [ ] 7.4 Make the game base path a constructor argument defaulting to
      `os.getcwd()`. Verify `GameData(gameno, player_number)` still resolves
      `games/_<gameno>` under the working directory, and that a test can point
      it at a temporary directory without `chdir`.

## 8. Finish

- [ ] 8.1 Rewrite `MODULE_DESCRIPTION.md` to describe the four packages instead
      of the three modules. Verify every path it names exists.
- [ ] 8.2 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green and
      lint reports nothing that was not already reported before the change.
