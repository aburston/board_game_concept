## 1. Move `views.py` to the shared tier

- [x] 1.1 Create `board_game_concept/http/` (with `__init__.py`) and move
      `cli/views.py` there as `http/views.py`. Leave a re-export shim at
      `cli/views.py` so `show.py`, `complete.py` and every test that names
      `from board_game_concept.cli import views` keeps working (design.md —
      Decision 1). Verify by running the full suite green.

## 2. The Flask app

- [x] 2.1 Add `board_game_concept/http/app.py` with `create_app(base_path)`
      that returns a `flask.Flask` configured for a `games/` directory. Also
      register `GET /_/health` returning `{"ok": true}`, so a test that
      starts the app in a thread can wait for it to be ready (design.md —
      Decision 6).
- [x] 2.2 Add `GET /games/<gameno>/players/<int:n>/state` returning
      `{turn_number, outcome, new_game, unprocessed_moves, rejected,
      dropped, eliminated}`. Uses `Game(repository, n).load()` — one load
      per request (design.md — Decision 4). Return 404 for a missing
      game/player, 409 for `GameIsBusy`, 422 for `UnreadableGame`
      (design.md — Decision 5).
- [x] 2.3 Add `GET /games/<gameno>/players/<int:n>/views/<subject>`
      returning the JSON `views.<subject>_view(...)` produces. Subject in
      `board`, `units`, `types`, `players`, `pending`. An unknown subject
      is 404.
- [x] 2.4 Add `GET /games/<gameno>/players` returning `{"players": [n, ...]}`
      — the numbers a completion would need to complete.
- [x] 2.5 Add `tests/test_http_api.py` — Flask `app.test_client()`-based
      tests, one per endpoint against a game the test builds through the
      SQLite backend. Verify each endpoint returns the same JSON the
      `views.<subject>_view(...)` builders produce.

## 3. `HttpSession`

- [x] 3.1 Add `HttpSession(base_url, gameno, player_number)` in
      `cli/backend.py`. Uses `requests.Session()`. Reads (`getOutcome`,
      `getTurnNumber`, `getNewGame`, `getUnprocessedMoves`,
      `getRejected`, `getDropped`, `isEliminated`) fetch `state` and
      return the matching field. `load()` fetches `state` and caches
      the result (design.md — Decision 4 — a `load()` in the CLI is a
      whole refresh, not a repository read).
- [x] 3.2 The view-object reads: `getBoard()`, `getPlayers()`,
      `getEliminated()` return light objects that answer the same field
      reads `show.py` and `complete.py` do (design.md — Decision 3).
      `_HttpBoard` covers `size_x`, `size_y`. `getPlayers()` returns a
      mapping so `players[n]['types']` still works. `getEliminated()`
      returns a list of numbers.
- [x] 3.3 The write and wait methods raise: `perform` raises
      `NotImplementedError("perform: step 3")`, `commit` and
      `resolve_pending` raise `NotImplementedError("commit: step 3")`,
      `waitForTurn` and `waitForPlayerCommit` raise
      `NotImplementedError("wait: step 5")`. `setNewGame` follows step 3
      because it changes state.
- [x] 3.4 HTTP errors become the same `GameError` subclasses (design.md —
      Decision 5). A helper `_raise_for(status, body)` in the same file
      does the mapping.

## 4. The observer, over HTTP

- [x] 4.1 In `cli/session.py`, extend `make_repository`/`add_backend_argument`
      family with `add_server_argument(parser)` and `make_session(gameno,
      player_number, server=None, backend=None)`. When `server` is set,
      constructs `HttpSession(server, gameno, player_number)`; otherwise
      `LocalSession(make_repository(gameno, backend), player_number)`.
- [x] 4.2 Wire `bgcobserver.py` through `make_session`. Add `--server URL`
      via `add_server_argument`. Verify by starting an in-process Flask
      app on a random port and running the observer's usual `show board`,
      `show units`, `show types`, `show players`, `show pending`
      commands against it.
- [x] 4.3 Accept `--server URL` on `bgcclient.py` and `bgcserver.py`, but
      raise a clear `GameError` (or `sys.exit(1)` with a message) if it
      is set. The flag exists so the three binaries stay consistent;
      wiring their write and wait paths is step 3 and step 5.
- [x] 4.4 Add `tests/test_observer_over_http.py` — start
      `create_app(tmp_path)` in a `threading.Thread`, wait on
      `GET /_/health`, run the observer against
      `http://127.0.0.1:<port>`, check the same subjects
      `test_cli_observer_surface.py` checks locally. Tear down the thread
      on test teardown.

## 5. `bgcapiserver`

- [x] 5.1 Add `board_game_concept/http/bgcapiserver.py` with a `main()`
      that parses `--host` (default `127.0.0.1`), `--port` (default `8080`)
      and `--base-path` (default `.`), then calls
      `create_app(base_path).run(host, port)`. Add
      `bgcapiserver = "board_game_concept.http.bgcapiserver:main"` to
      `[project.scripts]` in `pyproject.toml`. `flask` and `requests`
      into `dependencies`.

## 6. Finish

- [x] 6.1 Update `MODULE_DESCRIPTION.md`: `http/` as a new tier, and the
      seam's two implementations. Every path it names exists.
- [x] 6.2 Run the full suite under both backends, `flake8 . --select=E9,
      F63,F7,F82`, `pylint --rcfile=.pylintrc`. Verify green on both
      backends and no new pylint message kind in any file that did not
      report it before.
- [x] 6.3 Run the full suite ten times over. HTTP over threads is exactly
      the kind of thing that is green once and wedged on the eleventh.
