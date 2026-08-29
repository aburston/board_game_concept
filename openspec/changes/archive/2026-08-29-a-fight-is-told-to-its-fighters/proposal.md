## Why

Three things found by playing.

A player is told about fights that are none of their business. The rule today
is "you are told about other people's units where you could see every unit
involved", so a seat standing next to two other players reads every blow they
trade — who struck whom, for how much. Being able to see two units is not the
same as being in the fight, and what they did to each other is theirs.

The direction buttons live in the orders tray, on the other side of the
screen from the board they act on. Ordering a unit means looking at the
board, moving to the tray, and looking back to see what happened.

And a unit's energy — which decides whether it can move, whether it can
strike, and whether it is inert — is a number in a table. On the board, the
thing a player is actually looking at, a spent unit and a fresh one are drawn
identically.

## What Changes

- **A fight is told to the people in it.** A seat is told about an entry only
  where one of **its own units** is named in it. Seeing both fighters is no
  longer enough. **BREAKING**: a seat that could previously read two enemies
  fighting in sight is told nothing of it.
- The **direction buttons move into the board's own pane**, under the board,
  so ordering happens where the player is looking, and are laid out as a
  **compass**: the four headings drawn as their arrows, placed where the
  squares they point at are, around a **fifth control in the centre** for
  staying put — which is also what takes an order back.
- A unit's **energy is drawn on its ring**: the outer circle is filled in
  proportion to the energy it has left against what its type was designed
  with, so a spent unit reads as spent at a glance.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `visibility`: an account of a turn is bounded by whose units were in it,
  not by what the seat could see.
- `web-interface`: the direction controls belong to the board pane, and a
  unit's ring shows what energy it has left.

## Impact

- `service/turn_feed.py`: `for_seat` keeps an entry only where one of the
  seat's own units is named.
- `http/static/play.js`: the directions move into the board card.
- `http/static/board.js` and `style.css`: the ring is drawn as a proportion.
- No storage or contract change. The feed is written per seat at resolution,
  so a game already in progress writes narrower feeds from its next turn.
