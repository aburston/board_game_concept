## Context

See `proposal.md`. Steps 2–5 built the HTTP tier a client needs; step
6 makes it the default a real deployment reaches for. The umbrella
line — "`bgcserver -g` = admin client" — is what this change delivers:
in HTTP mode the same binary is an interactive admin session, not an
unattended resolver.

The local flow does not go away. Every test that runs `bgcserver`
directly against a game directory keeps passing; the "flip" is a
default a person points a shell at, not a rewrite of what the binary
means in isolation.

## Goals / Non-Goals

**Goals:**
- `bgcserver --server URL -g N` runs as an admin CLI over HTTP.
- `BOARD_GAME_SERVER` env var makes HTTP the default without the flag.
- Local mode unchanged: no `--server`, no env var → the binary opens a
  directory and runs the unattended resolver, byte-identical to today.
- `bgcserver` in HTTP mode does not need an unattended resolver loop;
  option (b) covers it.

**Non-Goals:**
- Retiring the local unattended mode. That is step 7 (retire the file
  transport) if it happens at all; nothing in this change forces it.
- Repurposing `bgcserver` (without `-g`) as the API server. The API
  server is `bgcapiserver`; the two binaries stay separate.
- New CLI arguments beyond what steps 2–5 added.

## Decisions

### 1. HTTP mode skips the unattended resolver

`bgcserver`'s loop today has two phases: interactive setup, and an
unattended resolver that waits for barrier and resolves. In HTTP mode
with option (b), the last player's commit resolves the turn during the
request that carried it. There is nothing for the unattended resolver
to do.

The simplest expression: in HTTP mode, after `setNewGame(False)` (the
setup commit), the binary exits. In local mode, it continues into the
unattended loop as it always did. The seam is `isinstance(data,
LocalSession)` — a shallow branch on the shape of the session, which
is honest about the two flows differing in what they do next.

### 2. The env var is where the "flip" lives

Setting `BOARD_GAME_SERVER=http://127.0.0.1:8080` in a shell picks HTTP
for every role in that shell:

```
   $ bgcapiserver &
   $ export BOARD_GAME_SERVER=http://127.0.0.1:8080
   $ bgcserver -g 1                      # admin
   $ bgcclient 1 2 &                     # player 2
   $ bgcobserver 1 &                     # observer
```

The env var reaches `session.default_server()` — the same fallback
`add_server_argument` uses today. Nothing new to add: what step 2
built is what step 6 uses.

### 3. The YAML print after each resolution is a local-mode thing

`bgcserver` prints `dump_units(units_document(board))` after each
resolution and after setup, so a human running it can see what
happened. Over HTTP, there is no local board object with the same
guarantees; the `HttpBoard` shim covers `size_x`/`size_y` but not the
whole board. The safest thing is to gate the print on
`isinstance(data, LocalSession)` — HTTP-mode `bgcserver` prints its
"commit complete" and lets the operator use the observer for a
visible board.

## Risks / Trade-offs

- **`isinstance(data, LocalSession)` in `bgcserver`.** Named as a
  trade-off: a proper "does this session hold a live board" question
  would live on the `Session` interface, and this is the seam that
  today does not have it. One place to change if we decide the
  question deserves a method.

- **HTTP-mode `bgcserver` does not print the board.** Named in
  Decision 3; the alternative is fetching a view and rendering it,
  which is what the observer does. `bgcserver` in HTTP mode is a
  setup tool, not a spectator.

- **The env var is silent.** A person who sets it and forgets sees
  every role go over HTTP. Fine: the equivalent local-mode complaint
  ("why does this open a directory instead of using my server?") is
  the same kind of thing, and the flag is documented.

## Migration Plan

1. Remove the "step 3" refusal from `bgcserver.py`; wire `--server`
   through `make_session`.
2. Skip the unattended loop in HTTP mode; gate the YAML print on
   local mode.
3. `test_server_over_http.py` — admin session end to end.
4. `README.md` — the quickstart.

## Open Questions

None.
