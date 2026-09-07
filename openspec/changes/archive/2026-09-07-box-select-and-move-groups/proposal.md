## Why

The ordering board can hold exactly one selected unit, so a player with eight
units gives eight separate orders — choose, order, choose, order — to do the
one thing they were actually thinking, which was "this wing advances east".
Every strategy game a player has met lets them draw a box round a group and
move it; this one makes them spell the group out a unit at a time.

The single click is also carrying more meaning than it can hold. On the
ordering board a click on a square beside the selected unit *is* the order,
which means a player who clicks to look at a square has ordered a move
instead. Making a move take a deliberate double-click leaves the single click
free to be what a click should be — choosing — and gives boxing a gesture to
live in.

## What Changes

- A player can draw a **selection box** on the ordering board: press on an
  empty square, drag, and every one of their own units inside the box when
  the pointer is released is selected. Dragging from a square a unit stands
  on still drags that unit, which is what it does today.
- **Shift and left click** adds a unit to the selection, or removes it if it
  is already in it, so a group can be built up and trimmed by hand.
- A plain left click on a unit selects that unit alone, clearing any box.
- **Group movement by double-click**: with two or more units selected, a
  double-click anywhere on the board orders every selected unit to move in
  whichever of the four directions the double-clicked square lies in relative
  to the **centre of the selection**. Each unit still moves one square; the
  group is not dragged to the clicked square.
- **Group movement from the keyboard**: an arrow key orders every selected
  unit that way, exactly as it orders one today, whether the group was boxed
  or shift-clicked together.
- **BREAKING (interaction)**: ordering a single unit by clicking the square
  beside it now takes a **double-click**. A single click on a square moves
  the cursor and never gives an order.
- **Double-clicking a unit takes back orders**: if it is part of the current
  selection, every selected unit's order is taken back; otherwise just its
  own. This is the compass's centre, given to the mouse.
- What is selected is shown on the board for every selected unit, not only
  one, and said in words for a reader that cannot see the ring.
- Dragging a unit onto a neighbouring square still orders it. The compass,
  the orders rows and the arrow keys all still work.

Non-goals: a selection is built with the pointer only — there is no keyboard
equivalent of boxing or shift-clicking, and a keyboard player still orders
their units one at a time as they do today; none of this reaches the deploy
board in the armoury, where a setup is still built one unit at a time; and nothing here changes what an
order costs, how a turn resolves, or what the server is told — a group order
is still one `move` per unit, sent through the same contract.

## Capabilities

### New Capabilities

None. This is the existing web interface learning a gesture.

### Modified Capabilities

- `web-interface`: the board gains a selection that can hold more than one
  unit (boxing, shift-click), group orders from a double-click and from the
  arrow keys, and a double-click requirement on the single-unit move that
  used to be a single click. The requirements describing selection, the
  ordering controls, keyboard play and the drag gesture are all touched.

## Impact

- `src/board_game_concept/http/static/board.js`: the box gesture on the
  squares layer, drawing the box while it is dragged, a click/double-click
  and shift-aware `onUnit`/`onSquare` contract, and drawing a selection of
  more than one.
- `src/board_game_concept/http/static/play.js`: `state.selected` becomes a
  set of names, the keyboard handler orders a group, the compass and the
  orders tray read the new selection, and the double-click paths order and
  take back.
- `src/board_game_concept/http/static/app.js`: the shape of `state.selected`.
- `src/board_game_concept/http/static/style.css`: the selection box, and the
  mark on each selected unit.
- No change to `domain/`, `service/`, `storage/`, the CLI, or the HTTP
  contract. The determinism invariant is untouched: a group order is a set
  of ordinary per-unit orders.
