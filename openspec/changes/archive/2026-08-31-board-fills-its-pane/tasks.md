## 1. The board takes the space

- [x] 1.1 Give `.board` the width of its pane in `style.css` — `width: 100%`,
  `height: auto`, and a `max-height` off the window — leaving the natural
  `width`/`height` attributes on the element as the fallback; verify by a
  source-level test and by opening a game at two window sizes.
- [x] 1.2 Check the narrow-screen rules still hold: the board fits a 375px
  phone without the page scrolling sideways; verify `pytest
  tests/test_static_serving.py` passes, the existing narrow-screen assertions
  included.

## 2. The pane is emptied of prose

- [x] 2.1 Remove the legend, the flag key, the fight key, the committed-setup
  note and the committed-orders note from `renderBoardCard` in `play.js`;
  verify by a source-level test that none of those strings is built there.
- [x] 2.2 Remove the "Choose one of your units to order it." prompt, leaving
  the pane with the compass when a unit is selected and nothing where one is
  not; verify by the same test, and that the compass and the commit are still
  appended.

## 3. What the prose said, said on the board

- [x] 3.1 Extend `describeUnit` in `board.js` to say a unit is not on the
  field yet when it is drawn from a committed setup, and that an order is
  committed when its heading came from published orders; verify by a
  source-level test and by hovering both states in a browser.
- [x] 3.2 Pass what those two clauses need from `renderBoardCard` — the
  `pending` flag is already on the unit, the committed headings are already
  computed — without a second lookup; verify by reading the call site in the
  same test.
- [x] 3.3 Confirm what must stay in words is still in words: the waiting card
  still says a committed setup takes the field with the first turn, and the
  Forces, Orders and feed are untouched; verify by a source-level test.

## 4. The whole thing

- [x] 4.1 Run `pytest` and confirm the suite is green.
- [x] 4.2 Play a game in a browser: check the board fills its pane at a wide
  and a narrow window, that no prose is left under it, and that hovering a
  pending unit and a committed order says what the notes used to; verify each
  by observation, with a screenshot of the wide layout.
