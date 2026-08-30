## Why

A seat is told what a turn did to and by its own units, and nothing of what
other players did to each other. That rule was enforced by **matching unit
names**: a seat held the names of its own units, and an entry reached it where
it mentioned one of them.

A name only has to be unique within one player's own units. `unit-types` says
so and `GAME_RULES.md` R2.7 says so, because two players setting up in secret
cannot avoid choosing alike. So two players who both called a unit `scout`
each read the other's entries about it - where it was placed, where it moved,
what struck it - which is exactly what this rule exists to withhold.

`default-army` made it certain rather than possible: both players are handed
the same array, so every seat of every default game read the other's
deployments.

## What Changes

- Every event that names a unit SHALL also say **whose** units it names.
  `Board.commit` reports them; the detail carries the player numbers involved.
- The seat filter SHALL decide from that rather than from a list of names.
- **BREAKING**: an event's detail gains a `players` key. Stored feeds written
  before this change do not have it, and entries without it reach nobody. No
  migration: a game in progress loses the account of turns already resolved,
  and keeps everything else.

## Capabilities

### Modified Capabilities

- `visibility`: the rule that bounds an account of a turn is stated as whose
  units an entry names rather than which names it mentions, and gains the case
  two players sharing a name always fell through.

## Impact

- `domain/events.py` - `owners()` and `players_in()`, and the `players` detail.
- `domain/board.py`, `domain/unit.py` - every event that names a unit.
- `service/turn_feed.py` - `for_seat` takes the seat's number.
- `service/turn.py` - the caller no longer gathers names.
- No client change: the browser and the CLI read the feed they are given.
