## 1. The selection becomes a set of units

- [x] 1.1 Change `state.selected` in `http/static/app.js` from a unit name to
  an array of unit names (empty for nothing selected), with the comment saying
  it is held in unit-name order; verify by grepping the module for the new
  comment and by `python -m pytest tests/test_static_serving.py`, which must
  still load every module.
- [x] 1.2 In `http/static/play.js`, add `selectedUnits(game)` returning the
  standing units whose names are in `state.selected`, in name order, and
  replace every `state.selected === unit.name` / `find(... state.selected)`
  read with it — the board's `selected` option, the compass, the orders tray's
  `chosen` row and `aria-pressed`, and the keyboard handler; verify no
  `state.selected` comparison against a bare name remains
  (`grep -n "state.selected" src/board_game_concept/http/static/play.js`).
- [x] 1.3 Make every place that clears the selection (`order`, `clearOrder`,
  the commit, `Escape`) set `[]` rather than `null`, and make the tray row's
  click select that unit alone; verify by reading the diff that no assignment
  of a bare name or `null` to `selected` is left.
- [x] 1.4 In `http/static/board.js`, take `settings.selected` as an array and
  mark every unit in it with the existing `rect.selected` outline; verify with
  a test asserting the board module marks a selection of more than one
  (source assertion in the style of `tests/test_web_flow.py`).

## 2. Boxing

- [x] 2.1 Add the box gesture to `board.js`: `pointerdown` on the squares
  layer, a `<rect class="selection-box">` written by attribute during the
  drag, removal on `pointerup`/`pointercancel`, and a call to a new
  `settings.onBox(fromX, fromY, toX, toY)` with the two corners in board
  coordinates (through the existing `at()`); a gesture that moves less than
  `DRAG_THRESHOLD` calls `onSquare` instead. Verify with a test asserting
  `board.js` defines `onBox`, draws `selection-box`, and reuses
  `DRAG_THRESHOLD`.
- [x] 2.2 Make sure a `pointerdown` on a unit does not also start a box (stop
  the propagation in `makeDraggable`), and that `onBox` is only wired where
  ordering is offered — not watching, not committed, not decided; verify by
  the same guard expression as `onDrop` and a source assertion for it.
- [x] 2.3 In `play.js`, implement `onBox` as: take this seat's standing units
  whose square is inside the rectangle, sort by name, and `set({ selected })`
  — replacing whatever was selected, and selecting nothing when the box
  catches nothing. Verify with a test that the filter is against
  `standing(game)` and not `game.units`.
- [x] 2.4 Add `.selection-box` to `http/static/style.css` (dashed outline,
  faint fill, no pointer events) and check it reads in both the board's
  colour schemes; verify by loading the play screen and drawing a box.
- [x] 2.5 Add the two-finger box for touchscreens: `touch-action: pan-x pan-y`
  on the squares layer so one finger still scrolls the page and pinch-zoom is
  ours, and a second pointer going down makes the two touch points opposite
  corners of the box, taken when either is lifted. Verify with a test
  asserting the `touch-action` rule and the second-pointer path exist.

## 3. Click, shift-click and double-click

- [x] 3.1 In `board.js`, pass the originating event to `settings.onUnit(unit,
  event)` and `settings.onSquare(x, y, event)`, and add `onUnitDouble` and
  `onSquareDouble`; hold the single-click callback for 250ms and cancel it
  when a `dblclick` arrives, so one gesture gives one outcome. Verify with a
  test asserting the delay constant and the cancel are both in `board.js`.
- [x] 3.2 In `play.js`, wire `onUnit`: with `event.shiftKey`, add the unit to
  `state.selected` or remove it if already there, leaving the rest alone;
  without shift, select that unit alone. In both cases move the cursor to it.
  Verify with a test asserting both branches exist and that shift-click does
  not clear.
- [x] 3.3 Wire `onSquare` to move the cursor only — no order, no clearing of
  the selection — and confirm the old "click the square beside it to order"
  path is gone; verify by grepping `play.js` for the removed call to `order`
  from `onSquare`.
- [x] 3.4 Wire `onSquareDouble` to `orderGroup` using the direction computed
  in task 4.1; where exactly one unit is selected and the square is not one of
  the four beside it, say the unit moves one square at a time and order
  nothing. Verify with a test covering both the group and single-unit paths.
- [x] 3.5 Wire `onUnitDouble` to take orders back: the whole selection if the
  unit is in it, otherwise that unit alone with the selection untouched.
  Verify with a test asserting the two branches.

## 4. Group orders

- [x] 4.1 Add `directionForGroup(units, x, y)` to `play.js`: the mean of the
  selected units' squares is the centre, the greater of `|dx|` and `|dy|`
  decides the axis with `>=` sending the diagonal tie east/west, and a click
  on the centre itself returns nothing. Verify with unit-level assertions on
  the four headings, the diagonal tie and the centre case.
- [x] 4.2 Replace `order(game, unit, direction)` with `orderGroup(game, units,
  direction)`: send `api.move` per unit in name order, `await`ing each, gather
  the refusals by name, call `loadSeat` **once** afterwards, and report which
  units were refused and why while leaving the rest ordered. Verify with a
  test that only one `loadSeat` follows a group order and that the refusals
  are named.
- [x] 4.3 Do the same for taking back: `holdGroup(game, units)` sending
  `api.hold` per unit that has an order, one reload, refusals named. Verify by
  the same shape of test.
- [x] 4.4 Point the compass at the group: `renderDirections` reads
  `selectedUnits(game)`, shows the unit's name where there is one and
  `<n> units selected` where there are more, and its headings and centre call
  `orderGroup`/`holdGroup`. Verify with a test asserting the plural line and
  the group call.
- [x] 4.5 Say the direction could not be read when a double-click lands on the
  selection's own centre, rather than silently doing nothing; verify by the
  message being produced through `say`.

## 5. The keyboard

- [x] 5.1 In `handleKey`, make an arrow key order every selected unit through
  `orderGroup`, and Backspace/Delete take back every selected unit's order
  through `holdGroup`; verify with a test asserting both call the group
  functions.
- [x] 5.2 Leave `Enter` selecting the unit under the cursor alone and
  `Escape` clearing, and add no key for building a group — a selection is
  built with the pointer only; verify by grepping `handleKey` for
  `shiftKey`, which must not appear.
- [x] 5.3 Update `renderKeys` and the unit hover text in `board.js`
  (`describeUnit`) to say that a move takes a double-click, and that a group
  is selected by boxing or shift-clicking and then ordered with the arrow
  keys; verify by asserting the new words are in the served source.

## 7. What browser testing found

- [x] 7.1 Give the board a grab margin of half a square outside the grid and
  move the box gesture from the squares layer to the SVG root, so a box can be
  anchored outside the board and a group standing in a corner can be boxed at
  all; verify with a test asserting the margin is in the `viewBox` and that
  the gesture listens on the root.
- [x] 7.2 Give the box its own threshold of half a square, separate from the
  drag's four units, so the small travel of a hand giving a double-click never
  draws a box that takes the selection away; verify with a test asserting the
  two thresholds are different and that `makeBoxable` uses the larger.
- [x] 7.3 Count a double-click in `makeClickable` rather than relying on the
  browser's `dblclick`, which the first click's redraw loses, and leave a node
  with no double-click handler firing its single click at once; verify with a
  test asserting there is no `dblclick` listener and that the undeferred path
  exists.

## 8. What the second round of browser testing found

- [x] 8.1 Take the pointer capture in `pointermove` once the gesture passes
  `BOX_THRESHOLD`, not in `pointerdown`: a captured pointer makes the browser
  dispatch the click at the capture element, so every click on a square was
  being delivered to the `<svg>` root and no double-click on a square ever
  ordered anything. Verify with a test asserting `pointerdown` does not
  capture and `pointermove` does.
- [x] 8.2 Make a double-click name a direction rather than a destination for a
  selection of one unit as well as for a group, so a double-click several
  squares off orders one square that way; verify with a test that the
  adjacency check is gone and that one unit and a group take the same path.
- [x] 8.3 Let a click on a unit that is not this seat's own reach the square it
  stands on, so an order can be given onto an occupied square — which is how a
  player attacks; verify with a test asserting the forwarding to
  `onSquare`/`onSquareDouble`.
- [x] 8.4 Update the keys card and the unit's hover text to say the
  double-click points a direction rather than naming a neighbouring square;
  verify by asserting the new words are in the served source.

## 9. A double-click acts on the selection

- [x] 9.1 Make `onUnitDouble` order the selection towards the double-clicked
  unit rather than acting on that unit, so a move onto another unit can be
  given; take the selection's orders back where it names no direction, and
  take the double-clicked unit's order back only where nothing is selected.
  Verify with a test asserting all three branches.
- [x] 9.2 Say it in the keys card and the unit's hover text: a double-click
  points at where the selection should go, whatever is standing there; verify
  by asserting the words are in the served source.

## 10. Clicking away puts the selection down

- [x] 10.1 Make a single click on a square clear the selection as well as
  moving the cursor, so clicking away from your own units puts a group down —
  an empty square and an enemy alike, since an enemy's square reaches the same
  handler; verify with a test asserting the clear and that a double-click
  still orders the group it was given.

## 6. Verification

- [x] 6.1 Add the front-end assertions of tasks 1–5 as a new
  `tests/test_board_selection.py` in the style of the source-level checks in
  `tests/test_web_flow.py`, one test per spec scenario it can reach; verify
  with `python -m pytest tests/test_board_selection.py`.
- [x] 6.2 Run the whole suite — `python -m pytest` — and confirm nothing under
  `domain/`, `service/`, `storage/` or the CLI changed behaviour; the HTTP
  contract tests must pass untouched.
- [x] 6.3 Play a turn in a browser against a running server: box three units,
  double-click east to order them, double-click one of them to take the orders
  back, shift-click a fourth in, order the group with the arrow keys, and
  commit. Confirm each behaves as the spec's scenarios say.
- [x] 6.4 Check the same gestures with a finger on a touchscreen (or emulated
  touch): one finger still scrolls the page, two fingers draw a box, a
  double-tap orders, and dragging a unit onto a neighbouring square still
  orders it.
- [x] 6.5 Update `SPEC_COVERAGE.md` for the `web-interface` requirements this
  change adds and modifies; verify the new requirement names appear there.
