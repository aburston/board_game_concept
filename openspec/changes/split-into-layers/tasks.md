## 1. Characterisation tests

Written against the current code, before anything moves. See design.md —
Decision 11. A scenario that fails here has found a divergence, not a
regression: record it, do not fix it.

- [x] 1.1 Add `tests/test_cli_server_surface.py` covering the `game-server`
      scenarios — blank input, unrecognised command, help, exit, board sizing
      and its refusals, adding players, loading board and player files, each
      `show` subcommand, incomplete `show`, commit and its refusal. Verify the
      new file passes, or record the failures under task 1.4.
- [x] 1.2 Add `tests/test_cli_client_surface.py` covering the `player-client`
      scenarios — startup and argument handling, blank input, unrecognised
      command, help, exit, defining types, deploying units, ordering moves and
      every refusal each of those has, the `show` subcommands, commit, and
      rejected-order reporting. Verify as for 1.1.
- [x] 1.3 Add `tests/test_cli_observer_surface.py` covering the `game-observer`
      scenarios — startup, argument handling, refusal of mutating commands,
      help, exit, every `show` subcommand, incomplete `show`, and reload. Verify
      as for 1.1.
- [x] 1.4 Cover the reload and read-only scenarios that need a resolved turn
      behind them. Verify the observer sees the units the server published.

## 1a. Correct the divergences the characterisation found

Each restores what the spec already requires (design.md — Decision 13).

- [x] 1a.1 Fix the arity guard on `add` and `load` at the server prompt, which
      tested `len(tokens) == 2` and let a bare verb reach `tokens[1]`. Verify
      `add` and `load` alone are reported rather than raising `IndexError`.
- [x] 1a.2 Replace the server's `show players` output, which printed an `email`
      field nothing sets, with the player numbers the spec asks for, and drop
      the dead `add_player(name, email)` stub. Verify `show players` lists a
      registered player instead of raising `KeyError`.
- [x] 1a.3 Validate board dimensions before constructing the board, so that a
      dimension below the minimum is reported as such rather than as
      non-numeric, and let the board report its own upper limit. Verify
      `set board 1 1` reports the minimum and `set board 4 4` still works.
- [x] 1a.4 Mirror a unit deployed during setup onto the view the server
      published, so its owner can see it before the turn resolves. Verify
      `show board` draws it and `show units` lists it, and that no unit the
      server has not revealed becomes visible.
- [x] 1a.6 Normalise player numbers to integers at every point they are read —
      the server prompt, a loaded player file, a unit dump and the client's
      argument — and have `Player` insist on one. Pulled forward from task 6.4:
      the mismatch is not cosmetic, it made any game created with
      `load player` unloadable, so the observer died on startup and the server
      would have died on its next turn. Verify the observer opens such a game
      and lists its units.
- [ ] 1a.5 Record all six in `SPEC_COVERAGE.md` under Known divergences, in
      the style of the existing entries, each marked fixed and naming the
      scenario that found it. Verify every divergence listed has a test.

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
- [ ] 3.2 Re-export from `board_game_concept/__init__.py` whatever the new
      layout makes sensible, and update `tests/test_basic.py`,
      `tests/test_combat_stalemate.py`, `tests/test_duplicate_seen_units.py` and
      `test_suite.py` to import from where things now live (design.md —
      Decision 2). Verify the whole suite passes and `board-game-test-suite`
      still runs.
- [ ] 3.3 Move `server.py`, `client.py` and `observer.py` under `cli/` and point
      the `pyproject.toml` console scripts at their new paths. Verify a
      `pip install -e .` exposes `board-game-server`, `board-game-client` and
      `board-game-observer`, and that the characterisation tests from task 1
      still pass.

## 4. Purify the engine

- [ ] 4.1 Add `cli/render.py` drawing the bordered grid (design.md — Decision
      12), remove `Board.print` and move its callers to the renderer, and delete
      the `board` import, `_FallbackBoard` and the `board` line in
      `requirements.txt`. Verify the characterisation tests still match the same
      board output and that `import board` appears nowhere.
- [ ] 4.2 Add `storage/serialise.py` holding the units and types YAML writers,
      remove `Board.listUnits` and `UnitType.dump`, and move their five test
      call sites onto the serialiser (design.md — Decision 3). Verify the units
      a game writes still round-trip through a save and load.
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
- [ ] 6.4 Convert unit statistics to integers at the parser and drop the
      `int()` re-casting below it, so a unit dump carries numbers rather than
      quoted strings (design.md — Decision 9). Player numbers are already
      integers; see task 1a.6. Verify the statistics survive a save and load
      without being re-cast on the way in.
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
- [ ] 7.3 Retire `GameData`, moving its callers onto the repository and the
      turn coordinator directly. Verify nothing imports `GameData` and the whole
      suite passes.
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
