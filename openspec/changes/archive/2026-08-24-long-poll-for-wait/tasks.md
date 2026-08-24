## 1. The wait endpoints

- [x] 1.1 Add `GET /games/<gameno>/players/<int:n>/wait/turn` in
      `http/app.py`. Loop up to `WAIT_BUDGET` seconds, checking each
      `POLL_INTERVAL` whether the player's orders have been consumed
      (`Game.getUnprocessedMoves()` False, or `has_orders(n)` False on
      the repository). Return `{"resolved": true, "turn_number": T}`
      when the condition met, else `{"resolved": false}` after the
      timeout (design.md — Decisions 1 and 2).
- [x] 1.2 Add `GET /games/<gameno>/players/<int:n>/wait/commit`. Loop
      until `_awaited_players` subset of `committed_players(turn)`, or
      the timeout. Return `{"met": true, "committed": [...]}` or
      `{"met": false, "waiting_on": [...]}`.

## 2. `HttpSession` wait methods

- [x] 2.1 Implement `HttpSession.waitForTurn` — loop `GET
      /wait/turn`s until the response says resolved. Client timeout is
      `WAIT_BUDGET + 5` so it always outlasts the server's budget.
- [x] 2.2 Implement `HttpSession.waitForPlayerCommit` — same shape
      with `/wait/commit`. Only the administrator calls it.

## 3. Tests

- [x] 3.1 `test_http_api.py` — wait endpoint coverage. A one-player
      game where the player has no pending orders returns `resolved:
      true` immediately; a game where the player has pending orders
      returns `resolved: false` after `WAIT_BUDGET` (use a small
      budget for tests).
- [x] 3.2 `test_wait_over_http.py` — the client-side loop end to end.
      Player 1 commits (locally) to close the barrier; the
      HttpSession waitForTurn returns promptly.

## 4. Finish

- [x] 4.1 Update `MODULE_DESCRIPTION.md`: the wait endpoints, and the
      backend's wait methods now implemented.
- [x] 4.2 Run the full suite under both backends, `flake8`, `pylint`.
- [x] 4.3 Run the full suite three times over.
