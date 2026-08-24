## Why

`put-a-rest-api-under-the-cli` names step 0b as the last thing that must land
before a SQLite backend can implement the same port cleanly. Two things about
`GameRepository` are shaped for YAML files rather than for storage in general,
and both would leak into any other backend if left alone:

- **The write side takes text.** `write_units(text)`, `write_view(n, text)` and
  `write_orders(n, text)` take a YAML string that the service layer builds by
  calling `serialise_units` from storage — service code composing storage-format
  text and handing it back. The read side returns data (records). A SQLite
  backend given `write_units("units:\n  - {...}")` would have to parse a
  hand-crafted YAML string in order to write rows, which throws away every
  reason to have chosen SQLite.

- **The port has a transport on it.** `wake(name)` and `waiter(name)` are the
  FIFO bus, not storage. `notify.py`'s own docstring already says so ("waking
  the other side of the file transport"). Long-poll replaces them at step 5;
  a SQLite backend has no obvious way to implement them because it has no
  business trying to. They do not belong on the storage port.

Step 0b puts both right. The port stops carrying text and stops carrying the
bus. The YAML backend keeps producing the same file bytes it did before — no
game a user or a test opens changes shape — and every test that constructed
those bytes by hand is updated to construct the data instead.

## What Changes

- **Writes take data.** The signatures become `write_units(document)`,
  `write_view(number, document)` and `write_orders(number, document)`, where a
  document is the plain-data shape the file already contained
  (`{board, turn, player, units}`). Each backend serialises its own way. The
  YAML backend keeps producing byte-identical files.

- **The service layer builds documents, not text.** `service/turn.py` stops
  calling `serialise_units` / `serialise_orders` / `_as_orders`. A new
  `units_document(board, player, in_play_only, turn)` in `storage/serialise.py`
  returns the dict; the emitters that build the YAML text move behind the YAML
  backend, where they belong.

- **`wake` and `waiter` leave the port.** A `Notifier` interface (still in
  `storage/notify.py`, beside its FIFO implementation) captures them. `Game`
  gains a `notifier` alongside its `repository`, and `service/turn.py` calls
  `game.notifier` for signalling. `GameRepository` no longer promises them.

- **`Game` keeps working today.** Where no notifier is passed to it — every
  callsite in the code and in the suite — it derives one from the repository if
  the repository knows how (the YAML case) or a no-op notifier otherwise. So
  nothing outside this change has to be told about the split; only the callers
  who care are.

**Test edits are expected.** Tests that constructed raw YAML strings and handed
them to `write_units("units: None\n")` are updated to pass the empty document
their string encoded. Tests that used `serialise_units(board)` as a helper are
updated to build the document. `test_turn_publication.py`'s recorder wrappers
carry the new signatures. Every edit is a rewrite of *how* a test says what it
already says; none changes what it asserts.

Not in this change: SQLite itself, HTTP, any behaviour change. This makes the
port shaped so the swap in step 1 is a swap and not a rewrite.

## Capabilities

None. This is a port shape refactor; the behaviour it constrains — which files
exist and what they contain — is unchanged. `skip_specs`.

## Impact

- **Storage**: `storage/repository.py` — the `GameRepository` ABC drops
  `wake`/`waiter` and switches the three write signatures to documents.
  `storage/yaml_repository.py` — writes accept documents and emit the current
  hand-crafted YAML from them; still has `wake`/`waiter`, now inherited from
  the `Notifier` interface. `storage/serialise.py` — `serialise_units` and
  `serialise_orders` become `units_document` (data-returning) plus internal
  YAML emitters used by the YAML backend. `storage/notify.py` — gains
  `Notifier` (an ABC over `wake`/`waiter`) and `FifoNotifier` around today's
  FIFO code.
- **Service**: `service/game.py` — `Game.__init__` gains an optional
  `notifier`, defaulted from the repository. `service/turn.py` —
  `repository.wake/waiter` calls become `game.notifier.wake/waiter`; the four
  callsites that pass text to writes build a document instead.
- **Tests**: `test_repository.py`, `test_storage_safety.py`,
  `test_turn_publication.py`, `test_rules_defects.py`, `test_turn_events.py`,
  `test_combat_stalemate.py`, `test_board_conventions.py` — the callsites that
  hand raw text or call `serialise_units` are updated. Nothing that any test
  asserts changes.
- **Docs**: `MODULE_DESCRIPTION.md`'s account of `storage/` — the port takes
  data and the bus lives on its own interface.
