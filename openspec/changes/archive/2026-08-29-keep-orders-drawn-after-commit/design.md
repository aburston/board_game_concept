## Context

See `proposal.md` — Why.

The board draws an arrow for a unit whenever the unit it is handed carries a
`direction` (`board.js`, `if (own && unit.direction)`). Before a commit that
direction is there: an ordered move is held in the seat's draft, the server
replays the draft onto the session board when it loads it, and the units view
the board is drawn from therefore carries the order.

Committing publishes the draft as orders and clears it. On the next load the
server reads those orders into the game but does not replay them onto the board
the units view is built from — the units view is the resolved board of last
turn — so `direction` is gone and no arrow is drawn. The committed orders are
not lost, though: the `pending` view carries every one of them, which is what
the armoury already uses to draw a committed setup before the first turn.

## Goals / Non-Goals

**Goals:**

- The committed moves stay drawn on the board until the turn resolves.
- The fix stays in the browser, reading what the contract already publishes.

**Non-Goals:**

- Changing what the server draws or stores. The `units` view is the resolved
  board and stays that way; the committed orders are read from `pending`, where
  they already are.
- Any change to the committed/locked messaging, which is already correct.

## Decisions

**The board overlays committed headings from the `pending` view.** When the
seat has committed a turn that has not resolved (`unprocessed_moves` and a
turn number past setup), the play screen reads each of its committed move
orders from `game.pending` — where the order is published as the word `move
north`, `move east`, and so on — and draws the matching unit with that
direction, so `board.js` draws the arrow exactly as it did before the commit.
The units are already on the board at the square the order was given from, so
the arrow points from the right square.

*Alternative considered:* replay the committed orders onto the session board on
the server, so the `units` view carries the direction. It would light up the
arrow with no client change, but it changes what every reader of the `units`
view is given — the CLI included — and makes the resolved-board view carry
this turn's unresolved orders, which is a larger and less honest change than
the browser drawing what `pending` already hands it.

**The pre-first-turn path is untouched.** A committed setup is already drawn
from `pending` by `committedArmy`, because before the first turn the units are
on no board at all. That case is left as it is; this adds the turn-past-setup
case, where the units are on the board and only their headings are missing.

## Risks / Trade-offs

- **The overlay reads an order word rather than a number** → It matches the
  four `move <heading>` words the `pending` view publishes and ignores
  anything else (a hold, a deployment), so a unit without a move draws no
  arrow, which is correct.
- **The arrows look the same committed as in flight** → Intended: the picture a
  player committed is the picture they should keep seeing. That the turn is
  committed and locked is said plainly elsewhere on the screen.
