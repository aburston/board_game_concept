# Three-Tier Architecture: Options

Exploration, not a decision. This maps what the code looks like today, names the
couplings that have to be cut before a tier split is even possible, and lays out
the options at each tier with the trade-offs. Nothing here has been implemented.

The README already states the intent ("web service - [TODO]": roles in the API
based on login, Flask, "moving to sqlite may be a thought via a common data
class"). This document works out what that actually costs.

---

## 1. Where the code is today

```
  server.py            client.py           observer.py        <- role-specific REPLs
  (player 0, admin)    (one player)        (read-only)           command parsing,
        \                   |                   /                authz, formatting
         \                  |                  /
          +----------> GameData.py <----------+               <- storage + transport
                        load() / clientSave()                     + turn barrier
                        serverSave() / waitForPlayerCommit()
                             |
                    BoardGameConcept.py                       <- domain + rendering
                    Board / UnitType / Player / Empty             + serialisation
                             |
                games/_<gameno>/data/*.yaml                   <- store AND message bus
                games/_<gameno>/players/*.yaml
```

It is closer to one-and-a-half tiers than three. There is a domain model, but
every other concern - presentation, persistence, transport, synchronisation,
authorisation - is spread across all three files rather than layered.

The filesystem is doing double duty: it is both the database and the message
queue between processes. `players/<n>_units.yaml` is an outbox, `players/commit_<n>`
is a semaphore, and the absence of a file is how the client knows its turn was
resolved.

---

## 2. The seams that have to be cut first

These are prerequisites, not options. None of the tier choices below are
reachable while they hold.

**2.1 The domain model does its own I/O.**
`Board.print()` (`BoardGameConcept.py:494`) writes a grid to stdout.
`Board.listUnits()` (`:527`) returns a hand-built YAML *string*, not data.
`UnitType.dump()` (`:364`) returns a YAML fragment. There are 28 `print()` calls
in the engine, most of them combat narration inside `preCommit`/`resolveContest`/
`commit`. An API tier cannot reuse this without capturing stdout and re-parsing
YAML it just built. The engine needs to return objects and emit events; rendering
belongs above it.

**2.2 `GameData` is three things at once.**
Repository (`load`/`clientSave`/`serverSave`), transport (order files), and
coordinator (`waitForPlayerCommit`, `GameData.py:470`, a 10-second `os.listdir`
poll). Splitting storage from transport is the whole point of the exercise, and
they are currently the same code path.

**2.3 Library code exits the process.**
`GameData.load()` calls `sys.exit(1)` in four places (`:102`, `:110`, `:174`,
`:273`) on malformed YAML or an unknown player. In a web process, one bad request
takes down the worker. These have to become raised domain errors that a caller
can turn into a 400 or a 404.

**2.4 The data layer reads the process CWD.**
`base_path = os.getcwd() + "/games/_" + gameno` (`GameData.py:60`). The current
working directory is part of the storage contract, which is why the integration
tests have to launch subprocesses with a specific `cwd`. Storage location has to
become configuration.

**2.5 Business rules live in CLI branches.**
"only the game admin (player 0) can set board size" (`server.py:195`), "can't
resize an existing board" (`:198`), "can't add players to an existing game"
(`:229`, `:249`), and the setup-versus-play gate in the client are all enforced
by `if` statements inside the REPL. An HTTP API would have to reimplement every
one of them, and the two copies would drift. They belong in a service layer that
both the CLI and the API call.

**2.6 Identity is a stringly-typed player number, inconsistently.**
`client.py:49` takes `player_number` straight from `argv` as a string. `add
player 1` at the server prompt stores the token `'1'` (`server.py:231`), while
`tests/player_1.yaml` carries the integer `1`. Unit stats are stored as quoted
strings and re-cast with `int()` on every load. There is no account, no session,
no credential - the player number *is* the authentication. Everything the README
wants from "roles in the API based on login" starts here.

Two stale copies of the engine also sit outside the package -
`src/BoardGameConcept.py` and `src/GameData.py`, left over from the restructure
in `7a26b26`. Nothing imports them and they have already diverged from the
package versions. They should go before anything else touches this code.

---

## 3. Target shape

```
   web UI            CLI clients          bots / scripts     <- presentation
      \                   |                    /
       +--------- HTTP + JSON (one contract) -+
                          |
                   transport (routes, auth, serialisation)   <- API tier
                          |
                   service layer (use cases, authz, phases)
                          |
                   domain engine (pure, no I/O, events out)
                          |
                   repository port
                    /            \
              YAML repo        SQL repo                      <- data tier
```

The engine stays pure and stays where the game rules live. Everything that is
currently ambient - identity, storage location, turn synchronisation, output
formatting - becomes an explicit dependency passed in.

---

## 4. Tier 1 - the data layer

### Options

| | Approach | Gains | Costs |
|---|---|---|---|
| **D1** | Keep YAML, add a `GameRepository` interface over it | Cheapest; `game-persistence` spec stays green unchanged; no new dependency | No transactions, no locking, no queries; the concurrency problem is untouched |
| **D2** | SQLite behind the same interface | ACID; the commit barrier becomes a transaction; single file, no server to run; the README's stated direction | Schema + migrations; one writer at a time (fine at this scale) |
| **D3** | PostgreSQL, same schema | Real concurrent writers, multi-process, network access | An operational dependency for a game that currently needs none |
| **D4** | Event-sourced turn log (orders as events, board state as a fold or snapshot) | Fits the domain unusually well - the game *is* a sequence of simultaneous-commit turns; free replay, free observer history, visibility becomes derived data | Most machinery; snapshotting needed; harder to debug by hand |

**Recommendation: D2, with one idea borrowed from D4.** SQLite via SQLAlchemy
behind a `GameRepository` port, plus a first-class `turn_events` table that
records what happened during resolution. That gives replay and a real combat log
without committing to full event sourcing. Keep a `YamlGameRepository`
implementation alongside it during the transition so the existing file-format
specs and integration tests keep passing while the SQL path is built. D3 is the
same schema later if it is ever needed; D1 alone does not solve anything that
matters.

### Aggregate boundary

Two ways to use a relational store here:

- **ORM-as-domain** - map `Board`/`UnitType` onto tables directly. Rejected: it
  would put persistence concerns back inside the engine, which is precisely the
  coupling being removed.
- **Load/resolve/save the whole game** - the repository reads a game snapshot,
  builds domain objects, the engine resolves the turn in memory, the repository
  writes the result back in one transaction. This is what `GameData` already
  does, so it is the smaller change, and it keeps the engine unit-testable with
  no database at all.

Take the second. **The game is the aggregate root**, and one row lock per game
serialises turn resolution.

### Schema, mapped from today's files

| Today | Becomes |
|---|---|
| `data/board.yaml` | `games` row (size_x, size_y, status, turn_no) |
| `players/<n>.yaml` | `memberships` + `unit_types` |
| `data/units.yaml` | `units` |
| `players/<n>_units.yaml` | `orders` for the open turn |
| `players/commit_<n>` | `commits(game_id, turn_no, player_number)` |
| `players/<n>_rejected.yaml` | `rejections(game_id, turn_no, ...)` |
| `players/<n>_units_seen.yaml` | `sightings(game_id, turn_no, viewer, unit_id)` |
| combat narration on stdout | `turn_events(game_id, turn_no, seq, kind, payload)` |

Every file has a home, and the mapping is close enough to one-to-one that the
persistence spec can be rewritten storage-agnostically without changing what it
requires. Typed columns also settle the string/int drift from §2.6 by force.

---

## 5. Tier 2 - the API layer

### Framework

| | Approach | Notes |
|---|---|---|
| **A1** | Flask + REST | The README's stated plan. Simple, familiar, no typing story - request validation and response shaping are hand-rolled |
| **A2** | FastAPI + Pydantic | Typed request/response models, generated OpenAPI, async available. The Pydantic models *are* the "dedicated objects for data returned from the DB" the README TODO already asks for |
| **A3** | GraphQL | Over-fit. The domain has a small, fixed set of views and one real mutation per turn |

**Recommendation: A2.** The generated schema matters more than usual here,
because three different presentation clients (web, CLI, observer) have to agree
on one contract, and a machine-checked one beats a documented one.

Structure it in two pieces regardless of framework: a **service layer** holding
one function per use case (`create_game`, `add_player`, `define_type`,
`deploy_unit`, `order_move`, `commit`, `view_for`), and a thin **transport**
layer that does nothing but bind HTTP to those functions. The rules from §2.5
move into the service layer, where the CLI can call them too.

### Cross-cutting decisions

**Who resolves the turn?**

- *(a)* Keep a daemon polling the store - closest to today, but keeps the
  polling loop and needs a second process running.
- *(b)* **Resolve inline in whichever commit request completes the barrier.** In
  one transaction: lock the game row, record the commit, check whether every
  player has committed, and if so resolve and persist. No daemon, no polling, and
  a whole class of races disappears.
- *(c)* Background worker + queue - needed only if turns become long-running or
  timed.

Take (b). Keep (a) in reserve for timed turns, where a turn must resolve on a
clock rather than on the last commit.

**How does a client learn the turn resolved?** Today `client.py:76` sleeps 5
seconds and reloads; the server sleeps 10. Version every state response with a
turn number, then: polling with `If-None-Match` (simplest, matches today's
semantics), long-poll `GET /games/{id}/turns/{n}` blocking until turn *n* is
resolved, or SSE/WebSocket push. Long-poll first, SSE later if the UI wants it.

**Identity and authorisation.** Player number becomes account + membership +
role (`admin` / `player` / `observer`), with a bearer token. Authorisation is
mostly *visibility filtering*, which the engine already implements -
`listUnits(player)` versus `listUnits()` is exactly the observer/player split.
That makes the three CLI roles collapse into one API with one role check per
endpoint, which is what the README describes.

**Concurrency.** Everything above rests on the game-row lock. Today two writes to
`players/<n>_units.yaml` simply race, and nothing notices.

### Endpoint sketch

```
POST   /games                       create (admin)
POST   /games/{id}/players          add player          [setup only]
POST   /games/{id}/types            define unit type    [setup only]
POST   /games/{id}/units            deploy a unit       [setup only]
POST   /games/{id}/orders           order a move        [play only]
POST   /games/{id}/commit           commit; resolves if the barrier is met
GET    /games/{id}/view             role-filtered board, units, types, rejections, turn_no
GET    /games/{id}/turns/{n}        long-poll: returns when turn n is resolved
GET    /games/{id}/turns/{n}/events combat narration for a resolved turn
```

---

## 6. Tier 3 - the presentation layer

| | Approach | Notes |
|---|---|---|
| **P1** | Server-rendered HTML (Jinja + htmx) | No build step, no JS toolchain. A board is a grid of cells and a turn is a page refresh - htmx polling maps onto the turn model almost exactly. Fastest route to the user stories in `design.md` |
| **P2** | SPA (React/Svelte) against the JSON API | Better for drag-and-drop deployment and animating combat rounds. Costs a toolchain and a second codebase |
| **P3** | Port the existing CLIs to be API clients | The real proof the API is complete, and it keeps `tests/test_server_client_integration.py` meaningful instead of obsolete |

**Recommendation: P3 then P1.** Porting the CLIs first is the cheapest possible
test that the API covers every use case - if a CLI command cannot be expressed
against the API, the API is wrong. P1 then delivers the `design.md` stories.
Because both go through the same JSON contract, P2 stays available later as a
swap of the top tier only.

---

## 7. A sequence that keeps the tests green

0. **Delete the stale duplicates** `src/BoardGameConcept.py` and
   `src/GameData.py`. Nothing imports them; they have already drifted.
1. **Purify the engine.** Move rendering out of `Board`/`UnitType` into a
   separate renderer; replace `listUnits`/`dump` string-building with plain data
   plus a serialiser; replace combat `print`s with an event list the caller
   renders. No behaviour change, and the existing unit tests largely carry over.
2. **Extract the service layer** from the CLI branches - one function per
   command in the specs. The three REPLs become thin. `sys.exit` disappears from
   library code in favour of raised errors.
3. **Introduce the repository port** with two implementations: `YamlGameRepository`
   (today's format, so `game-persistence` stays green) and `SqliteGameRepository`.
   Select by configuration; run the suite against both.
4. **Put HTTP over the service layer**, and port the CLIs to it (P3).
5. **Build the web UI** (P1).
6. **Retire the file transport** once nothing depends on it, and rewrite the
   affected specs.

Steps 1-3 are worth doing on their own merits even if the web tier never
happens. Nothing before step 4 requires choosing a framework, and nothing before
step 3 requires choosing a database - which means the two decisions with the
longest reach can be deferred until the code is in a shape to make them cheaply.

---

## 8. What this does to the specs

The OpenSpec capabilities are written against behaviour, so most survive intact.
The ones that move:

- **`game-persistence`** - currently specifies file paths and YAML shapes as
  requirements. Needs splitting into *what must be durable* (storage-agnostic)
  and *how a given backend stores it*.
- **`turn-commit`** - the commit barrier stops being "count `_units.yaml` files"
  and becomes a transactional check. The requirement itself is unchanged; its
  scenarios are not.
- **`player-client`, `game-server`, `game-observer`** - the command surfaces stay,
  but each gains an HTTP binding, and the three roles converge on one API.
- **New capabilities needed** - `identity-and-roles` (accounts, membership,
  authorisation) and probably `game-api` (the contract itself).

`combat-resolution`, `unit-movement`, `unit-types`, `board-model` and
`visibility` are untouched by any of this. That is a good sign: the engine is the
part worth keeping.

---

## 9. Open questions

1. **How much concurrency is real?** One game at a time on one box, or many
   games and many players? SQLite versus Postgres turns entirely on this, and
   nothing else does.
2. **Do turns stay untimed?** An untimed turn resolves on the last commit
   (option (b) above) and needs no daemon. A timed turn needs a scheduler, which
   is a different shape.
3. **Are the CLIs kept?** If they are ported to the API they stay the best
   integration test. If they are retired, step 4 gets smaller but the test suite
   needs rebuilding against HTTP.
4. **Do accounts persist across games?** A single account playing many games is a
   different membership model from an account being created per game.
5. **Is game history a feature?** Replay and a visible combat log are nearly free
   with a `turn_events` table, and expensive to retrofit later.
