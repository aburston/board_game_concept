## Context

See `proposal.md` — Why. What settles the approach is which of `resolve`'s
writes actually depend on each other.

`_apply_orders` reads `game.players[n]['moves']`, which `load` put in memory
before resolution began. **Nothing in `resolve` reads an order file.** The
deletion at line 221 is therefore free to move: it is not a step resolution
depends on, it is the moment a waiting client is released, and it happens first
only by accident of where it was written.

Between it and the views, `resolve` writes progress, each player's file and
rejections, the authoritative unit record, and each player's view. None of those
read an order file either. So the whole span can be reordered without touching
what resolution computes.

One thing in it is not free to move, and is the trap the proposal names:

```
   turn.py:244   repository.write_orders(number, _as_orders(player['units']))
```

Those are the units a `load player` file brought in, published as that player's
orders for the turn *about to be* resolved. They are the next turn's input, not
this turn's leftovers, and any `clear_orders()` placed after them erases them.

## Goals / Non-Goals

**Goals:**
- A client released from its wait can read the turn it was waiting for.
- The same guarantee for a client that reloads mid-resolution for any other
  reason, since `unprocessed_moves` reads the same fact.
- A test that fails deterministically when the ordering regresses, rather than
  one that catches it twice in twenty-six runs.

**Non-Goals:**
- A lock. The remaining exposure below is narrowed, not closed, and closing it
  is the same problem as every other concurrent write in the repository.
- Any change to what resolution computes: the same orders resolve the same way,
  and `test_determinism.py` must not move.
- A new concept for a client to wait on. The one it has becomes true at the
  right moment instead.

## Decisions

### 1. Publish the turn, then release the waiters

`resolve` is reordered so that everything a released client will read is written
before the fact it waits on goes false:

```
   before                              after
   ─────                               ─────
   clear_orders()          ← released  write_progress
   clear_commits()                     write_player / write_rejections   per player
   write_progress                      write_units
   write_player                        write_view                        per player
   write_orders (loaded)   ← trap      ────────────────────────────────
   write_rejections                    clear_orders()        ← released here
   write_units                         clear_commits()
   write_view              ← readable  write_orders + mark_committed     loaded players
   wake                                wake
```

The per-player loop splits in two, which is what lets `clear_orders()` sit
between them: the first publishes what this turn did, the second seeds what a
loaded player will be resolved for next. That split is the whole change.

*Why not give the client a new fact to wait on* — a resolution counter, a marker
written last, the turn number: the turn number is the tempting one and it is
wrong, because it deliberately does not advance during setup or on a turn where
no unit reaches the board, so "the turn number moved" is not the same as "a
resolution happened". A counter or a marker would work, but both add a concept
to storage and to the port to buy what moving three lines already buys.

### 2. `clear_commits` stays ahead of the loaded player's commit

It spends the commits that opened this turn, and `mark_committed` in the second
loop records a new one on a loaded player's behalf. In the current order that
holds because 223 precedes 245; in the new order it holds because the second
loop comes last. This is easy to get backwards, and getting it backwards makes a
`load player` game hang on a barrier waiting for a player who has nobody to
commit for them — which is the defect the previous change fixed.

### 3. `unprocessed_moves` needs no change

`Game._load_players` sets it from `read_orders`, the same file `wait_for_turn`
tests. It inherits the fix: once the file survives until publishing is done, a
client reloading mid-resolution is told the turn is still in progress rather
than being handed a half-published game. Nothing to edit, and worth a test
saying so, because it is the half of the bug that has no symptom of its own.

### 4. The invariant is asserted, not raced

The bug showed twice in twenty-six suite runs. A test that reproduces the window
by timing would be no better. Instead the repository is wrapped in a recorder
for one resolution and the order of calls is asserted directly:

```
   every write_view      before   clear_orders
   write_units           before   clear_orders
   write_progress        before   clear_orders
   clear_orders          before   any write_orders   (the loaded-player seeding)
   clear_commits         before   any mark_committed
```

That fails the moment someone reorders `resolve`, on every run, in
milliseconds — including the moment someone applies the obvious fix the proposal
warns about.

## Risks / Trade-offs

- **A reader that does not gate on an order file can still tear a page** → the
  administrator and the observer hold no orders, so nothing releases them and
  nothing holds them: either may load while `write_view` is midway through a
  file and get `UnreadableGame`. This change does not address it, because it is
  a different defect — atomicity of a single write, not ordering between
  writes — and its fix is writing to a temporary name and renaming, not
  reordering. Worth its own change; noted rather than absorbed.

- **The window is narrowed, not closed** → between `clear_orders()` and the
  wake, a loaded player's next-turn orders are written. A client reloading
  exactly there sees a fully published turn, which is correct, so the residual
  window is harmless for the case this change is about. It is still a window,
  and the missing lock is what would remove the class.

- **Reordering is behaviour-preserving only because nothing in the span reads
  an order file** → that is checked by reading `resolve` today and holds now.
  A future write placed in the span that *does* read one would break silently.
  The recorder test in Decision 4 pins the order but not the reason, so the
  reason is stated in a comment where the split happens.

## Migration Plan

No data migration and no format change: the same files are written with the same
contents, in a different order. A game in progress is unaffected — at worst a
turn resolved by the old order and the next by the new, which no reader can
tell apart.

1. Split the per-player loop and move `clear_orders()` / `clear_commits()`
   between the halves.
2. Add the recorder test for the ordering invariant.
3. Add the two behavioural tests: a client released from its wait sees its own
   units, and a loaded player's units still reach the board.

Step 1 is the change; steps 2 and 3 are what stop it coming back.

## Open Questions

None. The proposal's first question — what a client should wait on — is settled
by Decision 1: it keeps waiting on what it already waits on. Its second — whether
the window needs closing as well as narrowing — is answered in Risks: not by this
change, and not by ordering at all.
