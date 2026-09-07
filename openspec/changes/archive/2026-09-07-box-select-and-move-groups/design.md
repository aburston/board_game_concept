## Context

See `proposal.md` — Why. What matters here is the shape of what exists.

- `state.selected` in `app.js` is one unit name or `null`, and four places
  read it: the board's `selected` option, the compass in `renderDirections`,
  the orders tray's `chosen` row, and the keyboard handler.
- `board.js` draws the whole board from scratch on every `set()`. Listeners
  live on nodes that are thrown away and rebuilt each render; nothing is
  read back out of the DOM. The one deliberate exception is the drag, which
  writes a transform during the gesture because re-rendering under the
  pointer would destroy the element holding the pointer capture.
- The seat contract takes **one command per POST** (`POST
  .../commands` with a single `{kind: 'move', unit, direction}`). There is no
  batch. A group order is therefore N requests.
- The board is an `<svg>` drawn in a `viewBox` and scaled to fit; `at(root,
  event)` already converts a pointer position into board coordinates through
  the screen matrix, and is what the box gesture needs too.
- `armoury.js` does not read `state.selected`, so the deploy board is
  untouched by the change of shape.

## Goals / Non-Goals

**Goals:**

- One selection model that holds zero, one or many units, with the existing
  single-unit paths falling out of it as the case where the set has one
  member.
- Pointer gestures that never fire two meanings for one action: a click that
  becomes a double-click does the double-click's thing and not also the
  click's.
- No new dependency, no change below `http/static/`, and no change to the
  contract.

**Non-Goals:**

- Batching commands in the HTTP contract. A group order stays N ordinary
  moves; if the request count becomes a problem it is a later change to the
  contract, not to the interface.
- Boxing on the deploy board (`armoury.js`).
- Rubber-band selection of enemy units for inspection.
- Any change to what a move costs or how a turn resolves.

## Decisions

### `state.selected` becomes an array of unit names

An array, ordered by unit name, rather than a `Set` or a keyed object.

- It survives `set()` and the render cycle without special handling, and it
  is trivially comparable and loggable.
- **Ordered by name** so that the order units are sent to the server, and the
  order refusals are reported in, is a function of the game and not of the
  order somebody happened to click things — the same instinct as the
  project's determinism invariant, applied to the interface.
- The single-unit paths become `selected.length === 1`. `renderDirections`,
  the tray's `chosen` class and the board's `selected` option all take the
  array; `board.js` takes `selected` as an array of names and marks each.

Alternative: keep `state.selected` as one name and add `state.group`
alongside it. Rejected — two sources of truth for "what an arrow key orders"
is exactly the bug this would spend its life fixing.

### The box lives on the squares layer, the drag stays on the unit

`board.js` already puts a `pointerdown` on each unit group for the drag. The
box gets its own `pointerdown` on the squares `<g>` (and on the root behind
it), so which gesture starts is decided by what is under the pointer at the
press, exactly as the spec says. The unit's handler already calls
`stopPropagation` on its click; the pointerdown path gets the same treatment
so a press on a unit never also starts a box.

The rectangle is drawn as one `<rect class="selection-box">` appended to the
root and updated by attribute during the gesture — the same deliberate
exception the drag already makes, and for the same reason. It is removed on
`pointerup`/`pointercancel`, and the selection is handed back to the screen
through a new `onBox(fromX, fromY, toX, toY)` option. `board.js` decides
nothing about which units are caught; `play.js` filters its own standing
units, as it does for everything else.

A press and release with movement below `BOX_THRESHOLD` is a click, not a box.
This started out as the drag's existing `DRAG_THRESHOLD` — one question, not
two — and testing in a browser showed why they are two questions after all.
`DRAG_THRESHOLD` is four units of the board's own coordinate system, and the
board is scaled to its pane: on a wide screen four of those are less than a
pixel of glass. Every double-click on a square jittered past it, drew a box
that caught nothing, and so selected nothing — a moment before the second
click tried to order the selection that box had just thrown away. A box is now
half a square of deliberate travel.

The gesture listens on the SVG root rather than on the squares layer, and the
board carries a **grab margin** of half a square outside the grid, drawn as a
transparent rect and added to the `viewBox` so nothing else moves. A box has
to begin somewhere no unit stands, and a group in a corner leaves nowhere:
every square beside it is a unit or off the board. Listening on the root also
means a press on a flag or on a fought square's mark begins a box, which is
what a player pressing on the board expects. A press on a unit stops
propagating, so it never does.

### Click and double-click are resolved by a deferred single click

Both a unit's click (select alone) and a unit's double-click (take orders
back) are wanted, so the single click's effect is held for a short window
(350ms) and dropped if a second click arrives. `board.js` grows `onUnitDouble`
and `onSquareDouble` alongside `onUnit`/`onSquare`, and owns the timer.

The pair is **counted here rather than left to the browser's `dblclick`**.
The first click of a pair redraws the board - it moves the cursor, and
`render` replaces the whole SVG - so the element the browser would fire
`dblclick` at no longer exists by the time it would. Counting the clicks
ourselves means that redraw simply never happens: the first click's effect is
still waiting when the second cancels it.

A node with no double-click handler does not defer at all. The deploy board
places a unit the moment it is asked, as it always has; only a board that
offers both meanings waits to find out which was meant.

Squares do not strictly need the deferral — the spec says a single click on a
square moves the cursor and never clears the selection, so letting it fire
before the order is harmless. It is deferred anyway, so that there is **one**
rule for the whole board rather than two that a later reader has to
rediscover.

The 250ms delay is only ever on the *single* click — selecting a unit and
moving the cursor. Orders, which are the thing worth being sure about, fire
immediately on the double-click.

Alternative: make the single click on a unit fire immediately and have the
double-click undo it. Rejected — undoing a selection change is visible as a
flicker, and a group narrowing to one and then taking back only that one
unit's orders is exactly the wrong outcome.

### `shiftKey` is passed through, not interpreted, by `board.js`

`onUnit(unit, event)` gains the event, and `play.js` reads `event.shiftKey`.
The board keeps knowing nothing about what a selection is.

### A captured pointer takes the click with it

`makeBoxable` must not `setPointerCapture` on the way down. A captured pointer
makes the browser dispatch the resulting `click` at the element holding the
capture, so capturing on `pointerdown` delivered every click on the board to
the `<svg>` root and the square under the pointer never heard it. That is why
a double-click ordered nothing anywhere except on a unit: a unit's own
`pointerdown` stops propagation, so the box gesture — and the capture — never
started there.

The capture is taken in `pointermove`, at the moment the gesture passes
`BOX_THRESHOLD` and becomes a box. By then there is no click left to lose, and
the capture is doing the job it is for: following the gesture off the square
it began on.

### A double-click names a direction, not a destination

For a group this was always so — the direction is read from the centre. A
lone selected unit was the exception: the square had to be one of the four
beside it. That exception does not survive contact with a board. The squares
beside a unit are exactly the squares most likely to have something standing
on them, and moving onto an enemy is how a player attacks — so the one square
they most want to name was among the ones they could not.

One unit is now simply the case where the selection has one member: its own
square is the centre, and a double-click anywhere else reads as a heading.
A unit still moves one square; a square further off is the same move, pointed
at.

The drag keeps its destination semantics — dropping a unit two squares away
is still refused and still says why. A drop is a hand putting a piece
somewhere, and where it lands is the whole of what it means. A double-click
is a finger pointing.

### A double-click serves the selection, not the thing under it

The board hands `onUnitDouble` the unit that was double-clicked, and `play.js`
decides what that means — the board goes on knowing nothing about selections.
What it means is now the same thing it means for a square: order the selection
towards it.

The take-back did not need a gesture of its own to survive. A double-click
that names **no** direction is the centre of the selection, and where one unit
is selected that centre is the unit itself — so double-clicking the selected
unit still takes its orders back, and double-clicking the middle of a group
takes the group's back. The thing double-clicked twice is the thing undone,
and it falls out of the direction arithmetic rather than being a special case
bolted beside it.

With **nothing** selected there is no direction to name, so a double-click on
one of the seat's own units takes that unit's order back. It is the only thing
the gesture can still mean.

### The direction of a group order is computed from the mean square

`centre = (mean of selected x, mean of selected y)`, which may be fractional.
`dx = clickedX - centre.x`, `dy = clickedY - centre.y`; the axis is
`Math.abs(dx) >= Math.abs(dy) ? horizontal : vertical`, and `>=` is what
makes the diagonal tie go east/west as the spec requires. `dx === 0 && dy ===
0` gives no direction and is said.

The mean, not the bounding-box centre: a mean moves with where the units
actually are, so a long thin column being pushed sideways behaves the way it
looks like it should. Both are deterministic; the mean was chosen because it
is the one a player's eye estimates.

### A group order is N sequential requests, then one reload

`orderGroup(game, units, direction)` sends `api.move` for each unit in name
order, `await`ing each so the server sees a defined sequence, collects the
failures by unit name, then calls `loadSeat` **once** and reports. Reasons:

- One reload rather than N: N reloads would redraw the board N times and
  make an eight-unit group order look like a stutter.
- Sequential rather than `Promise.all`: the seat's draft is written per
  command on the server, and concurrent writes to it are not something this
  change should be the first to try. Eight requests on a local socket is not
  the slow part.
- The existing single-unit `order()` becomes `orderGroup` with one member,
  so there is one code path and one error-reporting style.

The same shape serves the group take-back (`api.hold` per unit).

### Building a selection is pointer-only

There is no keyboard equivalent of boxing or shift-clicking. `Enter` keeps
selecting the unit under the cursor alone and `Escape` still clears; no new
key is added.

The existing requirement that every action offered by pointing be reachable
without pointing is still met, and the spec now says how: a selection of
several units is a **shortcut**, not an outcome. Everything it produces —
ordering each unit, taking each order back, committing — a keyboard player
reaches one unit at a time, exactly as they do today. What a group changes is
how many keystrokes it takes, not what can be done. A group built with a
pointer is still ordered by the arrow keys and unordered by the take-back
key, so the two ways of working meet rather than fork.

Alternative: `Shift`+`Enter` to toggle the unit under the cursor, mirroring
the shift-click. Rejected — a second selection model with its own anchor and
its own bugs, to save keystrokes for a player who is not using the gesture
it exists for.

### What the selection looks like

Each selected unit keeps the existing `rect.selected` outline — already
"more than colour alone" and already spec'd. Where more than one is
selected, the compass's line above it reads `4 units selected` instead of a
unit's name, which is also what a screen reader gets. The dragged box is a
dashed outline with a faint fill, from `style.css`.

### Units that vanish fall out of the selection

`play.js` already recomputes the selected unit from `standing(game)` on every
render. The array form filters against `standing(game)` in the same place, so
a destroyed or captured unit leaves the selection with no extra bookkeeping.

## Risks / Trade-offs

- **A 250ms wait before a unit looks selected** → It applies only to
  selection, never to an order, and 250ms is at the bottom of the range that
  reads as a double-click. If it reads as sluggish in practice, the unit's
  ring can be marked optimistically on the single click and un-marked if the
  double arrives — a smaller change than moving the timer.
- **BREAKING: a player used to ordering with one click now gives no order**
  → It is the same gesture with one more click, the compass and the arrow
  keys are unchanged, and the keys card and the unit's hover text both say
  the move takes a double-click. There is no data migration; the worst case
  is a turn where somebody clicks once and nothing happens, which is strictly
  safer than the current worst case of an order given by accident.
- **N requests for a group order** → Bounded by the number of units a seat
  has, sent to a server on the same machine. If it becomes slow the fix is a
  batch command in the contract, which this change is careful not to
  foreclose.
- **A partly-refused group order leaves a half-ordered board** → Spec'd, not
  hidden: the refusals are named and the units that were refused are left as
  they were. Every order is individually reversible until the turn is
  committed.
- **Touch has no double-click, no shift, and no spare one-finger drag** → A
  double-tap fires `dblclick` on every current mobile browser, so ordering is
  the same gesture. Boxing is the awkward one: a one-finger drag on the board
  is a page scroll, and the stylesheet keeps it that way on purpose — a board
  fills a phone's screen, and a player who could not scroll past it would be
  stranded. So the box is a **two-finger** gesture on a touchscreen: the
  squares layer takes `touch-action: pan-x pan-y`, which leaves one-finger
  panning to the browser and takes pinch-zoom away from it, and the two touch
  points are opposite corners of the box. A one-finger drag that the browser
  claims for panning arrives here as a `pointercancel`, which already ends the
  single-pointer gesture, so the two cannot fight. Shift-click has no touch
  equivalent at all; the tray rows select a unit and remain the reliable path,
  as the existing spec already requires.

  The cost is that **pinch-to-zoom no longer works over the board** — it still
  works over the rest of the page. That is a real loss for anyone who zooms to
  read, and it is the price of having any two-finger gesture at all.

## Migration Plan

None: no stored state, no contract change, no schema. The change is static
assets served by the existing app; rolling back is reverting the commit.
`state.selected` lives only in the page and is gone on reload.
