## Context

See `proposal.md`. Step 5 replaced the FIFO wait with long-poll on the
HTTP tier; step 6 flipped the clients to that tier as their real
runtime. What remains is the FIFO code itself — `notify.py`'s
platform-checking wrapper around `mkfifo` and `select`, and the
`FifoNotifier` that hangs it off the `Notifier` interface.

The bus was on its own interface after step 0b for exactly this
occasion: retiring it is one file's changes plus one bridge in `Game`.

## Goals / Non-Goals

**Goals:**
- No FIFO code anywhere; no platform check for FIFO support; no
  `wake_path` under a game's `data` directory.
- Local-mode `waitForTurn` still returns when the condition holds.
  Polling at 0.2s is the same rate the FIFO's safety timeout used, so
  latency is not observable.
- The suite stays green under both backends.

**Non-Goals:**
- Removing the YAML backend. The port has two implementations and
  that is the shape.
- Removing local-mode CLI. `bgcserver -g <n>` still works over a
  YAML or SQLite directory without `--server`; nothing that ran
  locally today stops.
- Exporting a running game as YAML from SQLite. Follow-up.

## Decisions

### 1. `NullNotifier` becomes the only `Notifier`

```
   class Notifier(ABC):    wake(name), waiter(name)     unchanged
   class NullNotifier:     the one implementation, polls with sleep
```

`FifoNotifier` deleted. Nothing in the codebase constructs one; the
`Game.__init__` bridge that used to reach for it is gone.

Why keep the ABC: because a third notifier can still land (Redis
pub/sub for a multi-host deployment; an SSE bridge for browser
clients). The ABC is a two-method interface with one implementation,
and adding a second is a file. Deleting the ABC and inlining
`NullNotifier` into `Game` would cost the same file back the day the
third notifier lands.

### 2. `_NullWaiter.wait` sleeps `POLL_INTERVAL`

```python
class _NullWaiter:
    def wait(self, timeout=SAFETY_TIMEOUT):
        time.sleep(min(timeout, POLL_INTERVAL))
        return False
```

The outer loops (`wait_for_turn`, `wait_for_all_commits`) re-check the
condition after every `wait()` return. Sleeping `POLL_INTERVAL` (0.2s)
between checks is what the FIFO waiter already fell back to on
platforms without `mkfifo`, so this is the same code path those
platforms took.

`SAFETY_TIMEOUT` stays as a cap so a caller passing a short timeout
still gets that.

### 3. `Game.__init__` always builds a `NullNotifier` if none passed

```python
def __init__(self, repository, player_number, notifier=None):
    ...
    self.notifier = notifier or NullNotifier()
```

The `hasattr(repository, 'wake') and hasattr(repository, 'waiter')`
heuristic is dead code once no repository has those methods. Removing
it is what proves the bus is off the port.

### 4. Tests: keep only what is still true

- `test_turn_notification.py`:
  - The FIFO-specific tests (`test_signalling_nobody_is_not_an_error`,
    `test_a_waiter_is_woken`, `test_a_signal_sent_before_the_wait_is_
    not_lost`, `test_waiting_gives_up_rather_than_blocking_for_ever`,
    `test_the_fifo_is_kept_out_of_the_players_directory`, the
    `FifoNotifier` test, the "Game gets a FifoNotifier" test) all
    test a mechanism that no longer exists. Removed.
  - The `NullNotifier` test and the "Game with a plain repository
    gets a NullNotifier" test kept — those are what the interface
    still promises.
  - `TurnsResolveWithoutWaiting` — the end-to-end "commit comes back
    promptly" test kept. Under polling, the 8-second budget it asserts
    on is still met with plenty of margin.

- `test_a_committed_turn_comes_back_promptly` may become the one
  guard against the FIFO poll loop creeping back — its comment is
  updated to say "against a poll loop creeping back", not "against
  polling creeping back".

## Risks / Trade-offs

- **Local-mode waits are polled, not signalled.** Named as a trade-
  off: latency is a poll interval (0.2s) instead of a signal round
  trip (~milliseconds). No test measures below the poll interval, and
  a human at a REPL cannot tell.

- **A future notifier is a file to write, not a plugin architecture.**
  Named in Decision 1: the `Notifier` ABC stays, and a Redis or SSE
  bridge is one class inheriting from it plus one branch in
  `make_session` (or wherever a `Game` gets its notifier). No new
  abstraction.

- **Tests removed.** The FIFO tests were what proved that mechanism
  worked; removing them is honest about what still exists. The tests
  that remain assert the interface's contract, which is what the
  runtime still promises.

## Migration Plan

1. `storage/notify.py` — delete FIFO helpers and `FifoNotifier`;
   update `_NullWaiter.wait` to sleep `POLL_INTERVAL`.
2. `yaml_repository.py`, `sqlite_repository.py` — delete `wake` and
   `waiter`.
3. `service/game.py` — collapse `Game.__init__` to build
   `NullNotifier` when none is passed.
4. `tests/test_turn_notification.py` — prune to what still holds.
5. Full suite green under both backends; three-run stability check.
6. Docs.

## Open Questions

None.
