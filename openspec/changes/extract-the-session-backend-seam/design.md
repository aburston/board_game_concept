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

### 2. A facade seam, not a view-data seam — because the tests pin the view layer

The original intent was for the seam to return *view data*, so `show.py` and
`complete.py` would stop holding a board. Reading the tests killed that for step
0: `test_completion.py` constructs `GameNames(<a Game>, number)` and
`test_cli_views.py` calls `views.units_view(<Game>.getBoard())`. Both `views.py`
and `complete.GameNames` are pinned by direct unit tests to operate on board and
player objects. Moving them to view data means editing those tests, which is the
one thing this change forbids.

So step 0 is a **facade seam**. The roles hold a `Session` instead of a `Game`
and route their actions and lifecycle through it; but view building (`views.py`)
and completion (`GameNames`) stay exactly where and how they are, reached through
the session as passthrough reads:

```
   actions / lifecycle / state   go THROUGH the seam
      perform · commit · resolve_pending · wait_* · the scalar reads

   view objects                  PASS THROUGH the seam, unchanged callers
      getBoard() getPlayers() getEliminated()  ← show.py & GameNames still
                                                  call views.* on these
```

The view-object accessors are the honestly-remaining coupling. They are what the
HTTP step replaces with view data, because that is when `views.py` moves
server-side (it becomes what `GET /view` returns) and completion is reworked to
run off the fetched view. Purifying them now would either edit the tests or move
`views.py` prematurely; deferring them keeps step 0 pure and puts the work where
it belongs.

The interface, in the surface the REPLs actually use:

```
   load()                         delegate Game.load; the session loop's
                                  load_game keeps turning its error into an exit
   perform(command)               games.perform on the wrapped game; raises
                                  GameError as now
   commit() -> bool               what this role's `commit` does (Decision 4)
   resolve_pending() -> bool|None the server's unattended resolve
   waitForTurn() waitForPlayerCommit()   Game's names; the roles' existing
                                         calls are untouched by them
   getOutcome() getTurnNumber() getNewGame() setNewGame(v)
   getUnprocessedMoves() getRejected() getDropped() isEliminated(n)
   getBoard() getPlayers() getEliminated()   ← passthrough, for show/completion;
                                               local-only, refined at the HTTP step
```

The read methods keep their `Game` names so `show.py`, `complete.py` and
`cli/session.py` do not change — the session presents the same surface those
callers already use. Only the roles change, and only where they constructed a
`Game` or called `games.perform`.

### 3. `LocalSession` is today's calls, relocated

The one implementation wraps a `Game`, `service.games`, and the turn functions.
`load()` delegates `Game.load` (so `cli/session.py:load_game` keeps its error
handling unchanged); `perform` calls `games.perform` on the wrapped game;
`commit` maps by identity (Decision 4); the reads delegate. Nothing new is
computed; it is the same work behind one object.

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

### 5. The passthrough reads are local-only, and named as such

`getBoard()`, `getPlayers()` and `getEliminated()` cross the seam so that
`show.py` and `complete.GameNames` — unchanged, and pinned by their tests to
board objects — keep working, and so that `bgcserver`'s raw turn-log
(`print_board(getBoard())`, `serialise_units(getBoard())`, the latter already
listed in `SPEC_COVERAGE.md` under "Left to a follow-up") keeps its output
byte-for-byte. These are the accessors the HTTP session cannot provide, and the
HTTP step is where they go: `views.py` moves server-side, `show` renders fetched
view data, and completion runs off it. Naming them local-only here is the honest
statement that the seam is not yet at view-data altitude for reads — only for
actions, lifecycle and state.

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

1. Define the `Session` interface and `LocalSession` beside the roles; nothing
   uses them.
2. Rewrite the roles to construct and use a session — observer first (read-only,
   smallest), then client, then server with its two commit meanings and its
   turn-log. `show.py`, `complete.py`, `views.py`, `render.py` and
   `cli/session.py` are untouched: the session presents the `Game` read surface
   they already use.
3. Run the whole suite. Green with nothing edited is the exit condition.

No later tread starts here.

## Open Questions

1. **When the server's raw turn-log is cleaned up** (Decision 5's leak). Not
   this change; it belongs with making the server the API host, where the log
   becomes server-side output through the same view/render path as everything
   else. Recorded so it is not forgotten.
