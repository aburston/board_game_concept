## Why

`put-a-rest-api-under-the-cli` names step 3 as the write side. Step 2
served the read half over HTTP; step 3 makes the client end-to-end. What
is missing from `bgcclient --server URL` is `perform`: every command a
person types (`add type`, `add unit`, `order`, `load board`, `load
player`) is a mutation the local session applied in-process and the HTTP
session did not know how to send.

The drafts change made the client stateless already: `add unit` records
to a durable draft on disk, and `show units` reads the draft back
through the same view. So one `POST` per command that goes through
`games.perform` on the server puts every mutation on the wire without a
protocol per subject. The server holds the draft; the client keeps
nothing.

Commit and long-poll stay on their own steps because each is its own
kind of hard: commit is the barrier (step 4), waiting is the
notification (step 5).

## What Changes

- **`POST /games/<gameno>/players/<n>/commands`.** Body is
  `{kind, ...fields}` — the record `service/commands.as_record`
  produces — decoded through `service/commands.from_record` (which
  raises for anything it does not recognise, the same way an unparseable
  line does). The server opens a `Game(repository, n)`, holds it for
  writing, calls `games.perform(game, command)`, and returns 204 on
  success. `GameError` becomes 400 with the message in the body.

- **`HttpSession.perform`.** Sends the POST, throws away the cached
  state on success (the next reader fetches fresh), and re-raises the
  `GameError` on failure. The command object turns into the record via
  the same `as_record` the server decodes with, so the two are one
  agreement.

- **`bgcclient --server URL` runs end to end, less `commit`.** Every
  command the client sends over HTTP works; `commit` still stops with a
  clear "step 4" message. That lets a person type `add type`, `add
  unit`, `show units`, `remove unit`, `order`, back and forth, against a
  live server.

- **`bgcserver` accepts `--server URL` but stops.** Same as step 2;
  writing the server side of the barrier is step 4.

- **`load board` and `load player` work over HTTP.** These read a YAML
  file from the caller's disk and hand its contents to the server as
  the same `AddPlayer`-style command shape. That means the file's path
  is still the caller's — the server does not open a file at a name a
  client typed — but the parsed content is what goes on the wire.

- **Draft replay is server-side.** A client that closes and reopens over
  HTTP finds its draft still on the server, because `Game.load()` on
  the server plays it back. Nothing on the client changes; nothing new
  is needed here.

**Test edits are expected.** A new `test_client_over_http.py` runs the
`bgcclient` surface (setup, deployment, reload) against a Flask
thread with the SQLite backend. `HttpSession.perform` gains direct
tests through `test_http_api.py`.

Not in this change: commit or resolve over HTTP (step 4), long-poll
(step 5), tail-flipping every client to HTTP as the default (step 6),
retiring the filesystem transport (step 7), authentication.

## Capabilities

None. Another slice of the session-backend seam, in the same shape as
step 2. The behaviour it constrains — what a role sees when it runs a
command — is unchanged. `skip_specs`.

## Impact

- **HTTP**: `http/app.py` — `POST /games/<gameno>/players/<n>/commands`.
  Errors keep the same status codes step 2 mapped; a refused command is
  400 with the message.
- **CLI**: `cli/backend.py` — `HttpSession.perform` implemented,
  `HttpSession.setNewGame` too (it is a mutation but nothing on the CLI
  side calls it in the client flow). `commit`, `resolve_pending`, `wait*`
  still raise.
- **Tests**: `test_http_api.py` gains a `POST /commands` block;
  `test_client_over_http.py` runs the client surface end to end.
- **Docs**: `MODULE_DESCRIPTION.md`'s `http/` note gains the mutation
  endpoint.
