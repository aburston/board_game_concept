## 1. `SetNewGame` command

- [x] 1.1 Add `SetNewGame(new_game)` to `service/commands.py`, with a
      handler in `service/games.py` that calls `data.setNewGame(new_game)`.
      Verify with a direct `games.perform(data, SetNewGame(new_game=False))`
      unit test.

## 2. The commit endpoint

- [x] 2.1 Add `POST /games/<gameno>/players/<int:n>/commit` in
      `http/app.py`. For a player: `Game(repo, n).clientSave()` then
      `resolve_when_ready`. For the administrator: `serverSave`. Return
      `{"resolved": bool, "turn_number": T, "outcome": ...|null,
      "waiting_on": [...]}` with 200 for `resolved=true` and 202 for
      `resolved=false` (design.md — Decision 1).
- [x] 2.2 Add commit-endpoint tests in `test_http_api.py`. Cover:
      player commit that resolves the turn (one-player game), player
      commit that does not (two-player game with only one committed),
      admin setup commit (200 with `turn_number: 0`), board-too-small
      returning 400.

## 3. `HttpSession` write methods

- [x] 3.1 Implement `HttpSession.commit()` in `cli/backend.py`. POST
      the commit; return `True` for 200 or 202, `False` for a
      publish-side 400 (design.md — Decision 4). Invalidate the cache
      on success.
- [x] 3.2 Implement `HttpSession.resolve_pending()`. Same endpoint as
      `commit` (the admin's barrier check), but returns `None` when
      the response is 202 (barrier not met) and the resolved outcome
      when 200 (design.md — Decision 5).
- [x] 3.3 Implement `HttpSession.setNewGame(new_game)`. POST a
      `SetNewGame` command through the existing `/commands` endpoint;
      invalidate the cache. `LocalSession.setNewGame` stays as it was.

## 4. End-to-end client commit

- [x] 4.1 Add a `commit` test in `test_client_over_http.py` — a
      one-player game, `add type`, `add unit`, `commit`. Verify the
      client sees `commit complete` (or the equivalent local message)
      and the turn advances via a subsequent `show`.
- [x] 4.2 `bgcclient` REPL still calls `waitForTurn` after `commit`.
      Verify the commit test either has `waitForTurn` no-op'd for
      one-player games or that step 5's long-poll is not required for
      the commit path itself to complete. If the REPL blocks on
      `waitForTurn` after a resolved commit, decide whether to short
      it (turn already resolved → no need to wait) or let step 5
      finish it.

## 5. Finish

- [x] 5.1 Update `MODULE_DESCRIPTION.md`'s `http/app.py` note: the
      commit endpoint lives beside the write endpoint, and option
      (b) is what makes an unattended server optional.
- [x] 5.2 Run the full suite under both backends, `flake8`, `pylint`.
      Verify green on both backends and no new pylint message kind
      in any file that did not report it before.
- [x] 5.3 Run the full suite ten times over.
