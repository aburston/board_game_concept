## Context

See `proposal.md` — Why. Three facts about the page shape this:

- `board.js` draws on a fixed 44px grid inside a `viewBox`, and sets `width`
  and `height` attributes to the grid's natural size. `style.css` then caps it
  with `max-width: 100%`, so it can shrink and never grow.
- Every glyph the board draws already carries an SVG `<title>`: squares,
  units, flags and the marks of a fight. That is what a pointer shows and what
  a screen reader announces, and it is where the removed prose belongs.
- The page redraws whole screens from one state object, so this is a matter of
  what `renderBoardCard` appends and what `describeUnit` says — no new state
  and no new call.

## Goals / Non-Goals

**Goals:**

- Give the board the width of its pane, bounded by the window's height.
- Empty the board's pane of prose, and put what that prose said where the
  thing it described is.

**Non-Goals:**

- The armoury's deploy board. Its text is instruction for a task in progress —
  which type is being placed, which rows this seat may use — not a key to
  glyphs, and the pane it is in is a form.
- Removing anything a player compares or acts on. The Forces and Orders
  tables, the roster's flag, the feed and the waiting card all stay exactly
  as they are.

## Decisions

### The board is sized by CSS, not by arithmetic in the page

`width: 100%; height: auto` on the `<svg>`, with the `viewBox` doing the
scaling, and `max-height: calc(100vh - 12rem)` so a tall board stays inside
the window. The natural `width`/`height` attributes stay on the element as the
fallback for any context that has no layout to fill.

The alternative — measuring the pane and recomputing `SQUARE` — would put a
layout calculation in a file whose whole discipline is that it draws what it
is given, and would need a resize listener the page does not otherwise have.
The `viewBox` already describes the drawing in its own coordinates; scaling it
is what a `viewBox` is for, and a square stays square because
`preserveAspectRatio` defaults to keeping it so.

### The unit's own description carries the two things the notes said

`describeUnit` in `board.js` gains two clauses: `not on the field yet` for a
unit drawn from a committed setup, and `committed` beside the order for a unit
whose heading came from published orders. Both facts are already known where
the unit is built in `renderBoardCard` — `pending` on the one, the committed
headings on the other — so this is a sentence, not a lookup.

The legend, the flag key and the fight key need nothing: a unit's description
already names its type and whose it is, a flag's says whose flag it is and
what destroying its carrier does, and a mark's says what was taken, dealt and
destroyed on that square.

### The empty-selection prompt goes, and the requirement with it

"Choose one of your units to order it." was written to fill the space where
the compass appears. With no controls and no prose the pane simply ends at the
commit, and how to choose a unit is said over each unit, which is where a hand
is. `web-interface` asked for that written prompt in as many words, so the
requirement is changed rather than quietly broken — see the delta.

### What stays in words

The one thing the removed prose said that nothing else on the board says is
that a committed setup takes the field when the first turn resolves. The
waiting card says it (`Your setup is committed` / `Your army is published`),
and it sits outside both panes, so it is on the screen whichever pane a narrow
window is showing. That is what keeps the `A Committed Setup Is Shown As
Committed` scenario true after the note under the board is gone.

## Risks / Trade-offs

- **A hover is not readable on a touchscreen** → so only explanation moves
  there. Everything a player compares or acts on is in a table, the feed or
  the waiting card, each of which is text on the page. This is the same line
  `The Forces Are Listed Where They Can Be Compared` already draws.
- **A board scaled up is a board with fewer pixels per stroke than it was
  designed for** → the drawing is vector: strokes, glyphs and the rings scale
  with it. What changes is that a unit becomes easier to hit, not harder.
- **A very wide pane makes a very large board** → bounded by the window's
  height, which is the dimension that actually runs out, and the pane is at
  most half the screen on a wide window.
