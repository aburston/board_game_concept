## Context

See `proposal.md` — Why. Two facts about the existing code decide the shape.

**`resolve` reads the game from memory, not from disk.** `_apply_orders` works
from `game.players[n]['moves']`, which `load` put there. So a resolution is only
as current as the load that preceded it, and moving the barrier check inside the
resolution's hold is not enough on its own — the load has to come inside too, or
the check would be asked about a game the resolution is not going to resolve.

**The hold is re-entrant within a repository.** `lock.Holding` counts its depth
and takes the operating system's lock only at the outermost, so a `load` (which
holds for reading) nested inside a hold for writing is not a second acquisition
and does not downgrade anything. That is what makes read-then-check-then-resolve
expressible as one hold at all.

## Goals / Non-Goals

**Goals:**
- One operation that reads the game, asks whether the turn may be resolved, and
  resolves it — with nothing able to come between.
- The same operation available to any caller, so an HTTP handler does not
  reimplement the barrier.
- Waiting stays outside every hold, because it waits on a person.

**Non-Goals:**
- Resolving a turn from a player's commit. See the proposal.
- Changing what the barrier *is*. Every player still in the game, eliminated
  players not waited for: unchanged.
- Changing what a resolution computes. `test_determinism.py` must not move.

## Decisions

### 1. `resolve_when_ready` reads, asks and resolves under one hold

```
   with repository.held():        exclusive, for all three
       game.load()                the game as it is now, not as it was
       if not barrier_met(game):  asked here, inside
           return None            somebody else got there first
       return resolve(game)
```

`load` holds for reading and `resolve` holds for writing; both nest inside this
one and neither takes a second lock. The outer hold is exclusive because the
innermost thing it does is a resolution.

*Why the load is inside*: without it the barrier would be asked about
`game.getTurnNumber()` and `game.players` as they were before the wait, which is
exactly the staleness the change exists to remove.

### 2. Three answers, not two

| returns | means | what the server does |
|---|---|---|
| `None` | the barrier was not met | go back to waiting |
| `True` | resolved | say so, and carry on |
| `False` | could not resolve — no board, or the game is over | what it does today |

`resolve` already returns `False` for a board too small and for a decided game,
and the server treats that as fatal. Folding "the barrier was not met" into the
same `False` would make the server exit on the one case that is not a failure at
all. Hence a third answer rather than a second meaning for an existing one.

### 3. The condition comes out of the waiting

`wait_for_all_commits` holds the condition inline today. It becomes
`barrier_met(game)`, which both the wait and `resolve_when_ready` ask — the wait
against the game it was given, the resolution against the game it has just read.
One statement of what the barrier is, asked in two places, which is the point:
the two could otherwise drift, and a barrier that means one thing to the waiter
and another to the resolver is worse than the gap it was meant to close.

The wait keeps computing `awaited` and the turn number once, before its loop, as
it does today. It is a hint; being slightly stale costs a wake-up, and the
authoritative question is asked again where it matters.

### 4. `serverSave` stays what ends setup

The administrator's `commit` ends setup, and no barrier applies to it: nobody
has committed and nothing is being waited for. That path keeps calling a plain
resolution. The two were the same call before this change, which is part of why
the barrier had nowhere obvious to be asked.

### 5. The server asks, and goes back to waiting when told no

```
   wake  ─▶  resolve_when_ready()  ─┬─ None ─▶ wait again
                                    ├─ True ─▶ "commit complete"
                                    └─ False ─▶ the error it reports today
```

The `None` path waits before looping, rather than looping straight back into
another attempt — otherwise a barrier that is never met again becomes a spin,
which is the failure mode the `draft-orders-and-explicit-commit` change already
met once and fixed by spending commits.

## Risks / Trade-offs

- **The load moves inside the hold, so a resolution now reads as well as
  writes** → it always did read; it read earlier, outside. The hold is exclusive
  either way and the reading is milliseconds.

- **Two loads per cycle** → the server's loop still loads at the top for the
  interactive path and its display, and `resolve_when_ready` loads again inside
  the hold. The second is the authoritative one. Removing the first means
  restructuring the loop around the setup path, which is more change than the
  duplicate read costs.

- **`None` is easy to get wrong at a call site** → `if resolved:` treats it like
  `False`, which sends the server to the fatal branch rather than back to
  waiting. Named tests cover each of the three answers separately.

- **A wedged resolver now blocks the barrier as well as the writing** → it did
  from the moment holding existed; `lock.TIMEOUT` turns it into a reported error
  rather than a hang, and the operating system releases a dead holder.

## Migration Plan

No data migration and no format change. A single server resolving turns for a
game nobody else touches behaves identically, because the re-asked question has
the same answer.

1. `barrier_met` out of `wait_for_all_commits`, with the wait asking it. No
   behaviour change; the suite must stay green untouched.
2. `resolve_when_ready`, and the session operation beside `serverSave`. Nothing
   calls it yet.
3. The server's unattended half calls it and handles all three answers.

Step 3 is the one that changes what the server does, and the one to review.

## Open Questions

None.
