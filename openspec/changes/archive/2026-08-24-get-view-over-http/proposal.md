## Why

`put-a-rest-api-under-the-cli` names step 2 as the read side over HTTP. Steps
0, 0b and 1 shaped the seam and the schema for it: the session-backend seam
is where an HTTP implementation slots in, and SQLite is the store both
sides talk to. What is missing is the wire.

The read side comes first because reads are the simple half: a `GET` that
returns a JSON view. Writes and long-poll are step 3 and step 5; each is
its own change because each is its own kind of hard.

The observer is the natural first customer: it only reads. A `bgcobserver`
that speaks HTTP end to end without ever opening a game file is proof the
seam does what the port was shaped to do. `bgcclient` and `bgcserver` still
have write and wait paths not yet on HTTP, so they stay on `LocalSession`
until step 3 and step 4 land.

## What Changes

- **A Flask HTTP tier.** `board_game_concept/http/` gains the app: a
  factory that returns a `flask.Flask` configured for a game directory,
  and a `serve(host, port)` entry point for the `bgcapiserver` binary.
  Read endpoints only. Nothing on this tier mutates a game.

- **`GET` endpoints for the read side.** For a game and player:
  - `GET /games/<gameno>/players/<n>/state` — the reading-half data:
    outcome, turn number, new-game flag, unprocessed-moves flag,
    rejected orders, dropped commands, eliminated flag.
  - `GET /games/<gameno>/players/<n>/views/<subject>` — one view per
    show subject: `board`, `units`, `types`, `players`, `pending`. The
    server computes the same JSON the terminal already renders — the
    format `views.py` produced is what goes on the wire.
  - `GET /games/<gameno>/players` — the player numbers registered. The
    observer's completion needs this.

- **`HttpSession`.** A `Session` implementation that talks HTTP. The read
  methods make a `GET` and return the JSON; the view-object reads
  (`getBoard`/`getPlayers`/`getEliminated`) return light view objects that
  present the fields `show.py` and `complete.py` already ask for
  (`board.size_x`, `players[number]['types']`), so those callers do not
  change. The write methods (`perform`, `commit`, `wait*`) raise
  `NotImplementedError`; step 3 fills them in.

- **`bgcobserver` gains `--server URL`.** With it, the observer
  constructs `HttpSession` instead of `LocalSession` and never opens the
  game directly. The command surface stays the same; `show board`,
  `show units`, `show types`, `show players`, `show pending` all work
  the same way the terminal user reads them today.

- **`bgcclient` and `bgcserver` also gain `--server URL`, and stop
  short.** The flag is accepted so the two binaries look consistent, and
  each raises a clear error if used at this step. Step 3 wires them up.

- **A new binary: `bgcapiserver`.** Reads the same `games/` directory the
  other binaries do, serves the HTTP tier. Local-only by default
  (`127.0.0.1:8080`); a real deployment binds where its operator wants.

**Test edits are expected.** The observer surface tests gain an
`HTTP`-parametrised variant that runs the same commands against a
Flask app spun up in a background thread. Nothing that any test asserts
about a command's output changes.

Not in this change: writes over HTTP, long-poll, authentication, TLS,
production packaging. Each of those is its own step.

## Capabilities

None. This is another implementation of the session-backend seam. The
behaviour it constrains — what a role sees when it asks for the board or
runs `show` — is unchanged. `skip_specs`.

## Impact

- **HTTP**: new `board_game_concept/http/` package:
  `app.py` (Flask factory + routes), `views.py` (moved from `cli/` —
  now shared with the tier), `__init__.py` re-exports. `bgcapiserver`
  binary added to `[project.scripts]`. `flask` added to
  `dependencies`; `requests` added for `HttpSession`.
- **CLI**: `cli/backend.py` — `HttpSession` alongside `LocalSession`.
  `cli/session.py` — a `--server URL` argument helper, and
  `make_session(...)` picks the implementation. `cli/bgcobserver.py`
  wires up `--server`; `cli/bgcclient.py` and `cli/bgcserver.py`
  accept it and raise until step 3. `cli/views.py` re-exports the
  moved module so `show.py`, `complete.py` and the tests that name it
  keep working.
- **Tests**: `test_http_api.py` (unit-level: the Flask test client
  against a game directory), `test_observer_over_http.py` (the observer
  end to end against a live Flask thread). No changes to any test that
  currently pins to a backend.
- **Docs**: `MODULE_DESCRIPTION.md` — the seam has two implementations
  now, and the HTTP tier is where a computed view is served.
