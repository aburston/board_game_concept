## Why

A client can stop waiting for a turn before the server has published the result
of it, and then draw a board that is missing its own units.

The client waits on the wrong fact. `turn.wait_for_turn` blocks while
`has_orders(player)` is true — that is, while `players/<n>_units.yaml` still
exists — and `Game.load` decides `unprocessed_moves` from the same file. But
`resolve` deletes it near the *start* of resolution and publishes each player's
view near the end:

```
   turn.py:221   repository.clear_orders()      ← the client's condition goes false HERE
   turn.py:223   repository.clear_commits()
   turn.py:233   repository.write_progress(...)
   turn.py:236   write_player / write_orders / write_rejections, per player
   turn.py:252   repository.write_units(...)
   turn.py:254   repository.write_view(...)     ← its view is published HERE
   turn.py:261   repository.wake(number)        ← and only now is it woken
```

The wake at the end is right. The trouble is that a client which arrives at
`wait_for_turn` inside that window never waits at all: it checks the condition
before blocking, finds no orders, and goes straight on to read a view belonging
to the previous turn — or one being written underneath it.

Caught in the act. A client that had just committed its only unit redrew an
empty board and then timed out waiting for that unit's symbol:

```
    bgcclient> commit complete
    waiting for turn to complete...
    bgcclient> +-+-+-+-+
               |#|#|#|#|          <- no units
               +-+-+-+-+
```

Two failures in twenty-six runs of the suite, in
`tests/test_cli_client_surface.py`. The ordering is unchanged since the
`split-into-layers` change, so this is neither new nor caused by drafting or by
the observer's numbering; both of those changes only made it easier to catch.

It is a real defect and not only a flaky test. A player who commits can be shown
a board without their army on it, and can be asked for orders for a turn that
has not been published — and an order given against a stale board is refused
when the turn does resolve, which the player has no way to make sense of.

It also matters more than it did. `game-persistence` requires a client to load
its own published view and nothing else, so a view read in this window is the
whole of what the player is shown. And an HTTP API long-polling `GET
/games/{id}/turns/{n}` would be answering the same question this waits on: a
caller told "turn resolved" and then handed last turn's board is a worse failure
over a network than at a prompt, because nothing about it looks like a race.

## What Changes

**A player stops waiting when the turn has been published, not when the server
has started resolving it.**

- The fact a waiting client tests SHALL mean *this turn's result is readable*.
  Today it means *the server has consumed my orders*, which happens first.
- The same fact decides `unprocessed_moves`, so a client that reloads for any
  other reason during resolution is told the turn is still in progress rather
  than being handed a half-published game.
- The wake stays where it is, at the end. What changes is what a client that
  was not asleep for it concludes.

**BREAKING**: nothing in the file layout that a user or a game in progress
depends on. Whether the change is visible in `game-persistence`'s described
layout at all depends on which mechanism the design picks.

### The obvious fix is wrong, and the design must not take it

Moving `clear_orders()` down to sit beside the wakes deletes orders the same
function writes on a loaded player's behalf twenty lines earlier:

```
   turn.py:244   repository.write_orders(number, _as_orders(player['units']))
                 ← the units a `load player` file brought in, published as that
                   player's orders for the turn about to be resolved
```

A `clear_orders()` after that erases them, and a game set up with `load player`
never gets its units onto the board. That path has its own scenario in
`game-server` and is what `tests/test_cli_observer_surface.py` opens a played
game with, so it would fail loudly — but it is the first thing anyone reaching
for this bug will try, and it is worth writing down before they do.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `turn-commit`: *Players Wait For Turn Completion* comes to mean that a player
  is held until the turn they committed to has been published, rather than until
  their orders have been consumed. The requirement's intent is unchanged; what
  changes is the moment it is satisfied.
- `game-persistence`: *Pending Order Detection* stops resting on the presence of
  the order file, which is deleted before the turn is published; and *Order
  Publication*'s account of what the server removes and when is restated in
  terms of a turn that is finished rather than one that is under way.

## Impact

- **Service**: `service/turn.py` — `resolve`'s ordering, and the condition
  `wait_for_turn` blocks on. `service/game.py` — `unprocessed_moves`, which is
  read from the same fact and must move with it.
- **Storage**: possibly `storage/repository.py`, if the fact a client waits on
  becomes something the port has to offer rather than something derived from the
  operations it already has. Whether it does is the design's to settle.
- **Tests**: `tests/test_cli_client_surface.py` holds the two scenarios that
  caught this. A test that reproduces the window deliberately — rather than one
  in twenty-six runs — is the thing this change most needs and does not have.
  `tests/test_turn_notification.py` covers the signalling and will want the new
  condition stated in it.
- **Docs**: `SPEC_COVERAGE.md` gains the divergence, which belongs beside number
  10 — loading a game racing the server deleting orders — since both come of the
  same file being deleted while the turn is still being written.

## Open questions

1. **What should a client wait on?** The turn number reaching the one it
   committed for, a marker written last, or the views themselves. The first
   reads best and is what an API's long poll would want; `write_progress` is
   currently early, so it would move too.
2. **Does the window need closing as well as narrowing?** Any reordering leaves
   some interval between the first write of a turn and the last. Whether that is
   acceptable, or whether a turn must be published atomically, is the same
   question as the missing lock — and the answer may be that this change
   narrows the window and the lock closes it.
