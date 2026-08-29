## Why

While a player is giving orders, the board draws an arrow out of each unit it
has ordered — the order in flight. When they commit the turn, those arrows
vanish and the board snaps back to where the units stood before any order was
given, even though the orders are committed and waiting to resolve. A player
who has just committed their whole plan is shown a board that looks as though
they did nothing, and the plan they can no longer change is the one thing they
can no longer see.

## What Changes

- After a turn is committed, the board keeps drawing each of the player's
  committed moves as an arrow, exactly as it drew them before the commit,
  until the turn resolves.
- The screen still says the turn is committed and that nothing can be changed
  until it resolves — that messaging is unchanged; only the board is corrected
  to keep showing the committed orders rather than resetting.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `web-interface`: an order drawn on the board stays drawn after the turn is
  committed, until it resolves, rather than disappearing on commit.

## Impact

- `http/static/play.js`: the board overlays the committed moves, read from the
  pending-orders view the commit publishes, onto the units it draws.
- No engine, storage, contract or CLI change. The pending view already carries
  every committed order; this is the browser drawing what it is already given.
