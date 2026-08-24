## 1. Land the schema and the backend

- [x] 1.1 Add `storage/schema.sql` with the tables in design.md — Decision 2.
      Each table matches what the same-named YAML file already held; new
      tables `sightings` and `turn_events`. Verify by `sqlite3 :memory: <
      schema.sql` reports no error and every table is created.
- [x] 1.2 Add `storage/sqlite_repository.py` with `SqliteGameRepository`
      implementing every method on `GameRepository` (design.md — Decision 2).
      Reads and writes go to real rows; `read_view` runs the visibility
      join; `write_view` records sightings; `turn_events` is written but
      not read. Constructor takes `(gameno, base_path=None)` matching
      `YamlGameRepository`; the database lives at
      `games/_<gameno>/game.sqlite3` (design.md — Decision 1).
- [x] 1.3 `held(read=False)` opens a transaction — `BEGIN IMMEDIATE` for a
      writer, `BEGIN DEFERRED` for a reader; nested `held()` calls
      increment a depth counter rather than re-opening (design.md —
      Decision 3). A `SQLITE_BUSY` from a writer raises `GameIsBusy`
      (matching `lock.GameIsBusy` from the YAML side). WAL is on.
      Keep `wake`/`waiter` — they use the same `notify.py` helpers the
      YAML backend uses, and step 5 will retire them together.

## 2. Test the SQLite backend directly

- [x] 2.1 Add `tests/test_sqlite_repository.py` — direct-schema tests that
      do not go through the harness (design.md — Migration Plan step 2).
      Cover: `ensure()` creates every table; `write_units(document)` +
      `read_units()` round-trips a unit exactly; `write_orders` +
      `read_orders` round-trips; `mark_committed` + `committed_players`;
      `write_draft` + `read_draft`; `read_view(number)` is the visibility
      join.
- [x] 2.2 Add `tests/test_sqlite_safety.py` — the `held()` transaction as
      a lock. Cover: a second writer under `held()` gets `GameIsBusy`;
      a reader does not block a writer (WAL); a nested `held()` inside
      another `held()` is one transaction, not two.

## 3. Parametrise the suite

- [x] 3.1 Add `tests/backends.py` (or extend `game_harness.py`) with a
      pytest fixture `backend` that yields `'yaml'` and `'sqlite'`.
      `GameHarness.__init__` takes a `backend` parameter and constructs
      the matching repository. Verify by parametrising one
      already-existing test and watching it collect twice.
- [x] 3.2 Add `@pytest.mark.backend('yaml')` and `@pytest.mark.backend(
      'sqlite')` markers, and a conftest hook that skips a test whose
      marker does not match the current backend (design.md — Decision 6).
      Pin the byte-diff tests to `'yaml'`:
      `test_turn_publication.py::test_the_turn_is_published_before_a_
      player_is_released` (and its byte-related siblings),
      `test_storage_safety.py` write tests that assert on the exact
      target file bytes.
- [x] 3.3 Flip every remaining test through the harness. Every test that
      constructs `YamlGameRepository` directly now goes through
      `GameHarness.repository()`. Verify the full suite runs twice under
      `pytest` and both halves are green.
- [x] 3.4 Verify the SQLite half reports the same test IDs as the YAML
      half, less the ones pinned to YAML. A test collected once when it
      should be twice is what the parametrisation is meant to catch.

## 4. Flip the CLI default

- [x] 4.1 Add `--backend {sqlite,yaml}` (default: sqlite) to
      `bgcserver.py`, `bgcclient.py` and `bgcobserver.py`. The three
      binaries construct the matching repository at startup. Verify by
      running `bgcserver -g 1` in a fresh directory and finding a
      `game.sqlite3` under `games/_1/`; running with `--backend yaml`
      creates the YAML layout instead.
- [x] 4.2 `session.load_game` (or wherever the roles reach for a
      repository) takes a factory rather than constructing
      `YamlGameRepository` directly. Verify no `cli/` file constructs
      `YamlGameRepository` any more except through that factory.

## 5. Finish

- [x] 5.1 Update `MODULE_DESCRIPTION.md`: two backends under `storage/`,
      SQLite is the default, `schema.sql` is the DDL loaded on first
      `ensure()`. Verify every path it names exists.
- [x] 5.2 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI
      does, and `pylint` against the configured `.pylintrc`. Verify the
      suite is green under both backends and lint reports no new
      message kind in any file that did not report it before.
- [x] 5.3 Run the full suite ten times over and verify it is green
      every time. The transaction contention is exactly the kind of
      thing that is green once and wedged on the eleventh.
