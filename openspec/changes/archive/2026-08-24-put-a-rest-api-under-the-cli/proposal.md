## Why

The README has wanted a web service since it was written: "combine server,
client and observer into different roles in the API based on login", a Flask
service exposing the CLI commands as REST, "moving to sqlite may be a thought".
The six changes since the layer split built the foundation for it without ever
naming it — the engine is pure, the use cases are one function each, the command
vocabulary is data, the views are plain data, the roles are a table, the
repository is a port, resolution is an atomic operation, and a session's
uncommitted work is durable server-side. What is left is the transport.

This is the umbrella plan for supplying it. The REST API becomes the sole path
to game logic; the filesystem stops being a message bus; a single HTTP server
hosts every game; and the turn resolves inline in whichever commit completes the
barrier. The three CLI commands are preserved **exactly as a user experiences
them** — they become clients of the API rather than readers and writers of a
shared directory.

It is a plan, not a behaviour change: it declares no spec deltas of its own.
Each step of the migration below is its own change, carrying its own delta specs
and tasks. This change exists so the whole shape is on record before any of them
starts — because the decisions with the longest reach (the store, the topology,
the resolution model) are cheapest to get right at the start and dearest to
revisit once code depends on them.

## What Changes

The endgame, stated as differences from today:

- **The REST API is the only way in.** Every game operation goes through it.
  Nothing reads or writes a game directory except the one process that serves
  the API.

- **SQLite replaces YAML as the store**, behind the repository port that already
  exists, with a real schema rather than YAML blobs in columns — typed tables
  that settle the string/int drift by force and make a turn-event log
  (replay, a visible combat record) nearly free, since `board.commit()` already
  returns the events `turn._report_turn` currently discards.

- **One server hosts all games.** `bgcserver` with no game number becomes that
  host; `bgcserver -g <n>` becomes the admin console for one game, an HTTP
  client of the host. This is the one change a user sees: the host is started
  once, rather than one server per game.

- **A commit resolves the turn inline.** Whichever commit completes the barrier
  resolves the turn, in the request that completed it — option (b) of
  `ARCHITECTURE_OPTIONS.md` §5. The unattended poll loop is retired; the server
  process that hosts the API is what resolves, triggered by the request rather
  than by watching files.

- **The CLIs become HTTP clients, their behaviour unchanged.** Same commands,
  same prompts, same output. `bgcclient` no longer holds a live game it mutates;
  it posts each command and fetches its view. Drafting already made this
  possible — a session's uncommitted work is server-side, so the client is thin.

- **The filesystem transport is retired.** Order files as an outbox, commit
  markers as semaphores, and the FIFO wake/waiter of `storage/notify.py` are
  replaced by HTTP request/response and a long-poll that tells a waiting player
  the turn has resolved.

**Deferred, deliberately:**

- **Authentication.** `player_number` stays the whole of identity for now, and
  the server is trusted to be reached only from the same machine. The identity
  seam is shaped so a token slots in later without re-cutting it. A server
  exposed to a network without auth is unsafe, and this plan says so rather than
  pretending otherwise.

- **A web UI.** The API is presentation-agnostic; a browser client is a later
  change that swaps the top tier only.

- **Postgres.** SQLite's single writer per database is the ceiling; if many busy
  games ever contend, Postgres is the escape hatch behind the same port. Not
  now.

- **Timed turns.** An untimed turn resolves on the last commit and needs no
  scheduler. A timed turn does, and it is out of scope.

## Capabilities

This change declares no spec deltas; `skip_specs` is set. It is a program that
spawns changes, and the behaviour lands in them. For the record, the capabilities
each step will touch:

- new `game-api` — the HTTP contract: the endpoints, their request and response
  shapes, and their per-role authorisation.
- `game-persistence` — the store becomes SQLite with a schema; views become a
  query rather than a materialised file; the transport role leaves it.
- `game-server`, `player-client`, `game-observer` — each role keeps its
  user-facing behaviour and gains an HTTP binding; `game-server` gains the
  host mode.
- `turn-commit` — resolution moves into the commit that completes the barrier.

The engine capabilities — `combat-resolution`, `unit-movement`, `unit-types`,
`board-model`, `visibility` — are untouched, as they have been through every
change this far. That they keep surviving is the sign the layering is sound.

## Impact

- **Kept, unchanged**: `domain/` entirely; `service/games.py`,
  `service/turn.py` (`resolve`, `resolve_when_ready`, `barrier_met`),
  `service/identity.py`; `service/commands.py`; `storage/repository.py` (the
  port). These are the API's foundation and were built for it.
- **Refiled**: `cli/views.py` and `cli/roles.py` have nothing to do with a
  terminal — they become the API's response shaping and endpoint authorisation.
- **Replaced**: `storage/yaml_repository.py` by a SQLite implementation of the
  same port (YAML may be kept as an export or test format); `storage/notify.py`
  by HTTP long-poll; the filesystem-as-transport entirely.
- **Reshaped, behaviour preserved**: the three `cli/` roles become HTTP clients
  over a session-backend seam; `bgcserver` gains its host mode.
- **New**: the HTTP layer (routes over the service layer), and the long-poll
  that replaces the wait.
- **The safety rail**: `tests/test_server_client_integration.py` drives the
  real binaries as subprocesses, so it checks the user-facing behaviour is
  preserved at every step. It is why "the CLI still works" is a checkable
  requirement and not a hope.
