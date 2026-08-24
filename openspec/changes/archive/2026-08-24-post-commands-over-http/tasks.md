## 1. The write endpoint

- [x] 1.1 Add `POST /games/<gameno>/players/<int:n>/commands` in
      `http/app.py`. Body is `{kind, ...fields}`; decode with
      `service/commands.from_record`, hold the game for writing, call
      `games.perform(game, command)`, return 204 on success
      (design.md — Decision 1). `GameError` becomes 400 with the message
      in `{"error": "..."}`.
- [x] 1.2 Add write tests in `tests/test_http_api.py`. Cover
      `SetBoard` (as administrator), `AddPlayer`, `AddType`,
      `AddUnit`, `Move`, `RemoveUnit`. Each verifies the mutation via
      a subsequent `GET /views/<subject>`.

## 2. `HttpSession.perform`

- [x] 2.1 Implement `HttpSession.perform(command)` in `cli/backend.py`.
      Send the POST with `as_record(command)`; on success, invalidate
      the cached `_state`, `_board` and `_players` (design.md —
      Decision 3). On failure, `_raise_for` maps the response to the
      same `GameError` subclass the local session raised.
- [x] 2.2 `LoadBoard` and `LoadPlayer` are refused with a clear
      "load: not yet supported over HTTP" `GameError` (design.md —
      Decision 5). This lands the mechanism as a follow-up.

## 3. The client, end to end

- [x] 3.1 `bgcclient` already accepts `--server URL` (step 2 added the
      flag with a "step 3" refusal). Remove the refusal so the flag
      constructs `HttpSession` via `make_session`; wire it through
      `argparse` if the positional-args path is not enough.
- [x] 3.2 Add `tests/test_client_over_http.py` — start
      `create_app(TEST_DIR)` in a `threading.Thread`, run the client
      against `--server URL`, cover: `add type`, `add unit`, `show
      units`, `remove unit`, `order`, `reload`. Commit still stops.
      Same shape as `test_observer_over_http.py`; pins itself to the
      SQLite backend.

## 4. Finish

- [x] 4.1 Update `MODULE_DESCRIPTION.md`'s `http/` note: the mutation
      endpoint lives beside the read endpoints, and the same
      `Session.perform` seam feeds both backends.
- [x] 4.2 Run the full suite under both backends, `flake8 . --select=
      E9,F63,F7,F82`, `pylint --rcfile=.pylintrc`. Verify green on
      both backends and no new pylint message kind in any file that
      did not report it before.
- [x] 4.3 Run the full suite ten times over.
