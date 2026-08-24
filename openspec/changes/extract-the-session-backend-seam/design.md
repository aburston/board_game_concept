## Context

See `proposal.md` — Why, and `put-a-rest-api-under-the-cli` for the staircase
this is step 0 of. What shapes the seam is exactly where the REPLs reach into
the game today.

Three reach patterns, from the code:

```
   scalar state   data.getOutcome() / getTurnNumber() / getNewGame() /
                  getUnprocessedMoves() / getRejected() / getDropped() /
                  isEliminated(n)                         — plain values already
   actions        games.perform(data, cmd) · clientSave() · serverSave() ·
                  resolveWhenReady() · waitForTurn() · waitForPlayerCommit()
   view building  show.py and complete.py BOTH call views.*(data.getBoard(),
                  data.getPlayers()) themselves, then render / filter
```

The scalar state is already data. The actions are already a small set. The one
tangle is view building: `show.py` and `complete.py` each hold a board and call
`views.*` on it. That is the part an HTTP client cannot do — it has no board.

## Goals / Non-Goals

**Goals:**
- One interface the REPLs talk to; one implementation behind it that is today's
  in-process stack.
- The interface sits at an altitude the future HTTP implementation can meet: it
  returns *view data*, not board objects.
- A pure refactor — no test edited, the suite (real binaries included) green.

**Non-Goals:**
- The HTTP implementation, SQLite, any endpoint. Later treads.
- Any change to what `views.py`, `render.py`, `parser.py`, `roles.py` do.
- Any behaviour change whatsoever.

## Decisions

### 1. The seam is consumer-side, above the repository port

It lives in `cli/`, because it is what the *presentation* talks to. It is not
the repository port: the port is storage (`read_board`, `write_units`), and an
HTTP client implements none of that — it implements "post my command, get my
view", the use-case level. So the seam is above the port, and the port is
untouched.

### 2. The interface returns view data, not board objects

This is the decision that makes the seam stable. `show.py` and `complete.py`
stop holding a board and calling `views.*`; they ask the session for the view
data `views.*` produces, and render or filter it. `views.py` and `render.py` do
not change — only their *caller* moves, from the REPLs into the session.

```
   before   show/complete → views.*(getBoard(), getPlayers()) → render/filter
   after    show/complete → session.view(subject)             → render/filter
                                     └─ LocalSession calls views.* internally
```

The interface, in the surface the REPLs actually use:

```
   open()                        load/reload; raises the game-data errors the
                                 session loop already turns into an exit
   view(subject) -> data|None    views.* output for board/units/types/players/
                                 pending; None when the subject needs a board
                                 and there is none (drives the NO_BOARD message)
   names_for_completion()        the units/types data completion filters
   outcome() turn_number()       scalar reads, as today
   is_setup() set_setup(bool)    was new_game / setNewGame (the server flips it)
   unprocessed_moves()
   rejected() dropped() is_eliminated(n)
   perform(command)              games.perform; raises GameError as now
   commit() -> bool              what this role's `commit` does (Decision 4)
   resolve_pending() -> bool|None the server's unattended resolve
   wait_for_turn() wait_for_all_commits()
```

### 3. `LocalSession` is today's calls, relocated

The one implementation wraps a `Game`, `service.games`, and the turn functions —
the exact calls the REPLs make now, moved behind the interface. `open()` wraps
`Game.load` with the error handling `cli/session.py:load_game` has today.
`view(subject)` holds the board/players and calls `views.*` — the code lifted
verbatim out of `show.py:_view`. Nothing new is computed; it is the same work at
a different address.

### 4. `commit()` maps by identity; `resolve_pending()` is the server's loop

The user types `commit` in every role, but it means different things, and the
difference is identity, which the session knows:

```
   a player's commit   → clientSave()   (publish orders, wait to be woken)
   the admin's commit  → serverSave()   (end setup; no barrier)
   the server's loop   → resolve_pending() → resolveWhenReady()  (not a command)
```

`commit()` covers the first two by identity. `resolve_pending()` is separate
because it is not a typed command — it is what the unattended loop does when
woken. The observer calls neither.

### 5. One provisional leak, named: the server's raw turn-log

`bgcserver` logs each turn as `print_board(getBoard())` and
`serialise_units(getBoard())` — the latter a storage-format YAML dump.
`SPEC_COVERAGE.md` already lists that raw dump under "Left to a follow-up". To
keep this change a pure refactor, its output must not change, so the session
exposes a `board()` accessor used *only* by that turn-log, and only by the
server. It is the one thing not yet at view-data altitude. It is flagged rather
than cleaned, because forcing it through the seam now would change the logged
output and break the no-test-edited property; the turn-log is reconsidered when
the server becomes the API host, where it is a server-side concern anyway.

### 6. What does not move

`parser`, `grammar`, `roles`, `views`, `render`, and the mechanics of
`cli/session.py` (reading a line, refusing a command, reporting an error) stay
exactly as they are. `roles.py` still gates which commands a role may run, so
the session offers the union of operations and does not itself enforce role —
the same division as today.

## Risks / Trade-offs

- **The interface is a union of role operations** → a role could call one it
  should not (an observer calling `commit`). That is prevented where it is
  prevented today — by `roles.py` refusing the command before it reaches the
  session — not by the interface. Noted so the seam is not mistaken for the
  authority.

- **The `board()` accessor is a leak the HTTP implementation cannot meet** →
  scoped to the server's raw turn-log only (Decision 5), which is a known
  loose end and a server-side concern by the time HTTP arrives. It does not
  touch the player or observer paths, which are the ones the HTTP client must
  satisfy.

- **A refactor this broad could drift behaviour subtly** → the guard is that no
  test is edited. The CLI surface suites and the 542-line integration suite
  drive the real binaries; if the seam changed any prompt, table, refusal or
  wait, they fail. Green with zero edits is the definition of done.

## Migration Plan

Within this change:

1. Define the interface and `LocalSession` beside the roles; nothing uses it.
2. Move `show.py`'s view building into `LocalSession.view`, and have `show.py`
   and `complete.py` call the session for view data. `views.py`/`render.py`
   unchanged.
3. Rewrite `bgcclient`, `bgcobserver`, then `bgcserver` to construct and use a
   session. Do the observer first — it is read-only and the smallest — then the
   client, then the server with its two commit meanings and its turn-log.
4. Run the whole suite. Green with nothing edited is the exit condition.

No later tread starts here.

## Open Questions

1. **When the server's raw turn-log is cleaned up** (Decision 5's leak). Not
   this change; it belongs with making the server the API host, where the log
   becomes server-side output through the same view/render path as everything
   else. Recorded so it is not forgotten.
