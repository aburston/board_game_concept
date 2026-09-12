## 1. The arrow's shape

- [x] 1.1 In `src/board_game_concept/http/static/board.js`, rewrite
      `orderArrow` to append a single `polygon` with class `outline` inside
      `g.order`, tracing the seven-point silhouette from design.md (shaft 4
      wide from `ARC + 3`, head 10 wide by 9 long ending at the tip) for the
      given `dx, dy`, and remove the `line.shaft` and `polygon.head`; verify
      by reading the function that it appends exactly one child and that
      every other heading's points are `east`'s turned about the square's
      centre
- [x] 1.2 Update the comment above `orderArrow` and the one above `REACH` so
      they describe a hollow outline and why it is one, and verify no comment
      in `board.js` still describes the arrow as a line with a head on it

## 2. The arrow's length

- [x] 2.1 Change `REACH` in `board.js` from `0.78` to `0.70` and verify
      arithmetically, in the comment beside it, that the tip lands 8.8 past
      the square's edge - inside the next square, within a quarter of its
      width, and short of a neighbouring unit's ring

## 3. The stylesheet

- [x] 3.1 In `src/board_game_concept/http/static/style.css`, replace the
      `.board .order .shaft` and `.board .order .head` rules with one
      `.board .order .outline` rule setting `fill: none`, `stroke:
      var(--order)`, `stroke-width: 1.5` and `stroke-linejoin: round`, and
      update the comment above it; verify with `grep -n "shaft\|\.head"
      src/board_game_concept/http/static/style.css` that nothing still
      styles the removed classes

## 4. Tests

- [x] 4.1 Add `tests/test_order_arrow.py`, reusing the `_static` and
      `_function` approach from `tests/test_board_selection.py`, with a test
      that lifts `orderArrow` and runs it under node with a stub `svg`
      recording each element's tag and attributes, and asserts for each of
      the four headings that exactly one `polygon` is drawn, that its tip
      along the heading is more than 22 and at most 33 from the unit's
      centre, and that its nearest point is at least `ARC + 1.5` from the
      centre; skip when node is absent. Verify it fails against the current
      `orderArrow` (two elements, tip at 34.3) and passes after 1.1 and 2.1
- [x] 4.2 In the same file, add a test that reads the `.board .order` rule
      from `style.css` and asserts `fill: none` and `var(--order)` are in it
      and that no rule for `.shaft` or `.head` under `.board .order` remains;
      verify it fails against the current stylesheet and passes after 3.1

## 5. Verification

- [x] 5.1 Run `pytest tests/test_order_arrow.py tests/test_board_selection.py
      tests/test_static_serving.py tests/test_web_flow.py` and then the full
      `pytest`, and verify both are green
- [x] 5.2 Start the web interface, order a unit each way on a board where
      another unit stands in the square pointed at, and verify in both light
      and dark schemes that each arrow is a hollow red outline, that the
      neighbouring unit's ring and bars show through it, and that the arrow
      still plainly names the square it points at
