## Why

The red arrow drawn for a unit under orders is a solid bar with a filled
head, and it reaches well over a quarter of the way into the square it points
at. On a board with several ordered units the arrows are the heaviest thing on
it: they cover the ring, the energy arc and the health bar of whichever
neighbour they cross, and a plan of five moves reads as five red blocks rather
than as five units with headings. The arrow should still be the thing a player
checks last before committing, but it should sit on the board rather than
paint over it.

## What Changes

- The order arrow is drawn as an **outline** - a hollow arrow shape stroked in
  the order colour, with no fill - instead of a solid shaft and a solid head.
- The order arrow is **slightly shorter**: it still starts outside the unit's
  energy arc and still crosses the edge of the unit's own square, but its tip
  stops sooner in the square it is headed for. It keeps pointing at that
  square; it no longer reaches into the middle of it.
- No change to when an arrow is drawn, which units get one, its colour, or its
  behaviour on commit and resolution.

Assumptions recorded here rather than asked: "outline rather than solid" is
taken to mean the whole arrow - shaft and head as one hollow silhouette - not
just an unfilled head on a solid shaft; and "slightly shorter" is taken to mean
the tip moves back by roughly a tenth of a square, staying past the edge of
the unit's square so the arrow still lands in the square it names.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `web-interface`: the requirement "An Order In Flight Is Drawn On The Board"
  gains how the arrow is drawn - as a hollow outline in the order colour, and
  reaching only a short way into the square it points at - alongside the
  existing rules for when it is drawn.

## Impact

- `src/board_game_concept/http/static/board.js`: `orderArrow` draws one
  closed outline instead of a `line` and a filled `polygon`, and the `REACH`
  constant that fixes how far the tip goes comes down.
- `src/board_game_concept/http/static/style.css`: the `.board .order` rules
  change from a stroked shaft plus a filled head to an unfilled, stroked
  outline.
- Tests: a new source-reading test in the style of
  `tests/test_board_selection.py` holds the arrow to the spec - hollow, and
  no further into the next square than the spec allows. No existing test
  names the arrow's shape or reach.
- Not affected: the server, the board view JSON, the CLI, saved games, and
  the compass buttons (whose arrows are text glyphs, not this drawing).
