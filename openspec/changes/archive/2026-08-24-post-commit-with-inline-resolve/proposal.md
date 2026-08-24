## Why

`put-a-rest-api-under-the-cli` names step 4 as the commit endpoint, and
this is where option (b) — "commit resolves the turn inline" — lands
for real. Two steps set it up: step 3 put `perform` on the wire, and
step 2 put the read side on the wire. What is left before the client is
end to end over HTTP is `commit`, and the barrier that goes with it.

Option (b) is what the earlier exploration crystallised: the last commit
that meets the barrier resolves the turn itself, right there in the
request. No unattended server is required to be running between commits;
the resolver is whichever player closes the barrier. For a REST tier
that is the only shape that makes sense — a request coming in with the
last commit that would let the turn resolve should not wait for a
separate process to notice.

`bgcserver` running unattended is not gone. It still works for the
file-transport CLI flow and for a person who wants a game with a
resolver dedicated to it. What changes is that it is no longer
*required*.

## What Changes

- **`POST /games/<gameno>/players/<n>/commit`.** For a player: publish
  their orders, mark them committed, and — under the same hold — check
  the barrier and resolve if it is met (option (b)). For the
  administrator: run the setup resolution. The response is a small
  JSON: `{"resolved": bool, "turn_number": int, "outcome": ...|null,
  "waiting_on": [n, ...] | []}` so the client can decide whether to
  refresh or wait.

- **`HttpSession.commit`.** POSTs to the commit endpoint and returns
  what `LocalSession.commit` returns today (`True`/`False`). Caches
  invalidate on success. `commit`'s wait-for-turn semantics still live
  in the REPL loop; step 5 wires long-poll.

- **`HttpSession.resolve_pending`.** Reaches `/commit` too — for the
  admin server-loop use case the barrier-check-and-resolve endpoint
  is the same. Kept behind its own name so the two callers still read
  as what they are.

- **`HttpSession.setNewGame`.** POSTs a special-case command via the
  existing endpoint — `SetNewGame` command has never existed, so this
  is one new command node: `SetNewGame(new_game: bool)`, treated by
  the service layer as the setter it already is. Only the administrator
  ever calls it; step 3 refused it for lack of this piece.

- **The client's REPL still calls `waitForTurn` after `commit`.** For
  the local case that is what it always did. For the HTTP case that
  method is still `NotImplementedError('step 5')` until long-poll lands
  next. So this change lets a player commit and get their state back;
  waiting on the barrier for a turn *someone else's commit* resolves is
  step 5.

**Test edits are expected.** `test_http_api.py` gains commit coverage:
a two-player commit ends the turn, and one-player commit is 202-ish.
`test_client_over_http.py` gains `commit` end to end for a game where
the single player closing the barrier is the one committing —
one-player game, or two-player game where the other has already
committed via local storage.

Not in this change: long-poll (step 5), flipping the default so every
client is over HTTP (step 6), retiring the file transport (step 7),
retiring `bgcserver` as an unattended resolver (still available; the
umbrella keeps it as an admin CLI in later steps).

## Capabilities

None. Same shape as steps 2 and 3: another slice of the seam over HTTP.
Behaviour a caller sees when they type `commit` is unchanged.
`skip_specs`.

## Impact

- **HTTP**: `http/app.py` — `POST /commits`. Errors keep the mapping
  step 2 set up, with a 202 for "committed, waiting on others" and a
  200 for "resolved this turn".
- **CLI**: `cli/backend.py` — `HttpSession.commit`, `resolve_pending`,
  `setNewGame` implemented. Removes the "step 3"/"step 4"
  `NotImplementedError` on those three.
- **Service**: `service/commands.py` — new `SetNewGame(new_game)` node.
  `service/games.py` — its handler (calls `data.setNewGame(...)`).
- **Tests**: `test_http_api.py` gets commit endpoints coverage.
  `test_client_over_http.py` gets a commit end-to-end that resolves a
  turn.
- **Docs**: `MODULE_DESCRIPTION.md`'s `http/app.py` note — the commit
  endpoint lives beside the read and write endpoints.
