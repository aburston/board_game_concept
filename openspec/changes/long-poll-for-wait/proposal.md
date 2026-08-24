## Why

`put-a-rest-api-under-the-cli` names step 5 as long-poll. The read
side, the write side and the commit endpoint work; the only piece a
client still calls `NotImplementedError` on is *waiting* — the two
methods that block until a condition is met.

`bgcclient` needs `waitForTurn`: after it commits and the barrier is
still open (or after somebody else's commit resolved a turn), it
waits for the turn to actually resolve before printing. `bgcserver`
running as an admin needs `waitForPlayerCommit`: it sleeps until
everyone has committed, then resolves.

Long-poll is the shape: the client makes a request, the server holds
it for up to N seconds, either the condition is met and the server
responds, or the timeout hits and the server responds "still waiting".
Either way the client loops until it gets the answer it wanted. This
retires the FIFO transport for HTTP flows and lets step 6 flip the
default backend.

## What Changes

- **`GET /games/<gameno>/players/<n>/wait/turn`.** Long-polls until the
  player's orders are no longer pending (their turn resolved), or a
  short timeout. Returns 200 `{"resolved": true, "turn_number": T}`
  when the wait ended because the turn resolved; 200 `{"resolved":
  false}` when the timeout hit and the caller should ask again.

- **`GET /games/<gameno>/players/<n>/wait/commit`.** Long-polls until
  every awaited player has committed for the current turn, or the
  timeout. Only the administrator calls this. Returns 200 `{"met":
  true|false}`.

- **Server polls internally.** Each wait endpoint sleeps in short
  increments (`POLL_INTERVAL`, matching `notify.py`), checking the
  condition, until met or the total wait budget runs out. No FIFO
  reads; the endpoint stands on its own so the SQLite backend serves
  it the same way the YAML one does.

- **`HttpSession.waitForTurn` / `waitForPlayerCommit` implemented.**
  Each loops `GET`ing the endpoint until the response says the
  condition is met. The `_raise_for` mapping stays the same for
  errors.

- **The client's REPL flow unchanged.** `bgcclient` calls
  `waitForTurn` where it always did; that method blocks until the turn
  resolves, whether the caller is over HTTP or in-process.

**Test edits are expected.** A `test_wait_over_http.py` starts a
Flask thread, has one player commit locally to close the barrier, and
watches an `HttpSession.waitForTurn` return promptly. A second test
verifies the timeout path: no one else commits, the wait returns
`False` after the budget elapses, and the client loops.

Not in this change: retiring `notify.py`'s FIFO transport
(step 7 will), any authentication, streaming responses (Server-Sent
Events or WebSockets — long-poll is what the shape needs).

## Capabilities

None. The last slice of the seam over HTTP. Behaviour a caller sees
when they type `commit` and wait is unchanged. `skip_specs`.

## Impact

- **HTTP**: `http/app.py` — `GET /wait/turn` and `GET /wait/commit`.
  Both are read-only and use `held(read=True)` for the condition
  check.
- **CLI**: `cli/backend.py` — `HttpSession.waitForTurn` and
  `waitForPlayerCommit` implemented; the "step 5" `NotImplementedError`
  removed.
- **Tests**: `test_http_api.py` gains wait-endpoint coverage;
  `test_wait_over_http.py` runs the client-side loop end to end.
- **Docs**: `MODULE_DESCRIPTION.md`'s `http/app.py` and `backend.py`
  notes.
