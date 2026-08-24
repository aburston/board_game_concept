## Why

Nothing stops two processes writing a game at once, and nothing stops a third
reading it while they do.

The repository port has no lock. `SPEC_COVERAGE.md` has carried the consequence
since the layer split, as divergence 10: a client loading a game raced the
server deleting orders, and died of `FileNotFoundError`. That was patched by
tolerating the file being gone — not by stopping the race, which is still there.
The `wake-a-player-when-the-turn-is-published` change narrowed another one by
reordering, and said in as many words that the class of defect stays until
something serialises the access.

Two exposures remain, and both are ordinary rather than exotic:

- **A reader can see half a file.** The administrator and the observer hold no
  orders, so nothing gates them. Either can call `load` while `write_view` or
  `write_units` is midway through, and get `UnreadableGame` on YAML that is
  perfectly valid a millisecond later. `write_player`, `write_progress` and
  `write_rejections` are the same.

- **A writer can lose to another writer.** Two clients committing at once write
  different files, so they mostly miss each other; a client committing while the
  server resolves does not. `publish` writes an order file and `resolve` deletes
  every order file, and which happens first is decided by nothing.

A crash between opening a file and finishing it leaves the game unopenable, too,
because every write truncates in place.

It matters more the moment there is an API. A request handler is one of many
processes by construction, and the barrier the whole game turns on —
"has every player committed?" — is a read followed by a write with nothing
holding them together. `ARCHITECTURE_OPTIONS.md` reached for a database partly
for this; a lock is the part of that worth having now, and is what makes
`BEGIN IMMEDIATE` a swap rather than a rewrite if a database ever follows.

## What Changes

**A game can be held while it is being read or written, and the holding is the
repository's to offer.**

- **The port gains a lock.** A caller asks the repository to hold a game, for
  reading or for writing; the repository decides how. Everything above is
  written against "hold this game", not against a file.

- **Resolving a turn and publishing a commit take it for writing.** They are the
  two spans that change a game, and they stop overlapping each other and
  everything else.

- **Loading a game takes it for reading.** Several readers may hold it at once;
  a writer excludes them all. This is what closes the half-read file, and it
  closes it for the administrator and the observer, who have nothing else
  gating them.

- **Waiting does not hold it.** The commit barrier blocks for as long as a
  player takes to think, and a lock held across that would stop the game rather
  than protect it. The lock covers the writing, never the waiting.

- **A write replaces a file rather than truncating it.** Written to a temporary
  name in the same directory and renamed over the target, so a reader sees
  either the old file or the new one, and a crash leaves the old one intact
  rather than a half-written one.

**BREAKING**: nothing in the layout, the formats, or what any role does. A game
in progress is unaffected, and a game directory written before this change is
read after it unchanged.

### Where the platform cannot help

`storage/notify.py` already meets a platform without FIFOs by falling back to
waiting on the clock, and says so plainly rather than pretending. Locking takes
the same shape: where the platform offers no lock, the game is not held, the
behaviour is exactly what it is today, and nothing claims otherwise.

## Capabilities

### New Capabilities
None. Holding a game is how the existing requirements are kept, not a new thing
a caller may ask for.

### Modified Capabilities
- `game-persistence`: gains that a game may be held for reading or for writing,
  that a turn is resolved and a commit published while holding it for writing,
  that loading holds it for reading, and that a write replaces a file rather
  than truncating it. The layout and the formats are unchanged.
- `turn-commit`: the commit barrier — "every player still in the game has
  committed" — is answered and acted on while the game is held, so the check and
  the resolution it authorises cannot be separated by another writer. The rule
  is unchanged; what changes is that it can no longer be raced.

## Impact

- **Storage**: `storage/repository.py` gains the lock; `storage/yaml_repository.py`
  implements it over an advisory lock on a file in the game's directory, and
  routes its nine writes through a replace-rather-than-truncate helper. The lock
  file must sit where neither `player_numbers()` nor loading will read it —
  the same care `notify.py`'s FIFOs needed, and for the same reason.
- **Service**: `service/turn.py` — `resolve` and `publish` hold the game for
  writing, and `wait_for_all_commits` and `wait_for_turn` explicitly do not.
  `service/game.py` — `load` holds it for reading.
- **Tests**: `tests/test_repository.py` for the lock itself, including that a
  reader and a reader may hold it together and a writer excludes them. A test
  that two processes cannot interleave a resolution and a commit is the one
  worth having and the one hardest to write; the shape used by
  `tests/test_turn_publication.py` — assert the invariant rather than race
  it — is the model.
- **Docs**: `MODULE_DESCRIPTION.md`'s account of storage; `SPEC_COVERAGE.md`,
  where divergence 10 says the race was tolerated rather than removed, and
  where 27 says this exposure was left open.

## Open questions

1. **Does a reader's lock belong around the whole of `load`, or only the reads?**
   `load` also replays the session's own draft, which writes. Holding a read
   lock across a write is either harmless — the draft is private to the session
   — or a thing to separate. This changes no requirement and no task, only where
   one `with` begins.
