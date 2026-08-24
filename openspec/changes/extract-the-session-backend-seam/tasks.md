## 1. The seam, unused

- [x] 1.1 Define the `Session` interface in `cli/` with the surface from
      design.md — Decision 2: `load`, `perform`, `commit`, `resolve_pending`,
      `wait_for_turn`, `wait_for_all_commits`, and the read methods under their
      `Game` names (`getOutcome`, `getTurnNumber`, `getNewGame`, `setNewGame`,
      `getUnprocessedMoves`, `getRejected`, `getDropped`, `isEliminated`, and the
      passthrough `getBoard`/`getPlayers`/`getEliminated`). Nothing uses it yet;
      verify the suite is untouched and green.
- [x] 1.2 Implement `LocalSession` over today's `Game`, `service.games` and the
      turn functions (design.md — Decision 3). `load` delegates `Game.load`;
      `perform` calls `games.perform` on the wrapped game; `commit` maps by
      identity (Decision 4); the reads delegate. Verify with a unit test that a
      `LocalSession` drives a game through setup, a turn and an outcome, using
      only the interface's methods.

## 2. Nothing below the seam moves

- [x] 2.1 Confirm `show.py`, `complete.py`, `views.py`, `render.py` and
      `cli/session.py` need no change: the session presents the `Game` read
      surface they call (`getBoard`, `getPlayers`, `getEliminated`, and the
      scalar reads), so `perform_show(session, ...)`, `show_units(session)`,
      `GameNames(session, n)` and `load_game(session)` work as written. Verify
      `tests/test_cli_views.py`, `tests/test_cli_tables.py` and
      `tests/test_completion.py` pass unedited.

## 3. The roles on the seam

- [x] 3.1 Rewrite `bgcobserver` against the session — read-only and smallest, so
      it is the safe first cut. Verify `tests/test_cli_observer_surface.py`
      passes with no edit.
- [x] 3.2 Rewrite `bgcclient` against the session: `perform`, `commit`,
      `wait_for_turn`, and the scalar reads its loop makes. Verify
      `tests/test_cli_client_surface.py` and the client half of
      `tests/test_server_client_integration.py` pass with no edit.
- [x] 3.3 Rewrite `bgcserver` against the session: setup `commit`,
      `resolve_pending` in the unattended loop, `wait_for_all_commits`, and the
      turn-log through the passthrough `getBoard` (design.md — Decision 5),
      output unchanged. Verify `tests/test_cli_server_surface.py`,
      `tests/test_cli_outcome_surface.py` and the rest of
      `tests/test_server_client_integration.py` pass with no edit.

## 4. Finish

- [x] 4.1 Verify no role constructs a `Game` or calls `service.games` directly
      any more — the session is the only thing they hold. `grep` the three role
      files for `Game(` and `games.perform`, and confirm the only remaining
      `getBoard` use is the server's turn-log passthrough.
- [x] 4.2 Update `MODULE_DESCRIPTION.md`'s `cli/` section to describe the seam:
      the REPLs talk to a session, `LocalSession` is today's in-process stack,
      and an HTTP implementation is what a later change slots in. Verify every
      path it names exists.
- [x] 4.3 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green
      **with no test file edited** — the exit condition for a pure refactor —
      and lint reports no message kind in a file that it did not report before.
