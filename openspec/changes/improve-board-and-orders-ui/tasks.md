## 1. The orders tray tells the whole story

- [ ] 1.1 Add an `energy(game, unit)` helper in `play.js` shaped after
  `health()`, reading the design through `designOf`, and use it for the
  Energy cell of the orders table so it reads `3/5`; verify by a source-level
  test in `tests/test_static_serving.py` that the tray's energy cell is
  rendered through the helper rather than `String(unit.energy)`.
- [ ] 1.2 Add an Atk column to the orders table, between Order and Costs,
  filled from the unit's attack; verify the same test asserts the header and
  the cell, and that the Forces table is untouched.
- [ ] 1.3 Check the eight-column tray on a narrow screen against the rule
  `test_wide_content_scrolls_inside_its_card` states, adjusting `style.css`
  only if the table now escapes its card; verify `pytest
  tests/test_static_serving.py` passes.

## 2. Committing from the board's pane

- [ ] 2.1 Call the existing `renderCommit(game)` from the board card in
  `play.js`, beneath the compass, so both panes offer the same commit;
  verify a test asserts the board card renders the commit control and that
  there is still exactly one definition of it.
- [ ] 2.2 Confirm the `c` key still commits with two `button.primary` on the
  screen — the board's is first in document order — and record why beside
  `handleKey`; verify by a source-level test that the board pane's commit
  precedes the tray's in the rendered order.
- [ ] 2.3 Check the committed state: with `unprocessed_moves` set, both panes
  say the turn is committed and neither offers to commit again; verify by a
  test over the rendered source paths for that state.

## 3. Clearing a setup in one action

- [ ] 3.1 Add a "Clear board" control to `armoury.js`, offered only while the
  seat's setup is uncommitted and it has deployed at least one unit, that
  confirms with `window.confirm` and then sends `remove_unit` for each of the
  seat's deployed units in turn, reloading and redrawing once at the end;
  verify by a source-level test that the control is built from `removeUnit`
  and guarded by both conditions.
- [ ] 3.2 Stop on the first refusal, say what was refused, and reload so the
  board shows what is actually deployed; verify by reading the refusal path
  in a test alongside 3.1.
- [ ] 3.3 Drive the behaviour through the contract in `tests/test_web_flow.py`
  as the page drives it: deploy several units, remove each, and assert the
  seat has nothing deployed, its whole budget back, and that another seat's
  units are untouched; verify `pytest tests/test_web_flow.py` passes.
- [ ] 3.4 Assert the refusal the contract gives once a setup is committed, so
  the reason the control is withheld is the server's rule and not a guess;
  verify by a test asserting `remove_unit` after a commit is refused.

## 4. The drag gesture

- [ ] 4.1 Add a pointer-driven drag to `board.js`: `pointerdown` on a unit
  group with `setPointerCapture`, a movement threshold below which the
  gesture stays a click, `pointermove` moving that group's transform, and
  `pointerup` resolving the square through the SVG's screen CTM and calling
  an `onDrop(unit, x, y)` the screen supplies; verify by a source-level test
  that the handlers and the capture are present and that `onDrop` is
  supplied by the screen rather than decided in `board.js`.
- [ ] 4.2 Suppress the click that follows a drag past the threshold, so a
  dropped unit is not also selected or ordered by the click handler; verify
  by a test asserting the suppression is in the source and by a manual pass
  with a mouse.
- [ ] 4.3 Add `touch-action: none` to the board in `style.css` so a finger
  dragging a unit does not scroll the page, and check the coarse-pointer
  rules still hold; verify by a source-level test and a manual pass on a
  touchscreen or a device-emulating browser.
- [ ] 4.4 Offer the drag only where the action behind it is offered — not to a
  watching session, not once the seat has committed, not once the game is
  decided; verify by a test that `onDrop` is passed under the same conditions
  `onUnit` and `onSquare` already are.

## 5. Dragging to order, and dragging to deploy

- [ ] 5.1 Wire `onDrop` in `play.js`: a drop on one of the four squares next
  to the unit orders that move through the existing `order()` path; any
  other drop leaves the unit and its order as they were and says so; verify
  by a source-level test that the neighbour check uses `api.DIRECTIONS` and
  by `pytest tests/test_web_flow.py` for the order the drop sends.
- [ ] 5.2 Wire `onDrop` in `armoury.js`: check the target square against the
  seat's own view first — occupied, or outside the rows `placement`
  publishes — then send `remove_unit` and `add_unit` to re-place the unit,
  keeping its name and type; verify by a source-level test of the guard and
  the two calls.
- [ ] 5.3 Put the unit back where it was if the `add_unit` is refused anyway,
  and say plainly which unit is no longer deployed if the restore is refused
  too; verify by a test reading both failure paths.
- [ ] 5.4 Re-send `set_flag` after a successful re-placement of the unit that
  carried the flag, since taking a unit back drops the designation; verify
  through the contract in `tests/test_web_flow.py` that remove-then-add
  leaves no carrier and that `set_flag` restores it.
- [ ] 5.5 Confirm every existing route still works: click-to-place, the
  compass, the orders rows, the arrow keys and the take-back key; verify
  `pytest tests/test_static_serving.py tests/test_web_flow.py` passes with
  the existing assertions unchanged.

## 6. The board and the trays take turns

- [ ] 6.1 Add `pane: 'board'` to the state in `app.js` and render both panes
  plus a switch in `play.js`, the switch naming the view it shows and
  carrying `aria-pressed`; verify by a source-level test that the choice is
  held in the state rather than read back out of the DOM.
- [ ] 6.2 Add the media query to `style.css` that, below the width where the
  two columns fit, hides the pane not chosen and shows the switch — and above
  it hides the switch and shows both panes; verify by a test asserting the
  query and by resizing a browser.
- [ ] 6.3 Confirm the choice survives a redraw: giving an order while the
  trays are shown leaves the trays shown; verify by a test that nothing in
  the order path resets `pane`.

## 7. The whole thing

- [ ] 7.1 Run the full suite — `pytest` — and the linter the project uses
  (`.pylintrc`) over anything Python that changed; verify both are clean.
- [ ] 7.2 Play a game through in a browser: set up with drags and a clear,
  commit from the board pane, order by dragging and by keyboard, and switch
  panes on a narrow window; verify each of the six behaviours in the issue is
  observable.
- [ ] 7.3 Update `SPEC_COVERAGE.md` if this closes or opens any divergence
  between the specs and the code; verify by reading the entry for
  `web-interface`.
