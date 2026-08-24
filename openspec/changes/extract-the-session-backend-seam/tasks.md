## 1. The seam, unused

- [ ] 1.1 Define the session interface in `cli/` with the surface from design.md
      — Decision 2: `open`, `view(subject)`, `names_for_completion`, the scalar
      reads (`outcome`, `turn_number`, `is_setup`/`set_setup`,
      `unprocessed_moves`, `rejected`, `dropped`, `is_eliminated`), `perform`,
      `commit`, `resolve_pending`, `wait_for_turn`, `wait_for_all_commits`, and
      the provisional `board` accessor (Decision 5). Nothing uses it yet; verify
      the suite is untouched and green.
- [ ] 1.2 Implement `LocalSession` over today's `Game`, `service.games` and the
      turn functions (design.md — Decision 3). `open` wraps `Game.load` with the
      error handling `cli/session.py:load_game` has now; `view` holds the board
      and calls `views.*`, lifted verbatim from `show.py:_view`; `commit` maps
      by identity (Decision 4). Verify with a unit test that a `LocalSession`
      drives a game through setup, a turn and an outcome, using no `Game`
      method the interface does not expose.

## 2. Reads through the seam

- [ ] 2.1 Move view building out of `show.py` into `LocalSession.view`, and have
      `perform_show` and `show_units` render what the session returns rather
      than calling `views.*` on a board. `views.py` and `render.py` do not
      change. Verify `tests/test_cli_views.py` and `tests/test_cli_tables.py`
      pass unedited — they test `views`/`render` directly, so they prove those
      did not move.
- [ ] 2.2 Have `complete.GameNames` take its unit and type names from the
      session's view data rather than from `getBoard()`/`getPlayers()`. Verify
      `tests/test_completion.py` passes unedited.

## 3. The roles on the seam

- [ ] 3.1 Rewrite `bgcobserver` against the session — read-only and smallest, so
      it is the safe first cut. Verify `tests/test_cli_observer_surface.py`
      passes with no edit.
- [ ] 3.2 Rewrite `bgcclient` against the session: `perform`, `commit`,
      `wait_for_turn`, and the scalar reads its loop makes. Verify
      `tests/test_cli_client_surface.py` and the client half of
      `tests/test_server_client_integration.py` pass with no edit.
- [ ] 3.3 Rewrite `bgcserver` against the session: setup `commit`,
      `resolve_pending` in the unattended loop, `wait_for_all_commits`, and the
      turn-log through the provisional `board` accessor (design.md — Decision 5),
      output unchanged. Verify `tests/test_cli_server_surface.py`,
      `tests/test_cli_outcome_surface.py` and the rest of
      `tests/test_server_client_integration.py` pass with no edit.

## 4. Finish

- [ ] 4.1 Verify no role imports `Game`, a repository, or a board type directly
      any more — the session is the only thing they hold. `grep` the three role
      files for `Game(`, `Repository`, `getBoard`, and confirm only the
      permitted uses remain (the server's turn-log via the accessor).
- [ ] 4.2 Update `MODULE_DESCRIPTION.md`'s `cli/` section to describe the seam:
      the REPLs talk to a session, `LocalSession` is today's in-process stack,
      and an HTTP implementation is what a later change slots in. Verify every
      path it names exists.
- [ ] 4.3 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green
      **with no test file edited** — the exit condition for a pure refactor —
      and lint reports no message kind in a file that it did not report before.
