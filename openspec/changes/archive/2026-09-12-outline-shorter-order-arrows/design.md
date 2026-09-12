## Context

See proposal.md - Why. The arrow has one owner: `orderArrow` in
`http/static/board.js`, which draws a `line.shaft` and a filled
`polygon.head` inside a `g.order`, and `style.css`, which strokes the one at
width 4 and fills the other. Its geometry is written against the board's own
constants: `SQUARE` (44), `ARC` (the energy arc's radius, 14), and `REACH`
(0.78, the tip's distance from the unit's centre as a share of a square). The
start is `ARC + 3` so the arrow clears the arc; the tip is at
`SQUARE * REACH` = 34.3 from the centre, which is 12.3 past the square's edge
at 22 - more than a quarter of the way into the next square, where a unit's
ring (radius 11) begins at 11 from that square's centre.

Nothing else reads `.shaft` or `.head`. The interface has no build step, so
the tests read the source the browser is given (`tests/test_board_selection.py`
lifts a function by its braces and either greps it or runs it under node).

## Goals / Non-Goals

**Goals:**

- One hollow shape per order, stroked and unfilled, in the existing
  `--order` colour so both colour schemes keep working.
- A tip that stays past the edge of its own square and within a quarter of
  the next one, expressed against the same constants the rest of the square
  is drawn with, so moving the arc or the ring moves the arrow with it.
- A test that would catch the arrow being made solid or long again.

**Non-Goals:**

- Changing when arrows are drawn, their colour, or the commit and resolution
  behaviour the rest of the requirement covers.
- Redrawing the compass buttons, whose arrows are text glyphs.
- Any change to the clash marks or health bar layout that shares the square's
  edges with the arrow; they stay where they are.

## Decisions

**The whole arrow is one closed polygon, not a thinner line plus a hollow
head.** A `line` cannot be outlined - stroking it thinner only makes a thinner
bar - so "outline rather than solid" applied to the shaft has to be a shape
with two long sides. Drawing shaft and head as a single seven-point polygon
(the arrow's silhouette) and stroking it with `fill: none` gives one continuous
outline with no seam where the shaft meets the head, which two hollow pieces
overlapped would show. The alternative kept the `line` and only unfilled the
head; it was rejected because a solid shaft with a hollow head reads as a
mistake rather than a style.

Silhouette, in the square's own units along the heading `t` and across it
`s`, with `start = ARC + 3` and `tip = SQUARE * REACH`:
`(start, -2) (tip-9, -2) (tip-9, -5) (tip, 0) (tip-9, 5) (tip-9, 2) (start, 2)`.
The shaft is 4 wide and the head 10 wide by 9 long - the same envelope the
solid arrow had, so its footprint is familiar; only the fill goes.

**Stroked at 1.5 with round joins.** Thick enough to be red at a glance on a
board scaled down to a phone, thin enough that a 4-wide shaft has daylight
inside it. `stroke-linejoin: round` because the tip and the head's corners are
acute and a mitre would spike past the geometry. The existing `stroke-linecap:
round` is dropped - a closed shape has no caps.

**`REACH` comes down from 0.78 to 0.70.** The tip moves from 12.3 past the
edge to 8.8 past it - within the quarter-square (11) the spec allows, and
clear of a neighbouring unit's ring, which starts 11 from that square's centre
(22 - 11 = 11 past the edge). The start does not move, so the shaft loses
about a tenth of its length: shorter, and still unmistakably in the next
square. 0.75 was considered and rejected because 11 past the edge is exactly
on the neighbour's ring; 0.65 was considered and rejected as no longer
"slightly".

**The classes change to match.** `g.order > polygon.outline` replaces
`line.shaft` and `polygon.head`. Keeping the old class names on new shapes
would leave `.shaft` styling a polygon that is not a shaft. Nothing outside
`board.js` and `style.css` names them.

**The test runs the geometry rather than grepping for numbers.** Lifting
`orderArrow` with the existing `_function` helper and running it under node
with a stub `svg` that records attributes lets the test assert the spec's
actual bounds (tip past 22, no further than 33, start beyond `ARC`) for all
four headings, rather than asserting `REACH = 0.70`, which would pin the
implementation instead of the behaviour. The stylesheet half is grepped, as
`test_the_stylesheet_draws_the_box` does: `fill: none` and `var(--order)`
inside the `.board .order` rule.

## Risks / Trade-offs

- [A hollow arrow is fainter than a solid one, and the requirement says "read
  at a glance"] → The stroke stays the saturated `--order` red on both
  schemes, and the silhouette keeps the old arrow's size, so the shape is as
  large as before; only its interior clears. If it proves too faint on a
  phone, the stroke width is one number in the stylesheet.
- [Shortening the tip could leave it on the square's edge, where a heading is
  ambiguous] → The spec fixes both bounds, and the test holds the tip past
  the edge as well as within the quarter.
- [Node may be absent where the tests run] → The geometry test skips without
  node, exactly as the `directionForGroup` tests already do; the stylesheet
  test needs no node.
