## Context

See `proposal.md` — Why, and `put-a-rest-api-under-the-cli` — step 1. What
shapes this change is a real schema, held-as-transaction, and a suite that
passes over both backends unchanged.

Step 0b left the port taking data, and split the FIFO bus off onto
`Notifier`. Both preconditions the SQLite backend needed. The signal has
not moved yet — the FIFO transport keeps working — so the SQLite backend
exposes `wake`/`waiter` too. `Game` still picks a `FifoNotifier` when it
finds them. Long-poll is step 5.

## Goals / Non-Goals

**Goals:**
- A second implementation of the port, over SQLite, that the whole suite
  passes against — nothing behind the port changes.
- Real tables, not YAML text in blob columns. The reason to choose SQLite
  is typed columns and queries; a blob column throws both away.
- `held()` is a transaction. `BEGIN IMMEDIATE` for a writer, `BEGIN
  DEFERRED` for a reader, WAL on so a reader does not block a writer.
- SQLite is the default. `bgcserver`, `bgcclient` and `bgcobserver` construct
  it when nothing overrides them.
- The YAML backend keeps working. A `--backend yaml` on each CLI, and every
  test that already knew the file bytes still runs against YAML.

**Non-Goals:**
- HTTP, long-poll, `read_view` becoming a computed value at the roles.
- The observer's `read_view` reading from `turn_events`. The table lands
  here; the reader lands later.
- Migrating an existing YAML game to SQLite. Games are cheap to create;
  fresh games under the new default is the migration.

## Decisions

### 1. One file per game, beside a `data` directory for the FIFOs

The layout stays the same shape a directory-per-game already had:

```
   games/_<gameno>/
     game.sqlite3            -- the whole game state
     data/                   -- keeps the FIFOs for signal(); step 5 removes it
     .lock                   -- unused on the SQLite backend; kept so that the
                                YAML backend and the SQLite backend leave the
                                same directory shape behind
```

An operator can `cp -r games/_1 games/_2` to clone a game; `rm -rf
games/_1` to delete one; `sqlite3 games/_1/game.sqlite3` to poke at it.
The directory has one file rather than a dozen; that is the visible
difference to the operator.

*Why not `games/<gameno>.sqlite3` and lose the directory*: because
`notify.py`'s FIFOs still live somewhere, and putting them beside the
sqlite file rather than in a directory that also holds it is a worse
layout. When step 5 retires the FIFOs, the `data/` directory can go with
them and the sqlite file rises to the top of the tree if that reads
better then.

### 2. The schema maps the files nearly one-to-one

```sql
CREATE TABLE games (
    id           INTEGER PRIMARY KEY CHECK (id = 1),  -- one game per file
    size_x       INTEGER,
    size_y       INTEGER,
    turn_no      INTEGER NOT NULL DEFAULT 0,
    outcome      TEXT
);

CREATE TABLE eliminated (               -- progress: `eliminated` is a list
    player_number INTEGER NOT NULL,     -- and lists are their own tables
    PRIMARY KEY (player_number)
);

CREATE TABLE memberships (              -- registered players 1..999
    player_number INTEGER PRIMARY KEY   -- (0 admin, 1000 observer are not
        CHECK (player_number BETWEEN 1 AND 999)  -- members - they are
);                                                       -- sessions, not seats)

CREATE TABLE unit_types (
    player_number INTEGER NOT NULL,
    name          TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    attack        INTEGER NOT NULL,
    health        INTEGER NOT NULL,
    energy        INTEGER NOT NULL,
    PRIMARY KEY (player_number, name)
);

CREATE TABLE units (                    -- the authoritative board
    id            INTEGER PRIMARY KEY,
    owner         INTEGER NOT NULL,
    name          TEXT NOT NULL,
    type_name     TEXT NOT NULL,
    symbol        TEXT NOT NULL,
    attack        INTEGER NOT NULL,
    health        INTEGER NOT NULL,
    energy        INTEGER NOT NULL,
    type_attack   INTEGER NOT NULL,
    type_health   INTEGER NOT NULL,
    type_energy   INTEGER NOT NULL,
    x             INTEGER NOT NULL,
    y             INTEGER NOT NULL,
    state         INTEGER NOT NULL,
    direction     INTEGER NOT NULL,
    destroyed     INTEGER NOT NULL,     -- SQLite has no boolean; 0/1
    on_board      INTEGER NOT NULL
);

CREATE TABLE orders (                   -- the units a player published for
    player_number INTEGER NOT NULL,     -- the open turn. Present rows mean
    turn_no       INTEGER NOT NULL,     -- "not yet consumed", so a client
    id            INTEGER NOT NULL,     -- waits by asking the row count
    -- ...same columns as units, less `id` which is an order index...
    owner INTEGER, name TEXT, type_name TEXT, symbol TEXT,
    attack INTEGER, health INTEGER, energy INTEGER,
    type_attack INTEGER, type_health INTEGER, type_energy INTEGER,
    x INTEGER, y INTEGER, state INTEGER, direction INTEGER,
    destroyed INTEGER, on_board INTEGER,
    PRIMARY KEY (player_number, id)
);

CREATE TABLE commits (                  -- the barrier record
    player_number INTEGER PRIMARY KEY,
    turn_no       INTEGER               -- NULL means "committed but not
                                        --  for a particular turn"
);

CREATE TABLE drafts (                   -- a session's uncommitted work
    player_number INTEGER PRIMARY KEY,
    turn_no       INTEGER NOT NULL,
    commands      TEXT NOT NULL         -- JSON, one command per element
);

CREATE TABLE rejections (
    player_number INTEGER NOT NULL,
    turn_no       INTEGER NOT NULL,
    unit          TEXT,
    type_name     TEXT,
    x             INTEGER,
    y             INTEGER,
    reason        TEXT
);

CREATE TABLE sightings (                -- who has seen what
    viewer        INTEGER NOT NULL,
    seen_unit_id  INTEGER NOT NULL REFERENCES units(id) ON DELETE CASCADE,
    PRIMARY KEY (viewer, seen_unit_id)
);

CREATE TABLE turn_events (              -- the combat log; nothing reads it
    turn_no       INTEGER NOT NULL,     -- yet, but board.commit() already
    seq           INTEGER NOT NULL,     -- returns the events
    kind          TEXT NOT NULL,
    payload       TEXT NOT NULL,        -- JSON
    PRIMARY KEY (turn_no, seq)
);
```

*Why one game per file*: because a game is the aggregate. Two games have
no rows in common, and one file per game keeps operator commands (copy,
back up, delete) the same shape they were.

*Why not a single database with `game_id` on every row*: because
`held()` is a per-game transaction, not a whole-server one. Two games
committing at once would serialise on one write lock, which is exactly
what the file-per-game layout avoids.

### 3. `held()` is `BEGIN IMMEDIATE` / `BEGIN DEFERRED`

```python
def held(self, read=False):
    if read:
        # a reader that later needs to write upgrades via a savepoint;
        # nested held() calls do not open a second transaction
        self._begin('DEFERRED')
    else:
        self._begin('IMMEDIATE')  # takes the write lock at once
    return _Transaction(self._connection, self._depth)
```

WAL is on so a reader does not block a writer. A `BEGIN IMMEDIATE` fails
with SQLITE_BUSY if another writer holds the lock; the port raises
`GameIsBusy` in that case, which is what the YAML backend raised for the
same condition. `resolve_when_ready`'s outer `held()` block does not
need to change: same two words, different plumbing.

Nested `held()` — a caller inside a `held()` that calls it again —
increments a depth counter rather than starting a nested transaction.
That is what the YAML backend does with its advisory lock, and the
SQLite backend matches.

### 4. Views are queries; `write_view` is a no-op on SQLite

The YAML backend materialises each player's view because the filesystem
cannot do a visibility join. SQLite does not have that limitation: a
player's view is `units` joined against `sightings` for that viewer.

- `write_view(number, document)` on SQLite is a no-op. It stays on the
  port because the YAML backend still uses it; a no-op override is the
  cheapest way to say "not applicable here".
- `read_view(number)` on SQLite runs the join. That is what a caller was
  reading from the materialised file, produced fresh from the source
  every read.

*Why not delete `write_view` from the port*: because `service/turn.py`
still calls it, and the YAML backend still needs it. Delete-from-port is
a step 5 job when the YAML backend retires; today, an SQLite backend
that leaves it as `pass` costs one method definition.

*How is `sightings` populated*: `write_units(document)` on the SQLite
backend records the authoritative units, and `write_view(number,
document)` on the SQLite backend still writes the sightings — it reads
each `unit['id']` in the document and inserts a `(viewer, seen_unit_id)`
row per (id ∈ document.units, viewer=number). That is exactly what the
YAML backend was writing, expressed as rows instead of a file. The
no-op above only covers *materialising*; the sighting rows are the
join's other side.

### 5. `turn_events` is written, not read

`resolve()` receives `events = board.commit()` today. On the SQLite
backend, each event becomes a row in `turn_events` inside the same
`held()` transaction that publishes the turn. Nothing reads them yet —
adding a `show combat` subject that reads them, or replaying a game
from them, is a later change.

The YAML backend does not gain a `turn_events` file. That would break
the byte-identity guarantee step 0b established for `data/units.yaml`,
`players/<n>_units_seen.yaml` and `players/<n>_units.yaml`, and there is
no caller yet. A future step that reads `turn_events` is what would give
the YAML backend a reason to grow one.

### 6. The suite runs against both backends

`game_harness.GameHarness` gains a `backend` parameter (`'yaml'` or
`'sqlite'`, default from an environment variable or fixture); every
test that constructs a repository through the harness runs against
whichever backend it was given. A pytest fixture parametrises across
both, so the whole suite runs twice.

The two byte-diff tests — the ones that assert on the exact YAML text
in `data/units.yaml` and `players/<n>_units_seen.yaml` — pin themselves
to the YAML backend with `@pytest.mark.backend('yaml')`. They are
verifying the YAML format still emits what it emitted before, and are
not about the port.

`test_repository.py` splits: parts that assert on the port's contract
run against both; parts that assert on directory layout
(`data/board.yaml` exists) stay on YAML. A new
`test_sqlite_repository.py` asserts on the SQLite-specific
observables — the schema, the transaction behaviour, the sightings
join.

### 7. SQLite is the default at the CLI

`bgcserver`, `bgcclient` and `bgcobserver` construct
`SqliteGameRepository` when nothing overrides them. A `--backend yaml`
on each keeps YAML available. The `-g` / `--game-number` argument does
not change shape — a game number still names a directory under
`games/`, either backend.

The default rises here rather than in step 6 for one honest reason: the
port has two implementations now, and the second is meant to be the one
new games use. Anybody who wants a YAML game asks for it; anybody who
does not gets SQLite.

## Risks / Trade-offs

- **The suite doubling in wall-time.** Two backends over the whole suite
  is about 2× the time. `test_sqlite_repository.py` runs on SQLite only,
  and the byte-diff tests on YAML only. The rest is honest: a port with
  two implementations that the suite does not exercise against both is
  a port with a promise it does not keep.

- **`write_view` as a no-op on SQLite is asymmetric.** Named as a
  trade-off in Decision 4: the alternative is deleting it from the
  port, which the YAML backend still needs. The write is asymmetric
  because the two backends store visibility differently; that is a
  fact about the schema, not a smell in the port.

- **One database per file forgoes cross-game queries.** By design. Games
  are aggregates; queries across games are for an operator, not the
  application, and there is no such query today. If one lands, a
  read-only view over `ATTACH DATABASE` is one route in.

- **The FIFO transport is still on the SQLite backend.** It has to be
  until step 5; the alternative is long-poll landing here, which is a
  separate change. Documented in Context.

## Migration Plan

Within this change:

1. Land `storage/schema.sql` and `SqliteGameRepository` with every port
   method implemented, but nothing else uses it. The suite still runs on
   YAML only.
2. `test_sqlite_repository.py` — direct-schema tests that do not go
   through the harness. Includes the transaction behaviour.
3. Parametrise the harness. Every test that uses `GameHarness` (or
   constructs a repository through it) runs against both backends.
   Backend-specific tests carry `@pytest.mark.backend('yaml')` or
   `@pytest.mark.backend('sqlite')`.
4. Flip the CLI default. `bgcserver`/`bgcclient`/`bgcobserver` construct
   `SqliteGameRepository` by default; `--backend yaml` for the old
   layout.
5. `MODULE_DESCRIPTION.md`: two implementations under `storage/`, and
   SQLite as the default.

Steps 1–2 are safe on their own — the suite is green with nothing else
changed. Step 3 is where the suite doubles; step 4 is where the operator
notices; step 5 is docs.

## Open Questions

None.
