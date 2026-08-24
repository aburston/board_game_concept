## 1. Pin the order before changing it

Written first, against the current code, so the test is known to fail for the
reason the change exists rather than passing for a reason nobody checked.

- [x] 1.1 Add a repository recorder that logs the operations one resolution
      calls, in order, and a test asserting the invariant from design.md —
      Decision 4: every `write_view`, `write_units` and `write_progress` before
      `clear_orders`; `clear_orders` before any `write_orders`; `clear_commits`
      before any `mark_committed`. Verify it fails today, naming
      `clear_orders` as happening too early, and record what it said.

## 2. Publish the turn, then release the waiters

- [x] 2.1 Split `resolve`'s per-player loop in two — what this turn published,
      then what the next turn is seeded with — and move `clear_orders()` and
      `clear_commits()` between the halves (design.md — Decision 1). Leave a
      comment at the split saying why the order matters, because the reason is
      what the recorder test cannot pin. Verify 1.1 now passes.
- [x] 2.2 Verify `clear_commits` still precedes the loaded player's
      `mark_committed` (design.md — Decision 2). Getting this backwards makes a
      `load player` game hang on a barrier waiting for a player who has nobody
      to commit for them, so it gets an assertion of its own rather than being
      left to 1.1.
- [x] 2.3 Verify resolution itself is unchanged: `tests/test_determinism.py`,
      `tests/test_full_game.py` and `tests/test_turn_events.py` pass unedited,
      and the same orders on the same board still resolve the same way.

## 3. The behaviour the change exists for

- [x] 3.1 Add a test that a player released from waiting reads the turn they
      waited for: commit a unit's deployment, resolve, and verify the view that
      player is then shown holds that unit rather than the previous turn's
      board. This is the empty board in proposal.md — Why.
- [x] 3.2 Add a test that a session loading a game part way through a resolution
      is told its orders are still pending, rather than being handed a partly
      published turn. `unprocessed_moves` reads the same fact and inherits the
      fix (design.md — Decision 3), which is the half of the bug with no symptom
      of its own.
- [x] 3.3 Verify a game set up with `load player` still gets its units onto the
      board — the trap in proposal.md, and what the obvious fix breaks. Verify
      at the service layer as well as through
      `tests/test_cli_observer_surface.py`, which opens a played game this way
      and would otherwise be the only thing catching it.

## 4. Finish

- [x] 4.1 Record the divergence in `SPEC_COVERAGE.md`, beside number 10 —
      loading a game racing the server deleting orders — since both come of the
      same file being deleted while the turn is still being written. Name the
      tests that now hold it, and say plainly that the residual exposure for a
      reader that holds no orders is not addressed.
- [x] 4.2 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does, and
      `pylint` against the configured `.pylintrc`. Verify the suite is green and
      lint reports no message kind in a file that it did not report before.
- [x] 4.3 Run the full suite ten times over and verify it is green every time.
      The defect showed twice in twenty-six runs before this change, so a single
      green run is not evidence that it is gone.
