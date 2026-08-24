## Context

See `proposal.md`. The `Notifier` interface `purify-the-repository-port`
carved out is what a local session waits through today: a `FifoNotifier`
blocks on a FIFO until the other side signals. The HTTP tier has no
such rendezvous; long-poll is what stands in until Server-Sent Events
or WebSockets are worth their weight, which is not this change.

## Goals / Non-Goals

**Goals:**
- Two `GET` endpoints, one per wait condition, each honest about the
  fact that its answer might be "still waiting".
- `HttpSession.waitForTurn` and `waitForPlayerCommit` block until the
  condition is met, looping `GET`s under the hood.
- The server-side wait is a short poll of the same condition
  `resolve_when_ready` and `wait_for_turn` already check.

**Non-Goals:**
- Streaming responses. Long-poll is a one-line client loop and a
  one-loop server implementation; SSE and WebSockets are what to reach
  for when a client needs push, and no client does yet.
- Retiring the FIFO transport. `notify.py` stays for the local flow;
  step 7 retires it.
- Sub-second latency. `POLL_INTERVAL` from `notify.py` (0.2s) is what
  the server polls at; the client's wait resolves within one poll of
  the condition being met.

## Decisions

### 1. Two endpoints, one condition each

```
   GET /games/<gameno>/players/<int:n>/wait/turn
   → 200 {"resolved": true, "turn_number": T}   turn resolved during wait
   → 200 {"resolved": false}                    timeout; poll again

   GET /games/<gameno>/players/<int:n>/wait/commit
   → 200 {"met": true, "committed": [n, ...]}   barrier closed
   → 200 {"met": false, "waiting_on": [n, ...]} timeout; poll again
```

Two endpoints because the two conditions differ. `wait/turn` asks "is
this player's `has_orders` False now?" - i.e. the server consumed the
orders. `wait/commit` asks "have the awaited players all committed?".
One endpoint with a query parameter would collapse them but each
answer carries different fields.

### 2. The server polls internally, up to `WAIT_BUDGET`

```
   WAIT_BUDGET = 25.0    # short enough to keep a proxy happy
   POLL_INTERVAL = 0.2   # from notify.py; matches the file-transport rate
```

`WAIT_BUDGET` is under 30 seconds so an intermediary (nginx, a load
balancer) does not close the connection thinking it hung. `POLL_INTERVAL`
matches the FIFO poller so latency is the same across transports.

The endpoint enters a loop: check the condition; if met, return the
"met" response; else sleep `POLL_INTERVAL`, until the budget runs out.
Each check opens `Game(repository, n)` and calls `held(read=True)` for
the read — cheap on SQLite (a shared transaction) and cheap on YAML
(a shared advisory lock).

*Why not use the `Notifier` in-process*: because the HTTP server would
have to wait on a FIFO the player-committer might not signal. The
signal is meant for the *other* transport (a bgcserver process reading
FIFOs); the HTTP tier is what replaces that transport, so it does the
polling directly.

### 3. `HttpSession` loops until the condition is met

```python
def waitForTurn(self):
    while True:
        response = self._session.get(
            f'{self.base_url}/games/{self.gameno}/players/'
            f'{self.player_number}/wait/turn', timeout=WAIT_BUDGET + 5)
        _raise_for(response)
        if response.json().get('resolved'):
            return
        # timed out; the condition was not met yet - loop
```

`WAIT_BUDGET + 5` for the client's `requests` timeout covers the round
trip. The client's socket cannot linger on a request the server is not
going to answer.

`waitForPlayerCommit` is the same shape with the other endpoint.

### 4. The wait is not itself the answer

Every existing caller of `waitForTurn` and `waitForPlayerCommit`
already re-checks the condition after the wait returns — the code
comment on `wait_for_all_commits` says it: "A hint, not an answer. …
every caller re-checks the condition it actually cares about". The
HTTP shape keeps that contract: the wait returning does not mean the
condition holds, it means one poll's worth of time has passed and the
caller should look.

## Risks / Trade-offs

- **Long-poll costs a request per wait budget.** Named as a
  trade-off: over a 5-minute idle a client sends ~12 requests. Fine.
  A wire that costs less is SSE or WebSockets; both are their own
  step and neither is needed yet.

- **Two players finishing at almost the same time may both see the
  same "resolved" response.** Both `waitForTurn`s return; the REPL
  handles it by re-reading state, which is what it did over FIFOs
  too. No correctness cost.

- **`WAIT_BUDGET` is 25s and not longer.** Some proxies allow 60s;
  some allow less. 25s is safe under the common defaults; a
  deployment behind a proxy that requires shorter can tune it, and
  one that allows longer gains nothing until the polling itself
  becomes cheaper (SSE).

## Migration Plan

1. `GET /wait/turn` and `GET /wait/commit` in `http/app.py`, using
   `Game.load()` under `held(read=True)` per iteration.
2. `HttpSession.waitForTurn` / `waitForPlayerCommit` in
   `cli/backend.py`.
3. `test_http_api.py` gains wait coverage;
   `test_wait_over_http.py` covers the client's loop end to end.
4. `MODULE_DESCRIPTION.md`.

## Open Questions

None.
