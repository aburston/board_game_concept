## Why

The check that authorises a turn to resolve, and the resolution it authorises,
are two separate acts with a gap between them.

`wait_for_all_commits` loops until every player still in the game has committed,
outside any hold — it must be outside, because it waits for as long as a player
takes to decide. It then returns, the server loads the game, and `resolve` takes
the game for writing and resolves it. Three steps, and the first is the only one
that asks whether the turn *may* be resolved:

```
   wait_for_all_commits   every player has committed        ← asked here
   load_game              read the game
   resolve                take the game, resolve it         ← done here
```

Nothing re-asks inside the hold. The `serialise-access-to-a-game` change made a
resolution uninterleavable and said in as many words that this was what it did
not fix: the resolution cannot be cut in half, but it can still be begun on a
decision that was true a moment ago and is not true now.

What can change in the gap is not exotic. Another resolution — a second server
started by accident, or one an operator ran by hand — takes the game first,
resolves the turn and spends every commit that opened it. The first server then
loads and resolves too, against a game with no orders in it, advancing the turn
number and publishing a board nobody ordered. Each player is told their orders
were consumed twice.

It matters more the moment there is an API. `POST /commit` is one of many
processes by construction, and the natural shape — record the commit, and if
that was the last one resolve the turn — is precisely a check and a resolution
that must not come apart. Today's service layer offers no operation that does
both, so every caller would have to reimplement the barrier, and every caller
would have the same gap.

## What Changes

**Resolving a turn asks whether it may be, while holding the game.**

- **One operation decides and acts.** A caller asks for the turn to be resolved
  *if the barrier is met*, and gets back whether it was. The check and the
  resolution happen under one hold of the game, so nothing can come between
  them.

- **It reads the game inside that hold.** The barrier is asked about the game as
  it is when the turn resolves, not as it was when the caller last looked.

- **Waiting becomes what it always was — a hint.** `storage/notify.py` already
  says a signal "is only ever a hint: every caller re-checks the condition it
  actually cares about". The commit barrier is the one caller that did not.
  Waking now sends the server to ask again, holding the game, rather than to act
  on what it was told.

- **A turn that may not be resolved is not an error.** The barrier not being met
  when it is re-asked means somebody else got there first, which is the system
  working. The server goes back to waiting rather than reporting a failure.

**BREAKING**: nothing. A single server resolving turns for a game nobody else is
touching sees exactly the behaviour it sees today, because the re-asked question
has the same answer.

### Not in this change

A player's commit does not resolve the turn. The other reading of "one step" —
that whichever commit completes the barrier resolves the turn inline, retiring
the unattended server — is the option `ARCHITECTURE_OPTIONS.md` sets out as (b)
in §5, and it removes `game-server`'s Unattended Turn Cycle rather than tightening
it. It also needs exactly the operation this change adds, so nothing here is
spent if it follows.

## Capabilities

### Modified Capabilities
- `turn-commit`: the Commit Barrier states that the question is asked where the
  turn is resolved and while the game is held, so that a turn is never resolved
  on a barrier that was met a moment ago; and that finding it unmet is ordinary
  rather than a failure.
- `game-server`: the Unattended Turn Cycle asks again after being woken instead
  of acting on the waking, and treats a turn it may no longer resolve as
  something to go on waiting for.

## Impact

- **Service**: `service/turn.py` — the barrier condition comes out of
  `wait_for_all_commits` into something both the wait and the resolution ask,
  and a new operation holds the game across reading it, asking, and resolving.
  `service/game.py` — the session gains that operation beside `serverSave`,
  which stays what the administrator's `commit` calls to end setup, where no
  barrier applies.
- **CLI**: `cli/bgcserver.py` — the unattended half of the loop asks for a turn
  to be resolved if it may be, and goes back to waiting when it may not.
- **Tests**: a second resolution racing the first is the case worth having, and
  it can be driven deterministically by resolving from inside the first
  resolution's hold rather than by timing. `tests/test_turn_publication.py` and
  `tests/test_commit_record.py` both assert around the barrier and must keep
  passing unedited.
- **Docs**: `SPEC_COVERAGE.md`, where the entry for `serialise-access-to-a-game`
  says this is the part it left open.
