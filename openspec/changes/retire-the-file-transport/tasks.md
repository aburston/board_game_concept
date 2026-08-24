## 1. Strip the FIFO code

- [x] 1.1 In `storage/notify.py`, delete `HAVE_FIFOS`, `wake_path`,
      the FIFO `Waiter` class, and the `signal` function. Delete
      `FifoNotifier`. Keep `Notifier` (ABC) and `NullNotifier`.
- [x] 1.2 In `_NullWaiter.wait`, add `time.sleep(min(timeout,
      POLL_INTERVAL))` before returning `False` (design.md — Decision
      2). The outer loops in `wait_for_turn` /
      `wait_for_all_commits` are what actually decide when the wait
      ends.

## 2. Strip the port's leftovers

- [x] 2.1 Remove `wake` and `waiter` from `YamlGameRepository`.
- [x] 2.2 Remove `wake` and `waiter` from `SqliteGameRepository`.

## 3. Simplify `Game.__init__`

- [x] 3.1 In `service/game.py`, collapse the notifier branch:
      `self.notifier = notifier or NullNotifier()`. Remove the
      `hasattr(repository, 'wake')` heuristic and the `FifoNotifier`
      import.

## 4. Prune the tests

- [x] 4.1 In `tests/test_turn_notification.py`, remove the FIFO-
      signalling tests (design.md — Decision 4). Keep
      `test_the_null_notifier_does_nothing_and_does_not_raise` and
      `test_game_falls_back_to_a_null_notifier_when_the_repository_
      has_no_bus` (renaming the latter to reflect that every
      repository is now such a repository).
- [x] 4.2 Keep the `TurnsResolveWithoutWaiting` end-to-end test as
      the guard against a poll loop creeping back.

## 5. Docs

- [x] 5.1 `MODULE_DESCRIPTION.md` — the `storage/notify.py` line
      rewritten (no more "the bus on its own interface"); the
      `storage/lock.py` line updated to name only the YAML backend.
- [x] 5.2 `README.md` — a short "Storage backends" note: SQLite is
      the recommended runtime; YAML is the readable-file alternative,
      still available.

## 6. Finish

- [x] 6.1 Run the full suite under both backends, `flake8`, `pylint`.
      Verify green and no new pylint message kind in any file that
      did not report it before.
- [x] 6.2 Run the full suite three times over.
