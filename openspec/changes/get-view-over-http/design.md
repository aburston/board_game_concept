## Context

See `proposal.md` — Why. What shapes this change is the interface
`extract-the-session-backend-seam` drew: the seam's read side is a set of
`get*` calls that today reach into a `Game` and can equally reach across a
network.

The seam already handles two of the three coupling problems the umbrella
named. The one it deliberately deferred — `getBoard`, `getPlayers`,
`getEliminated` returning live domain objects — is what this change
resolves for the read half.

## Goals / Non-Goals

**Goals:**
- A Flask app that serves the read side, keyed by game and player.
- `HttpSession` reads through it; `LocalSession` still works unchanged.
- `bgcobserver` runs end to end over HTTP without opening a game file.
- The wire format is the same JSON the terminal already renders through
  `views.py`, so the two views cannot drift.

**Non-Goals:**
- Writes over HTTP, `POST`/`PUT`/`DELETE` — step 3.
- Long-poll waiting for a turn — step 5.
- Authentication and authorisation — deferred (see the umbrella).
- TLS, gunicorn/uvicorn packaging — a production deployment is not a
  step-2 problem.
- Rewriting `show.py` to take view dicts instead of the objects it takes
  today — `HttpSession` returns objects that answer the same reads.

## Decisions

### 1. `board_game_concept/http/` is the tier

Not a top-level file, not under `cli/`. HTTP is neither of those: it is
the server the `cli` client(s) talk to. A separate package keeps the
imports honest — `cli/` may import from `http/` (to construct the
client's URLs and helpers), but not the other way round.

```
   board_game_concept/http/
     __init__.py     re-exports `create_app`, `serve`
     app.py          Flask factory + routes (this change's HTTP surface)
     views.py        the view builders moved from `cli/views.py`
     bgcapiserver.py `main()` for the console script
```

`cli/views.py` stays as a re-export of `http/views` so every current
caller (`show.py`, `complete.py`, `test_cli_views.py`, `test_completion
.py`, `test_cli_tables.py`) does not change.

### 2. Endpoints, one for each thing a role reads

```
   GET /games/<gameno>/players/<n>/state
   GET /games/<gameno>/players/<n>/views/<subject>    subject ∈
                                                     board, units, types,
                                                     players, pending
   GET /games/<gameno>/players
```

Each is exactly what a role's REPL asks for:

- `state`: `{turn_number, outcome, new_game, unprocessed_moves, rejected,
  dropped, eliminated}`. One request per screen refresh, one JSON.
- `views/<subject>`: the value `views.<subject>_view(...)` already
  produces. The observer's `show board` is a `GET` of `views/board`.
- `players` (without a player number): the numbers the game holds. The
  observer's completion needs this to complete a player name.

The player number appears in the path rather than in a header or a query
string because it names the identity of the session, and that is what
`Game(repository, number)` takes today. When authentication lands, the
identity moves to a token and the path stops carrying it; until then, it
is where the CLI code already has it.

### 3. `HttpSession` returns view objects, not view dicts

`show.py` and `complete.py` call `data.getBoard().size_x`,
`data.getPlayers()[n]['types']` and so on. Rewriting those callers to
consume dicts is a much larger change than this one — every render, every
completion path, every `getPlayers`-based test. So `HttpSession` fetches
the JSON and returns light objects that answer the same reads:

```python
class _HttpBoard:
    def __init__(self, view): self._view = view
    @property
    def size_x(self): return self._view['size_x']
    @property
    def size_y(self): return self._view['size_y']
    # `rows` and `units` deferred: an observer's `show board` renders
    # from the board view directly, and the units iteration lives in
    # `views.units_view`, which the server already computes
```

The client's `show board` shortcuts a level: it fetches `views/board`
directly and hands the result to the same renderer, rather than
fetching the board object and re-computing the view client-side. Only
callers that still need the shape of a `Board` reach `getBoard()`, and
those are named and small.

*Why not JSON dicts everywhere*: because there are twenty-odd callers,
each with its own subtle read. This change is meant to land the wire,
not to redraw every reader.

### 4. Views are recomputed per request, from a fresh session

The Flask app opens a `Game(repository, number)` and calls `load()` for
each request. That is what the CLI does today too; the game is small and
SQLite reads under `held(read=True)` are cheap. No app-level cache: a
cache would be one more thing that can lie about what is on the board.

The cost this pays is one `load()` per read. The observer refreshes on
demand, not on a timer, and a human refreshes at human speeds. If a
future load-testing view says this is the bottleneck, an app-level
game-state cache with an invalidation on `POST /commit` is a
one-file change.

### 5. Errors: the CLI turns them into the same words `LocalSession` did

`Session` methods raise on failure. `LocalSession` raises `GameError`
subclasses; `HttpSession` maps HTTP error codes to the same exception
kinds so the REPLs' `except GameError` blocks do not need to know
whether the failure came out of a database or off a wire.

```
   404 game / player      NoSuchGame / NoSuchPlayer
   409 game busy          GameIsBusy
   422 unreadable game    UnreadableGame
   any other 4xx / 5xx    GameError with the response body as the message
```

### 6. The test server is a Flask app in a background thread

`test_observer_over_http.py` starts the app on `127.0.0.1:<random port>`
in a `threading.Thread`, waits for a `GET /_/health` (a route the app
carries for exactly this purpose) to succeed, runs the observer against
that URL, and stops the thread when the test tears down. No subprocess,
no port file, no sleep-and-hope. `test_http_api.py` uses Flask's own
`app.test_client()` for a faster path.

## Risks / Trade-offs

- **A dev server for a test.** Flask's dev server is single-threaded and
  not for production; it is fine for a test. The proposal says so and
  the docs will too.

- **`HttpSession` returns lightweight objects rather than dicts.** Named
  as a trade-off in Decision 3. The alternative is a much larger CLI
  edit that this change is not the place for.

- **One `Game.load()` per read.** Named as a trade-off in Decision 4.
  Refresh rates are human-shaped; the cost is real but small, and a
  cache is available where and when it is needed.

- **Two Flask dependencies (`flask`, `requests`).** Both are small, both
  are ubiquitous, both are needed for the tier to exist. The alternative
  is the standard library's `http.server` and `urllib`, which cost a lot
  of ceremony to save two dependencies.

## Migration Plan

Within this change:

1. `views.py` moves from `cli/` to `http/`. `cli/views.py` becomes a
   re-export shim. The suite passes green.
2. The Flask app: routes for `state`, `views/<subject>`, `players`. Unit
   tests via `app.test_client()`.
3. `HttpSession` gains the read half. Write and wait methods raise
   `NotImplementedError('step 3')` / `'step 5'`.
4. `bgcobserver` gains `--server URL`. When set, it constructs
   `HttpSession`; without it, `LocalSession` as today.
5. `test_observer_over_http.py` runs the observer against a live Flask
   thread with the SQLite backend, and checks every subject the
   observer surface tests check locally.
6. `bgcapiserver` binary, `MODULE_DESCRIPTION.md`, `pyproject.toml`.

## Open Questions

None.
