## Why

Issue #30 collects six things the browser interface makes harder than it needs
to be. Setting up an army can only be undone one unit at a time, and only from
a list beside the board; a unit can only be ordered by clicking a square or
pressing a key, which is not how anybody expects to move a piece on a board,
least of all with a finger; on a phone the board and the trays beside it fight
over the same narrow column; and the Orders tray - the table a player reads
while deciding what to do - omits the two numbers the decision turns on, what
a unit can hit for and how much of its energy is left of what it started with.

## What Changes

- **Clear the board while setting up.** The armoury offers one control that
  takes back every unit this seat has deployed and not committed, on
  confirmation, freeing their squares and their points. It is offered only
  while there is something to take back and the setup is not committed.
- **Units are dragged, on a mouse and on a touchscreen.**
  - On the deploy board, dragging a deployed unit to another square this seat
    may place in moves it there. A drop the server refuses leaves the unit
    where it was.
  - On the play board, dragging a unit onto one of the four squares next to it
    orders that move; dropping it anywhere else changes nothing and says so.
  - Every existing way of doing these things stays: clicking to place, the
    compass, the orders rows, and the arrow keys.
- **The board and the trays take turns on a narrow screen.** Where the layout
  can no longer hold both side by side, one control switches the play screen
  between the board and the tabs beside it, and says which one it is showing.
  A wide screen still shows both at once and offers no toggle.
- **The Orders tray shows energy against the energy the type was built with** -
  `3/5` rather than `3` - the way it already shows health.
- **The Orders tray shows each unit's attack**, so what a unit hits for is read
  where its order is given rather than in the Forces card below it.
- **The board pane carries a commit control of its own**, beside the compass,
  so a player who has just given their last order commits without leaving the
  board. It is the same commit: one confirmation, one call, and both controls
  say the same thing about a turn already committed.

## Capabilities

### New Capabilities

None. Everything here is behaviour of the existing web interface.

### Modified Capabilities

- `web-interface`: adds requirements for clearing a setup in one action, for
  dragging a unit to deploy it and to order it (pointer and touch), for
  switching between the board and the trays where they do not fit side by
  side, and for what the orders tray lists; and extends the requirement that
  puts the ordering controls in the board's pane so that committing is offered
  there too.

## Impact

- **Code**: `src/board_game_concept/http/static/` only - `armoury.js` (clear,
  drag to place), `play.js` (drag to order, orders columns, commit in the board
  pane, the toggle), `board.js` (drag handlers on units and drop targets on
  squares), `style.css` (the toggle's breakpoint, drag affordances, the wider
  orders table).
- **Contract**: none. Clearing is the `remove_unit` command it already sends,
  once per unit; a dragged deployment is `remove_unit` then `add_unit`; a
  dragged order is the `move` command the compass sends. No new endpoint, no
  new command kind, and nothing new for the command-line roles to be missing.
- **Tests**: `tests/test_static_serving.py` (the source-level assertions about
  what the page draws) and `tests/test_web_flow.py` (the contract calls behind
  clearing and re-placing, driven as the page drives them).
- **Assumptions recorded from the request**: the toggle appears only where the
  two panes do not fit side by side, and dragging is offered on both the deploy
  board and the play board.
