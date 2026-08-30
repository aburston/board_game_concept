## Context

See proposal.md - Why.

`Board.commit` returns `Event`s, each a kind and a detail. A detail names
units (`unit`, `target`, and for a couple of kinds a comma-joined `units`) and
never says whose they are. `turn_feed.for_seat` was handed the names of a
seat's own units and kept an entry that mentioned one of them.

The wording a person reads is built from the detail by `DESCRIPTIONS`, which
reads named keys, so a detail may gain a key without any sentence changing.

## Goals / Non-Goals

**Goals:**

- The rule already written in `visibility` becomes true of two players who
  chose the same unit name.
- One place decides it, as one place decides it now.

**Non-Goals:**

- Making names unique. The rules allow two players to share one on purpose,
  and `default-army` hands them the same array; a game that forbade it would
  be a different game.
- Any change to what a seat may see of the *board*. This is the account of a
  turn, not the view.

## Decisions

### Every event carries the players it involves, as one key

`players` is a comma-joined string of the distinct player numbers whose units
the event names, sorted. `attacked` involves two, `deployed` one, `undecided`
as many as survived.

*Why one key rather than `player` and `target_player`*: `undecided` and
`shared` name a variable number of units, so a per-role key would need a rule
per kind. What the filter asks is "was this seat in it", which is a set
question, so a set is what the event carries.

*Why a string*: a detail travels through JSON and YAML on its way to a client
and back out of storage. `units` already carries a list of names this way, so
a string arrives as the string it left as, on both backends, without anything
in between having to know the key exists.

*Alternative considered*: resolving names against the board at filter time.
It cannot work - that is the same ambiguity, one layer up. A name shared by
two players maps to two units, and the event does not say which.

### Square-only entries are left alone

`contested`, `emptied` and `shared` name nobody and are decided by the square,
as they were: a seat reads them where it was already told something else at
that square. They gain no `players`, because a seat that was in the fight is
already known from the entries that named its units.

### The filter takes a seat number

`for_seat(made, number)` rather than `for_seat(made, owned)`. The caller in
`turn.py` no longer gathers the names of a player's units to pass in, which
also removes the only reason that loop read the board.

## Risks / Trade-offs

**A stored feed written before this change has no `players`, so its entries
reach nobody.** → Accepted, and stated in the proposal. A game in progress
loses the account of turns already resolved; the board, the units and the
game itself are untouched. No migration, per the standing instruction for
this line of work.

**A new event kind that names a unit and forgets `players` would leak
silently** - it would reach nobody rather than everybody, so it fails quiet.
→ `owners()` is one call and every existing site uses it, so the shape is
there to copy. The tests that pin the rule are per-kind.

## Migration Plan

None. Feeds already written are not rewritten.
