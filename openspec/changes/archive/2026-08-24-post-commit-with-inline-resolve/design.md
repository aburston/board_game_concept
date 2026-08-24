## Context

See `proposal.md`. Option (b) was explored in an earlier session and
decided: the last commit that closes the barrier resolves the turn
inline, so no unattended `bgcserver` is required for HTTP flows.
`resolve_when_ready` in `service/turn.py` already does the barrier
check and the resolve under one hold, which is exactly what a request
carrying the last commit needs.

## Goals / Non-Goals

**Goals:**
- One endpoint that carries every kind of commit: player publish, admin
  setup, admin barrier-check-and-resolve.
- Publish and the inline resolve happen under separate holds — publish
  releases before `resolve_when_ready` takes its own hold, and the
  race that opens is one the design already handled (three answers,
  `None` = another caller got there first).
- `HttpSession.commit` returns the same `True`/`False` `LocalSession`
  returns today, so `bgcclient` does not care which is behind it.
- The response body is small and honest about what happened.

**Non-Goals:**
- Long-poll — step 5.
- Retiring `bgcserver` unattended — the umbrella keeps it, still
  reachable through the file transport and still resolving.
- Two-commit atomicity or idempotency keys. If the client's connection
  drops mid-commit, the state on disk decides: the commit is either
  recorded or is not.

## Decisions

### 1. One endpoint, three behaviours

```
   POST /games/<gameno>/players/<int:n>/commit
   → 200 {"resolved": true, "turn_number": T, "outcome": ...|null,
          "waiting_on": []}          the turn resolved during this request
   → 202 {"resolved": false, "turn_number": T, "waiting_on": [n, ...]}
                                    the commit was recorded; barrier open
```

For a player: the endpoint calls `LocalSession(player_n).commit()` on
the server, which is `Game.clientSave()` → `turn.publish`. Then, under
a fresh hold, `resolve_when_ready`. If it returned `None` the barrier
was not met; the response is 202.

For the administrator: `Game.serverSave()` → `turn.resolve`. The setup
resolution has no barrier and always resolves; the response is 200.

The two branches are decided by `identity.is_player(number)`, exactly
what `LocalSession.commit` does today.

### 2. Publish and resolve are separate holds; the race is safe

Two players might close the barrier at nearly the same instant. Both
would call publish; the second sees the first's `mark_committed` when
it checks the barrier. Only one of the two calls to
`resolve_when_ready` actually resolves; the other sees the turn has
advanced and returns `None`.

Under one hold both — combine publish and resolve into a single
transaction — is tempting, and wrong. `publish` deletes the caller's
draft and writes their order; `resolve` deletes every order and
advances the turn. Rolling both back on a single unrelated failure
inside `resolve` would waste the publish; committing them separately
is what makes the second commit's request see the first's fact.

### 3. `SetNewGame` becomes a proper command

`bgcserver` calls `setNewGame(False)` inline today to end setup. The
HTTP flow has nothing else to reach for — commands go through
`POST /commands`. So a new `SetNewGame(new_game: bool)` node in
`service/commands.py`, with a handler in `service/games.py` that
delegates to `data.setNewGame(new_game)`.

`HttpSession.setNewGame(value)` posts `{"kind": "set_new_game",
"new_game": value}` and invalidates the cache the same way `perform`
does. `LocalSession.setNewGame` still calls the Game method directly;
the command is only for the HTTP wire.

### 4. `HttpSession.commit` maps 202/200 to True

The seam contract: `commit()` returns `True` on success, `False` on a
publish-side failure the local session used to return `False` for
(board too small). The HTTP counterpart returns `True` for both 200
and 202: both are "your commit landed", the difference between them is
whether the turn also resolved, which the caller finds out through
`getOutcome`/`getTurnNumber` on the next `load()`.

Publish-side refusals — the board being too small — come back as 400.
The mapping is what step 2 set up; `HttpSession.commit` returns `False`
on those the way `LocalSession.commit` returns `False`.

### 5. `resolve_pending` reaches `/commit` too

The admin `bgcserver` loop calls `resolve_pending` at the top of each
turn. That is `resolve_when_ready` — the barrier-check-and-resolve.
Its HTTP shape is the admin's `POST /commit` at player number 0. The
endpoint is the same; the semantics fall out of who is asking.

## Risks / Trade-offs

- **The 202 response is a "poll again".** Named as a trade-off: the
  client sees `waiting_on` and knows what to do (wait for turn), but
  the actual waiting is step 5. Until then, a client that commits and
  is second on the barrier has to fall back to `waitForTurn` — which
  is still `NotImplementedError`. In practice the tests exercise the
  case where the committing client is the one that closes the barrier
  (a one-player game, or the last committer in a two-player game).

- **The publish/resolve gap is two holds, not one.** Named as a
  trade-off in Decision 2. The alternative is one long transaction
  that couples every commit to the whole board, and that costs more
  concurrency than the race is worth.

- **`SetNewGame` is a new command with one caller.** Fine: better one
  new node than a special-case endpoint that reaches around the
  command surface.

## Migration Plan

1. `SetNewGame` command + handler.
2. `POST /commit` in `http/app.py`.
3. `HttpSession.commit` / `resolve_pending` / `setNewGame`
   implemented.
4. Write tests: `test_http_api.py` covers the endpoint;
   `test_client_over_http.py` covers `commit` end to end.

## Open Questions

None.
