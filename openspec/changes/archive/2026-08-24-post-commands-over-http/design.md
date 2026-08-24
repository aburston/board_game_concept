## Context

See `proposal.md` — Why. Step 2 landed the read half and left every
mutation raising `NotImplementedError`. The shape this change fills in
is exactly what `games.perform` already accepts locally: one command
object at a time, decoded from a record.

`service/commands.as_record` and `service/commands.from_record` were the
draft's on-disk format before this change; they are also what the wire
carries. Nothing new to design — the client encodes its command with
`as_record`, the server decodes with `from_record` and calls
`games.perform`. The same rules that refuse a bad line refuse a bad
POST.

## Goals / Non-Goals

**Goals:**
- A single write endpoint that carries any command a role can perform.
- `HttpSession.perform` sends it; `bgcclient --server URL` covers every
  command it types today.
- The server's `Game` is what holds the draft. A crashed client that
  reopens finds the draft the way it did before HTTP was in the picture.
- Error mapping is what step 2 set up: 400 for a refused command with the
  `GameError` message in the body.

**Non-Goals:**
- Commit or resolve over HTTP — step 4.
- Long-poll — step 5.
- Batch commands, transactions, idempotency keys. One command, one POST,
  one 204. If a caller wants two commands atomic, they run them locally.
- New commands, new endpoints for `show`. The subject-per-endpoint
  temptation is what the draft already refused; one command endpoint is
  what makes the wire flat.

## Decisions

### 1. One endpoint, one command

```
   POST /games/<gameno>/players/<n>/commands
   Content-Type: application/json
   Body: {"kind": "AddUnit", "type_name": "Cross", "name": "x1",
          "x": 0, "y": 0}
   → 204 No Content on success
   → 400 with {"error": "..."} on any GameError
```

Not one endpoint per subject (`POST /types`, `POST /units`, `POST
/orders`). Two reasons:

1. The command grammar is the API. If a new command lands (a
   `TransferOwnership`, a `SetTerrain`), one place teaches every client
   about it: `service/commands.py`. A per-subject shape would need a
   new route and a new client method for every one.
2. `games.perform` is the one function that carries a command out. The
   HTTP surface is a thin wrapper over it; anything else would be a
   second copy of the rules `games.perform` already holds.

### 2. Held for writing, once per POST

The server opens a `Game(repository, n)`, calls `load()`, and holds it
for writing while `games.perform` runs. That is exactly what
`LocalSession.perform` does in-process; the seam is transparent.

*Why not hold across POSTs*: because the client would then be racing
its own barrier. `load()` re-reads the draft on every request so the
next command carries on from the last one; `perform`'s write is what
persists it. A held session across requests would look faster and
harder to reason about, without a measurable win.

*Why hold at all, if the read half didn't*: because `perform` writes,
and the YAML backend needs the advisory `flock` while it does. On
SQLite the transaction has the same shape. The reader was one atomic
`load()`; the writer is `load + perform`, and holding covers both.

### 3. `HttpSession.perform` invalidates the cached state

Every mutation throws away the cached `_state`, `_board` and `_players`.
The next reader fetches fresh. Ordinary caching, ordinary invalidation.

```python
def perform(self, command):
    record = as_record(command)
    response = self._session.post(
        f'{self.base_url}/games/{self.gameno}/players/'
        f'{self.player_number}/commands', json=record)
    _raise_for(response)
    self._state = None
    self._board = None
    self._players = None
```

`setNewGame` is the exception: only the server ever calls it during
setup, and it does not correspond to a `Node`-shaped command. It stays
`NotImplementedError` for step 4.

### 4. Errors are the same words the local session raises

`_raise_for` already maps 400/404/409/422 to `GameError` subclasses. A
refused command is 400 with the message; the client raises
`GameError(message)` and the REPL prints it the same way it prints a
refused command locally.

### 5. `load board` and `load player` still name a file on the caller

The command `LoadPlayer(path='/some/file.yaml')` carries a path. The
server does not open that path; the client does. The parsed content
becomes the command shape the server carries out.

*Why not a `POST /players` with the parsed body*: because that would
be a second shape for what is already the `LoadPlayer` command. The
change to make the server open a client's file is different from the
change to run a command over HTTP.

For step 3, `HttpSession.perform` catches `LoadPlayer` / `LoadBoard`
before it POSTs, opens the file on the client, and sends the effective
commands (`SetBoard(size_x, size_y)` for `LoadBoard`; `AddPlayer`
plus `AddType`s for `LoadPlayer` plus a draft-embedded units list). The
same effect as reading the file on the server, from the same content.

Not doing that in step 3 is the choice: `load` over HTTP still runs
locally on the client, and reaches the server only through the
subsequent per-command POSTs the local `load` would produce anyway.
For now, `LoadPlayer` / `LoadBoard` are refused by `HttpSession.perform`
with a clear "load: not yet supported over HTTP" message; the write
tests exercise `AddType`, `AddUnit`, `Move`, `RemoveUnit`, `SetBoard`
and `AddPlayer` — the ones a person types.

## Risks / Trade-offs

- **A refused command is a 400.** Every `GameError` becomes 400. A
  future distinction (a `NoSuchUnit` versus a `TypeAlreadyDefined`)
  would want its own subclass and status. Not this change.

- **`load` is refused over HTTP.** Named as a trade-off in Decision 5.
  A person driving a scripted setup will hit this and understand; a
  person driving an interactive game will not. The mechanism to do it
  right (open the file client-side, sequence the commands) is not
  step 3 either.

- **The client invalidates its whole cache on every write.** Fine:
  screens are small and reads are cheap; the alternative is targeted
  invalidation, which is a bug factory.

## Migration Plan

Within this change:

1. `POST /games/<gameno>/players/<n>/commands` in `app.py`.
2. `HttpSession.perform` and `setNewGame` in `cli/backend.py`
   (setNewGame remains `NotImplementedError` for step 4; noted here for
   symmetry). `HttpSession._invalidate_cache` if the invalidation grows
   more than three lines.
3. `LoadBoard` / `LoadPlayer` refused with a clear message.
4. `test_http_api.py` gains write coverage.
5. `test_client_over_http.py` runs the client's setup and deployment
   surface end to end over HTTP.
6. `MODULE_DESCRIPTION.md`.

## Open Questions

None.
