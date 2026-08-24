## Why

`put-a-rest-api-under-the-cli` names step 6 as "flip the clients to the
HTTP backend — `bgcserver -g` = admin client". Steps 2–5 built every
piece of the HTTP tier the CLIs need: read, write, commit (with
option (b) inline resolve), and long-poll wait. What is left is
switching the shape so that, in HTTP mode, the three role binaries do
what their names imply against a REST server rather than against a
directory of files.

- **`bgcapiserver`** — already the HTTP server. Unchanged.
- **`bgcserver -g N`** in HTTP mode — becomes the interactive admin
  session (sets the board, registers players, ends setup). It commits
  and exits; the unattended resolver loop is unnecessary because option
  (b) makes the last player's commit resolve the turn.
- **`bgcclient <gameno> <player> --server URL`** — already works end
  to end after steps 3 and 5. This change makes the flag opt-in rather
  than "step 3 refuses".
- **`bgcobserver <gameno> --server URL`** — already works after step 2.

The three CLIs keep local mode too: `bgcserver -g N` without
`--server` still opens the directory and runs its own unattended
resolver, so nothing that runs locally today breaks.

## What Changes

- **`bgcserver`'s `--server URL` is honoured.** Removes the "step 3
  refusal" that step 2 left in place. In HTTP mode: setup runs
  interactively (`SetBoard`, `AddPlayer`, `load board`, `load player`,
  `commit`), and the server exits after commit rather than looping as
  an unattended resolver. The unattended loop is retained for local
  mode; HTTP mode does not need it (option b).

- **`BOARD_GAME_SERVER` env var promotes HTTP to the default.** Set it
  once for a shell and every role in that shell picks HTTP without
  `--server`. Unset, the roles are local, unchanged. This is where the
  "flip" lives: the operator points `$BOARD_GAME_SERVER` at
  `bgcapiserver` and every CLI honours it.

- **`bgcserver`'s file-transport prints are gated on local mode.** In
  HTTP mode, the CLI does not print the raw YAML of `data/units.yaml`
  after each resolution — there is no local file for it, and the
  server prints what a human wants over its own log. Local mode still
  prints, byte-identical.

- **A quickstart doc.** `README.md` gains a "run over HTTP" recipe:
  start `bgcapiserver`, `export BOARD_GAME_SERVER=http://127.0.0.1:8080`,
  run the roles as before.

**Test edits are expected.** `test_cli_server_surface.py` still runs
in local mode (pinned to YAML through the existing marker). A new
`test_server_over_http.py` runs the admin session against a Flask
thread, sets up a game, commits, and confirms the server exited.

Not in this change: retiring the filesystem transport or `notify.py`
(step 7), authentication, packaging `bgcapiserver` for production.

## Capabilities

None. Behaviour a user sees when they run the CLI is the same; what
changes is the seam it goes through when `--server` is on. `skip_specs`.

## Impact

- **CLI**: `bgcserver.py` — `--server URL` handled through
  `make_session`; the unattended resolver loop is skipped in HTTP
  mode. The print of the YAML units after each resolution is gated on
  `LocalSession`.
- **HTTP**: unchanged.
- **Tests**: `test_server_over_http.py` new — admin session end to
  end against a Flask thread.
- **Docs**: `README.md` gets a "run over HTTP" section;
  `MODULE_DESCRIPTION.md` names the flipped default.
