## Context

See `proposal.md` — Why. What shapes the approach is that the repository already
has a precedent for a platform facility it cannot assume.

`storage/notify.py` blocks on a FIFO, and where the platform has none it waits
on the clock instead, saying so in its own docstring rather than pretending.
Locking is the same shape: `fcntl.flock` exists on this platform and does not
everywhere, and the honest fallback is no locking and the behaviour of today.

Two more facts decide the rest. The spans that write a game are short —
`resolve` and `publish` are milliseconds — while the spans that *wait* are
unbounded, because the barrier holds until a person types `commit`. And the
process that dies holding a `flock` releases it, so there is no stale lock to
break, only a wedged process to notice.

## Goals / Non-Goals

**Goals:**
- One place that decides how a game is held, so everything above asks to hold a
  game rather than to lock a file.
- The half-read file closed for every reader, including the administrator and
  the observer, which nothing else gates.
- A write that cannot leave a file half-written, by a race or by a crash.

**Non-Goals:**
- Locking across a wait. That would stop the game rather than protect it.
- A database. This is the part of `ARCHITECTURE_OPTIONS.md`'s D2 worth having
  now, and is what makes `BEGIN IMMEDIATE` a swap rather than a rewrite later.
- Locking between games. A game is the unit; two games share nothing.

## Decisions

### 1. The port offers to hold a game, not to lock a file

```
   caller                          repository
   ──────                          ──────────
   with repository.held():         exclusive - nobody else reads or writes
   with repository.held(read=True) shared    - other readers may hold it too
```

`storage/repository.py` says a repository can hold a game and for which purpose;
`YamlGameRepository` implements it with an advisory lock. A repository that
keeps a game in a database would implement the same two words as a transaction,
which is the point of putting it on the port rather than in `turn.py`.

*Why not lock in the service layer*: `service/` would have to know there is a
file to lock, which is the coupling `repository.py` exists to remove — it says
of itself that everything above it is "written against these operations rather
than against a directory of YAML".

### 2. The lock file sits in the game's root, not beside anything that is listed

`<root>/.lock`, alongside `data/` and `players/` rather than inside either.
`player_numbers()` and `committed_players()` both classify by filename, and
`notify.py` had to put its FIFOs in `data/` for exactly this reason. The root is
listed by nothing, which is the one place that needs no reasoning at all.

### 3. Exclusive for the two spans that write, shared for the reads in a load

| span | held | why |
|---|---|---|
| `turn.resolve` | exclusive | the whole of a turn's publication, and the barrier check that authorises it |
| `turn.publish` | exclusive | writes an order file that `resolve` deletes |
| `Game.load`'s reads | shared | several sessions may read at once; a writer excludes them all |
| `wait_for_all_commits` | **not held** | unbounded; holding it stops the game |
| `wait_for_turn` | **not held** | as above |

The barrier deserves a word. `wait_for_all_commits` loops outside the lock and
`resolve` takes it, so the check that releases the loop and the resolution it
authorises are still two steps. What the lock buys is that the *resolution* is
atomic against a commit arriving mid-flight — which is the race that exists.
A caller that must decide and act indivisibly, as an HTTP `POST /commit` will,
takes the lock and re-checks inside it; the port now lets it.

### 4. The read lock covers the shared state, and the draft replay sits outside it

`load` ends by replaying the session's own draft, which writes. The draft is
private to the session that made it — no other process reads or writes it, which
`player-numbering` and `game-persistence` both require — so it needs no lock, and
holding a *read* lock across a write would misdescribe what is happening. The
lock is released when the shared reads are done.

This settles the proposal's open question.

### 5. Held re-entrantly, and bounded rather than forever

`flock` is per open file description, so a second `held()` inside a first would
take a second descriptor and deadlock against itself. Nothing nests today —
`resolve` does not load, `load` does not resolve — but the failure mode is a
hang, and a hang is the worst thing to debug. The repository counts its depth
and locks only at the outermost.

Waiting is bounded rather than indefinite, for the same reason: a wedged holder
turns into a reported error instead of a suite that never finishes. The OS
releases a dead process's lock, so the timeout is for the wedged case only and
can be generous.

### 6. A write replaces the file rather than truncating it

Every write goes to a temporary name in the same directory and is renamed over
the target. Same directory means the same filesystem, which is what makes the
rename atomic; a reader sees the old file or the new one, and a crash leaves the
old one.

The temporary names are chosen so the three places that classify by filename
skip them: `player_numbers()` wants `.yaml` exactly, `committed_players()` wants
`commit_` and digits, and `clear_orders()` wants `_units.yaml` at the end. A
suffix after the extension fails all three.

*Why do this as well as the lock*: the lock closes the race between processes;
the replace closes the crash. Either alone leaves a way to have a file that
cannot be read.

### 7. Where the platform has no lock, it says so and carries on

As `notify.py` does. No `fcntl`, no holding, and the behaviour is exactly
today's — which is not safe, and is not claimed to be.

## Risks / Trade-offs

- **A wedged writer stops the game** → it did not before, because nothing waited
  for anything. The bound in Decision 5 turns it into a reported error rather
  than a hang, and the OS handles the ordinary case of a writer that dies.

- **The barrier is still two steps for the CLI** → Decision 3 explains why that
  is the existing shape and what the lock does buy. The indivisible
  check-and-resolve is available to a caller that takes the lock itself, which
  is what the API will do; retrofitting the CLI's loop to it is not this
  change.

- **Advisory locks bind only those who ask** → anything editing a game directory
  by hand ignores them. That is what advisory means, and it is the same
  contract every process here already runs under.

- **A crash leaves a temporary file behind** → harmless: nothing lists it and
  nothing reads it. Not cleaned up, because a sweep would race a concurrent
  write of the same name.

## Migration Plan

No data migration. `.lock` is created on demand, and a game directory written
before this change is read after it unchanged. A game in progress keeps playing:
a process that holds the lock and one that does not can coexist, the second
being exactly as safe as it was yesterday.

1. The port and the YAML implementation: `held()`, and the replace-rather-than-
   truncate helper the nine writes route through. Nothing calls `held()` yet, so
   the suite must stay green on the replace alone.
2. `resolve` and `publish` hold it for writing.
3. `load`'s shared reads hold it for reading.

Step 1 is separately revertable. Step 3 is the one that can deadlock if a nest
were introduced, and Decision 5 is what stops it.

## Open Questions

None. The proposal's question — how much of `load` a reader's lock covers — is
settled by Decision 4.
