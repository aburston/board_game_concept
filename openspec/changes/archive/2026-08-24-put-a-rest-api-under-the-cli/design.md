## Context

See `proposal.md` — Why. What shapes the plan is how much of it is already
standing.

Read through the supersession lens, the layer split and the five changes after it
built an API without a transport:

```
   domain/            pure engine, no I/O
   service/games.py   one function per use case (perform)
   service/commands   the command vocabulary          → REQUEST BODIES
   cli/views.py       plain data per subject           → GET RESPONSES
   cli/roles.py       role → allowed commands          → ENDPOINT AUTHZ
   service/identity   0 / 1..999 / 1000                → who may do what
   storage/repository the port                          → swap for SQLite
   resolve_when_ready atomic check-and-resolve          → POST /commit
   storage/lock       held()                            → a transaction
   drafts             uncommitted state durable         → a thin client
```

Two things are still filesystem-shaped and must be cut before the swap. The
repository is really two ports in one coat: storage (`read_*`/`write_*`) and
transport (`wake`/`waiter`). And the write side leaks the YAML format —
`write_units(text)`, `write_view(n, text)`, `write_orders(n, text)` take
serialised strings, asymmetric with the read side, which returns data.

## Goals / Non-Goals

**Goals:**
- The REST API is the sole path to game logic; one server hosts all games.
- The CLIs are preserved exactly as a user experiences them, as HTTP clients.
- SQLite with a real schema, behind the existing port.
- A turn resolves inline in the commit that completes the barrier.
- Every step leaves the suite — and the real CLI binaries — green.

**Non-Goals:**
- Authentication now. Deferred, but the identity seam is shaped for it.
- A web UI; Postgres; timed turns. Each is a later change or an escape hatch.
- Changing what the engine computes. `test_determinism.py` never moves.

## Decisions

### 1. The session-backend seam

The CLIs touch the game through a narrow, bounded set of operations — the whole
surface between the REPLs and the game is:

```
   read my view / board / players / rejections / dropped / outcome / turn
   perform a command (add type, deploy, move, set board, add player, load ...)
   commit
   wait until the turn resolves
   ask whether my orders are still pending
```

Everything else in `cli/` — parsing, the role table, rendering, the session
loop, completion — is transport-agnostic already. So the seam is an interface
with that surface and two implementations:

```
   REPL ─▶ session backend ─┬─ local  = today's Game + repository (in-process)
                            └─ http   = talks to the REST API
```

The CLIs are rewritten against the interface with the local implementation
first — a pure refactor, fully covered by the existing suite — and the HTTP
implementation is flipped in later. This is the strangler seam that keeps the
CLI working at every step.

*Why this is the seam and not the repository port*: the port is about storage
(read a board, write units). An HTTP client does not implement "write units" —
that would put the whole board on the wire to a player. It implements "post my
command, get my view", which is the use-case level. The seam is above the port.

### 2. Drafts already made the client thin

To be an HTTP client, `bgcclient` must not hold a live `Game` it mutates — it
must send each edit and fetch its view. Drafting already arranged exactly that:

```
   add unit   → games.perform records it to the durable DRAFT (server-side)
   show units → the view, with the draft replayed in
```

So the HTTP client is stateless: `add unit` is `POST /orders`, `show units` is
`GET /view`, `commit` is `POST /commit`. The `Game` behind the REPL evaporates
into HTTP calls. The change we made so a crashed client would not lose its army
is the change that makes the client portable.

### 3. SQLite with a real schema, behind the port

The port stays; `SqliteGameRepository` joins `YamlGameRepository` under it. Real
tables, not YAML blobs in columns — the reason to choose SQLite over "YAML with
a better lock" is the typed columns and the queries, and blobs throw both away.

The game is the aggregate: load a snapshot, resolve in memory, write it back in
one transaction — which is what `Game.load` + `resolve` + the writes already do.
The schema maps the files nearly one-to-one:

```
   games(id, size_x, size_y, turn_no, outcome, status)
   memberships(game_id, player_number)                 -- registered players 1..999
   unit_types(game_id, player_number, name, symbol, attack, health, energy)
   units(game_id, owner, name, type_name, symbol,
         attack, health, energy, type_attack, type_health, type_energy,
         x, y, state, direction, destroyed, on_board)  -- the authoritative board
   orders(game_id, player_number, turn_no, ...)         -- published, for the open turn
   commits(game_id, player_number, turn_no)             -- the barrier record
   drafts(game_id, player_number, turn_no, commands)    -- uncommitted, commands as JSON
   rejections(game_id, player_number, turn_no, unit, type, x, y, reason)
   sightings(game_id, turn_no, viewer, unit)            -- contact: who has seen what
   turn_events(game_id, turn_no, seq, kind, payload)    -- the combat log, nearly free
```

Two things the schema buys that the files could not:

- **A view stops being a materialised file and becomes a query.** Today
  `write_view` writes each player's view because the filesystem cannot do a
  visibility join. SQLite can: a player's view is `units` joined against
  `sightings` for that viewer. `write_view` disappears, and with it the whole
  class of "the view drifted from the board" concern.
- **The combat log is a table insert.** `board.commit()` already returns the
  events; capturing them into `turn_events` is nearly free and gives replay and
  a visible combat record that are expensive to retrofit later.

### 4. `held()` becomes a transaction

The lock built by `serialise-access-to-a-game` was shaped for this: a database
backend implements the same two words as a transaction.

```
   YamlGameRepository.held()   → advisory flock on .lock
   SqliteGameRepository.held() → BEGIN IMMEDIATE (write) / deferred (read), WAL
```

`resolve_when_ready` still reads `with repository.held():` and does not change.
That is what the port existed for.

### 5. Purify the port before the swap

Two contained changes first, each green on the YAML backend alone:

- **De-text-ify the write side.** `write_units`/`write_view`/`write_orders` take
  data, symmetric with the read side; each backend serialises its own way. The
  YAML backend keeps writing YAML; the SQLite backend maps to rows.
- **Split transport off.** `wake`/`waiter` leave the port — they are the FIFO
  bus, which becomes long-poll and is not storage at all.

### 6. Resolution: option (b), and what becomes of the server

`POST /commit` records the orders and calls `resolve_when_ready`. The commit
that completes the barrier resolves the turn, in its own request, server-side:

```
   POST /commit
     record orders (publish)
     resolve_when_ready ─┬─ None     → 202  "recorded, waiting for others"
                         └─ resolved → 200  "you completed the turn, here it is"
```

The lock elects the resolver for free: `barrier_met` flips once, and concurrent
last-commits serialise on the hold so exactly one resolves and the rest get 202.
The unattended poll loop (`wait_for_all_commits` + the server cycle) is retired.
`bgcserver` — the process hosting the API — is still what resolves, triggered by
the request instead of a poll, so from a user's point of view "the server
resolves turns" is unchanged.

### 7. The signal: long-poll is `notify.py` over HTTP

A player who committed earlier and got 202 learns the turn resolved the same way
they do today, in a different pipe:

```
   notify.py:  block on a FIFO until signalled, timeout as backstop
   HTTP:       GET /games/{id}/turns/{n}  blocks until turn n is published,
               timeout as backstop
```

Same shape — a hint that is always re-checked against the real state — so the
`waitForTurn` half of the session backend maps onto it directly.

### 8. One server, all games — and what a user sees

The filesystem let every process rendezvous through a directory with no address.
One shared server needs one host, which splits `bgcserver`'s two jobs:

```
   bgcserver          host ALL games (the one server)      ← new mode
   bgcserver -g 1     admin console for game 1, an HTTP client
   bgcclient 1 2      player client, HTTP, localhost by default
   bgcobserver 1      observer, HTTP
```

The single user-visible change: the host is started once (`bgcserver`, no `-g`),
not one server per game. After that, `bgcserver -g 1` and `bgcclient 1 2` behave
as today. It is arguably simpler; it is still a change, and it is the
unavoidable cost of "one server for all games".

### 9. Auth deferred, but the seam is shaped for it

`player_number` stays the whole of identity. The session backend carries an
identity that is a bare number now and becomes account-plus-membership later, so
a token slots into the same seam without re-cutting it. Until then the server is
trusted to be reached only from the same machine — a networked server without
auth is unsafe, and the plan says so.

### 10. Visibility is strengthened, not merely preserved

Today a `bgcclient` process could read `data/units.yaml`; it is trusted not to.
Over HTTP it is on the far side of the boundary and the server only ever sends
its view. The concern behind divergence 17 — hidden information hidden only when
drawn — closes completely, because the hidden information is never on the wire.

## Risks / Trade-offs

- **SQLite has one writer per database** → not "one row lock per game" as the
  old doc hoped; a write transaction is database-wide. One `.db` for all games
  means resolving game 1 briefly blocks a commit to game 2. At this scale —
  one box, milliseconds per resolution, WAL keeping readers unblocked — this is
  fine. It is the ceiling, and Postgres behind the same port is the escape hatch
  if many busy games ever contend. Take SQLite with eyes open.

- **The last committer pays the resolution latency inline** → milliseconds on a
  board of tens of squares. A background worker (option (c)) is the answer only
  if turns ever become expensive.

- **Auth is deferred, so the server is localhost-only until it lands** → stated
  in the open, not discovered. The seam is shaped so adding it does not re-cut
  identity.

- **A big-bang would throw away the integration suite during the riskiest work**
  → mitigated by the strangler: the seam (Decision 1) means the CLI runs on the
  local backend until the HTTP one is proven, and the 542-line suite drives the
  real binaries at every step.

- **Two resolution paths could coexist mid-migration** (daemon + inline) →
  harmless, because `resolve_when_ready` makes them mutually safe; but the
  migration retires the daemon promptly to avoid reasoning about both.

## Migration Plan

Each step is its own change, with its own delta specs and tasks. The suite — and
the real CLI binaries — stay green at every tread.

```
   0.  extract the session-backend seam        pure refactor, local impl only
   0b. purify the port                         de-text-ify writes; notify leaves
   1.  SqliteGameRepository (schema)           held() → transaction; run the
                                               suite against both backends,
                                               SQLite the default
   2.  GET /view                               the read side over HTTP
   3.  POST commands                           the write side; drafts make it thin
   4.  POST /commit + (b)                      bgcserver (no -g) becomes the host
   5.  long-poll = waitForTurn                 retire notify.py
   6.  flip the clients to the HTTP backend    bgcserver -g = admin client
   7.  retire the filesystem transport + poll loop; keep YAML as export/test only
```

Steps 0, 0b and 1 are worth doing on their own merits even if the HTTP tier
stalled: they are a cleaner port and a real store. Nothing before step 2 chooses
a web framework; nothing before step 1 is irreversible.

## Open Questions

1. **`turn_events` now or later.** The schema makes the combat log nearly free,
   but nothing consumes it yet (no replay, no web UI). Capture it from step 1
   so the history exists from the first SQLite turn, or add the table when
   something reads it. Leaning: capture from the start — it is cheap now and
   un-retrofittable later.
2. **Host discovery.** `bgcclient 1 2` needs an address where it needed a
   directory. Localhost on a default port covers the preserved-CLI case; a
   `--host` flag covers remote. The exact default port and config surface is a
   step-6 detail, not a plan-level decision.
