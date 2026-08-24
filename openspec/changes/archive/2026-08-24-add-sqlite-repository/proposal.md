## Why

`put-a-rest-api-under-the-cli` names step 1 as the second backend that the
port existed for. Two steps preceded it — extracting the session-backend
seam, and de-text-ifying the port. This is the swap they were shaped for.

The port is one interface with one implementation today. `YamlGameRepository`
keeps games as YAML files under a directory; every reader and writer in the
service layer talks to that shape. A second implementation over SQLite is
what turns the port from a promise into a lever: the same suite passes over
two backends, and the choice of backend is the caller's rather than the
codebase's.

Two things the schema buys that the files could not:

- **A view stops being a materialised file and becomes a query.** Today
  `write_view` writes each player's view because the filesystem cannot do a
  visibility join. SQLite can: a player's view is `units` joined against
  `sightings` for that viewer.
- **The combat log is a table insert.** `board.commit()` already returns the
  events; capturing them into `turn_events` is nearly free and gives replay
  and a visible combat record that are expensive to retrofit later.

And one thing SQLite buys that the file layout could not: `held()` becomes a
transaction. `serialise-access-to-a-game` shaped the lock for this — the
same two words are advisory `flock` for the YAML backend and `BEGIN
IMMEDIATE` for SQLite. `resolve_when_ready` does not change.

## What Changes

- **`SqliteGameRepository` joins `YamlGameRepository` under the port.** One
  file per game — `games/_<gameno>/game.sqlite3` — so a game is still a
  directory the operator can copy, back up, and delete. Real tables, not
  YAML blobs in columns; a database backend that stored the YAML text would
  throw away every reason to have chosen SQLite.

- **The schema maps the files nearly one-to-one.** `games`, `memberships`,
  `unit_types`, `units`, `orders`, `commits`, `drafts`, `rejections`,
  `sightings`, `turn_events`. Each table is what the same-named YAML file
  held, less the ones the schema absorbs (`views` becomes a join,
  `turn_events` is new).

- **`held()` is a transaction.** `BEGIN IMMEDIATE` for a writer,
  `BEGIN DEFERRED` for a reader; nested `held()` calls upgrade a read
  lock to a write one on demand. WAL is on so a reader does not block a
  writer.

- **The suite runs against both backends.** The `harness` fixture takes a
  backend parameter — `yaml` and `sqlite` — and every test that constructs
  one runs twice. Nothing in the suite hard-codes `YamlGameRepository`.

- **SQLite is the default.** `bgcserver`, `bgcclient` and `bgcobserver`
  construct `SqliteGameRepository` when nothing overrides them. A new
  `--backend yaml` on each CLI keeps YAML available for anybody who wants a
  game they can `cat` — and for the byte-diff tests that guard the YAML
  format.

- **A view becomes a query.** `read_view(number)` on the SQLite backend
  joins `units` against `sightings`. `write_view` still exists on the port
  and is a no-op on the SQLite backend, because writing what can be
  computed is the file-layout habit the schema is trying to unlearn.

- **The combat log lands.** Every event `board.commit()` returns is
  inserted into `turn_events`. Nothing reads it yet; this is the point at
  which it becomes cheap to keep.

**Test edits are expected.** Every test that constructed
`YamlGameRepository` directly now goes through a factory the harness
picks. Nothing that any test asserts changes.

Not in this change: HTTP, long-poll, any user-visible behaviour change,
the observer's `read_view` rewriting, or the combat log becoming a
`show` subject. Those are their own changes.

## Capabilities

None. This is a port implementation, and the behaviour it constrains —
what a game holds and what a turn resolves to — is unchanged. `skip_specs`.

## Impact

- **Storage**: `storage/sqlite_repository.py` — new; `SqliteGameRepository`
  over a real schema. `storage/schema.sql` — the DDL for that schema,
  loaded on first `ensure()`. `storage/repository.py` — no signature
  changes (step 0b already made the port take data). `storage/lock.py` —
  keeps its `Holding` for the YAML backend; unrelated to the SQLite
  transaction.
- **Service**: no changes. The port took data before this change; the
  callers do not care which backend is behind it.
- **CLI**: `bgcserver`, `bgcclient`, `bgcobserver` — a new `--backend`
  option (`sqlite`, default; `yaml`); default becomes SQLite. `harness`
  (test helper) — takes a backend and constructs the matching
  repository.
- **Tests**: the whole suite runs twice, once per backend, via a
  harness-level parameter. The byte-diff tests keep asserting on the
  YAML backend specifically. `test_repository.py` and
  `test_storage_safety.py` gain their SQLite counterparts —
  `test_sqlite_repository.py` and `test_sqlite_safety.py` — that check
  the schema does what its columns say, and that a `held()` transaction
  behaves like the advisory lock behaved.
- **Docs**: `MODULE_DESCRIPTION.md`'s `storage/` — the port has two
  implementations, and SQLite is the default.
