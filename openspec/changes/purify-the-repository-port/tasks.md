## 1. De-text-ify the writes

- [x] 1.1 Add `units_document(board, player=None, in_play_only=False, turn=None)`
      to `storage/serialise.py`, returning the dict shape the file already
      contains (`{board, turn, player, units}`) — data-only, no YAML text
      (design.md — Decision 2). Verify by round-tripping through
      `yaml.safe_dump` and confirming keys and unit records match what
      `serialise_units` was producing.
- [x] 1.2 Move the hand-crafted YAML emitter — the `serialise_units` and
      `serialise_orders` text builders — from `storage/serialise.py` into
      `storage/yaml_repository.py` as private helpers. They keep producing
      the current bytes exactly (design.md — Decision 2 explains why hand-
      crafted rather than `yaml.safe_dump`). Verify no service or CLI file
      imports the moved emitters any more.
- [x] 1.3 Change the port signatures on `GameRepository` (the ABC in
      `storage/repository.py`) so `write_units`, `write_view` and
      `write_orders` take documents rather than text (design.md — Decision 1).
      Update `YamlGameRepository` to accept documents and use the emitters
      from 1.2 internally.
- [x] 1.4 Update `service/turn.py`'s four writing callsites to build documents
      via `units_document(...)` rather than calling `serialise_units` /
      `serialise_orders` / `_as_orders`, and remove `_as_orders` and the
      unused imports. Verify with a byte-diff that a game resolved before this
      change and one resolved after produce identical files under
      `data/units.yaml`, `players/<n>_units_seen.yaml` and
      `players/<n>_units.yaml`.
- [x] 1.5 Update every test that handed text to a write method or called the
      removed emitters (design.md — Decision 4): `test_repository.py`,
      `test_storage_safety.py`, `test_turn_publication.py`,
      `test_rules_defects.py`, `test_turn_events.py`,
      `test_combat_stalemate.py`, `test_board_conventions.py`. Only the input
      shape changes; verify by re-reading each edit that nothing an assertion
      checks was rewritten.

## 2. Split notify off the port

- [x] 2.1 Add `Notifier` (an ABC over `wake(name)` and `waiter(name)`),
      `FifoNotifier` (implementing over today's FIFO helpers) and
      `NullNotifier` (no-ops) in `storage/notify.py` (design.md — Decision 3).
      Verify each with a small direct test — `FifoNotifier` wakes and waits;
      `NullNotifier` does neither and does not raise.
- [x] 2.2 Have `Game.__init__` take an optional `notifier`. When one is not
      passed, derive it: `FifoNotifier` if the repository has `wake`/`waiter`
      (the YAML case), a `NullNotifier` otherwise. Verify with a unit test that
      a `Game` built with only a `YamlGameRepository` gets a `FifoNotifier`,
      and one built with a repository that only reads and writes gets a
      `NullNotifier`.
- [x] 2.3 Change `service/turn.py`'s four wake/waiter callsites to use
      `game.notifier` instead of `game.repository`. Verify the client's
      `waitForTurn` still returns when the server signals it, using the
      existing `test_turn_notification.py` shape — the notification stops
      going through the port but keeps working.
- [x] 2.4 Remove `wake` and `waiter` from `GameRepository` (the ABC in
      `storage/repository.py`). `YamlGameRepository` keeps its methods — they
      are no longer part of the port's promise, but the FIFO helpers still
      exist for the bridge in 2.2 to find.

## 3. Finish

- [x] 3.1 Verify `serialise_units`, `serialise_orders` and `_as_orders` are no
      longer called from `service/`, `cli/` or anywhere outside the YAML
      backend, and delete them (or keep them local to `yaml_repository.py`).
- [x] 3.2 Update `MODULE_DESCRIPTION.md`'s account of `storage/`: the port
      takes data, the bus is on its own interface, and a repository that does
      not know how to notify is fine — `Game` bridges. Verify every path it
      names exists.
- [x] 3.3 Run the full suite, `flake8 . --select=E9,F63,F7,F82` as CI does,
      and `pylint` against the configured `.pylintrc`. Verify the suite is
      green and lint reports no new message kind in any file that did not
      report it before.
- [x] 3.4 Run the full suite ten times over and verify it is green every time.
      The bus split touches how the server and clients rendezvous, and that
      is exactly the kind of thing that is green once and wedged on the
      eleventh.
