## Why

`put-a-rest-api-under-the-cli` names step 7 as the last one: retire the
file transport (the FIFO bus and its poll-loop fallback), keep YAML as
export/test only. Steps 2–6 built and flipped the HTTP tier; nothing
that ships as a real deployment reads a FIFO now. What is left is
paying down the two-transport tax: `notify.py`'s FIFO helpers, the
`FifoNotifier` bridge in `Game`, and the `wake`/`waiter` methods each
repository still exposes.

The FIFO bus was there because a client and a server on the same host
needed to rendezvous through the filesystem. Over HTTP they rendezvous
through long-poll, which lands the same latency without a FIFO or a
poll loop that pretends to be one. Deleting the file transport is the
step that removes a whole class of concerns: platforms that have no
`mkfifo`, FIFOs blocking `open()`, signals lost between processes.
Nothing above the storage port cares that any of that is gone.

The YAML backend does not go away. It is kept for two things: the
byte-diff tests that pin themselves to it (so a future change that
touches the file format has a canary), and one-shot export of a game
someone wants to `cat`. What it stops being is a *running* backend on
its own — no CLI role now runs unattended over YAML. Local mode
against YAML is still built and tested; a real deployment picks
SQLite behind the HTTP tier.

## What Changes

- **`storage/notify.py` loses its FIFO code.** `HAVE_FIFOS`, `Waiter`
  (the FIFO one), `signal`, `wake_path`, and `FifoNotifier` are gone.
  `NullNotifier` stays and becomes the only implementation. Its
  `_NullWaiter.wait` sleeps `POLL_INTERVAL` (0.2s) so the outer
  re-check loop does not spin — the same cadence the FIFO poll used
  as its safety timeout.

- **`Game.__init__`'s bridging logic goes.** Every `Game` gets a
  `NullNotifier` (or whatever the caller passed). The `hasattr(
  repository, 'wake')` heuristic is dead code once no repository has
  those methods.

- **`YamlGameRepository` and `SqliteGameRepository` lose `wake` and
  `waiter`.** They were never part of the `GameRepository` contract
  after step 0b — they were the FIFO bridge. Now the bridge is gone
  too.

- **Local-mode `waitForTurn` / `waitForPlayerCommit` fall back to
  polling.** The outer loops in `service/turn.py` already re-check the
  condition after `waiter.wait()` returns — with the `NullNotifier`
  they check every `POLL_INTERVAL`. Semantically identical, latency
  measured in tenths of a second.

- **`test_turn_notification.py` is largely gone.** The FIFO signalling
  tests test a mechanism that no longer exists. The Game-picks-a-
  notifier tests are replaced by one small test: every `Game` gets a
  `NullNotifier`.

- **A note in `README.md`.** "Storage backends" section says SQLite is
  the recommended runtime backend; YAML is available for tests and for
  the operator who wants to read the game state with `cat`.

**Not** in this change: an export command (`bgcadmin export --format
yaml`); the file layout is what any future export would produce, so
adding a command is a follow-up. Also not: removing the YAML backend
class itself — the port has two implementations, and that stays the
proof the port is one.

## Capabilities

None. Behaviour a caller sees is unchanged; the latency of local-mode
waits shifts from "FIFO-signalled" to "polled at 0.2s" and is not
observable outside microbenchmarks. `skip_specs`.

## Impact

- **Storage**: `storage/notify.py` — FIFO code removed;
  `NullNotifier`'s `_NullWaiter.wait` gains its sleep.
  `storage/yaml_repository.py` and `storage/sqlite_repository.py` —
  `wake`/`waiter` removed.
- **Service**: `service/game.py` — the `FifoNotifier` bridge branch
  removed; `Game.__init__` always constructs a `NullNotifier` when
  none is passed.
- **Tests**: `test_turn_notification.py` — the FIFO-specific tests
  removed; the `FifoNotifier` and Game-picks-`FifoNotifier` tests
  removed; the Game-picks-`NullNotifier` test kept. Test suite must
  stay green under both backends.
- **Docs**: `README.md` — a "Storage backends" note; `MODULE_
  DESCRIPTION.md` — the storage section's `notify.py` line rewritten
  and the mention of a "bus on its own interface" trimmed to what is
  actually served.
