## Why

The board is the thing a player looks at, and it is the smallest thing on the
screen. It is drawn at a fixed 44 pixels a square — a 6×6 board is 276 pixels
wide in a pane three times that — and beneath it sit up to five paragraphs
explaining glyphs that are already on the board: what each symbol is, what the
flag means, what the crossed swords mean, that a committed army is not on the
field yet, that committed orders cannot be changed, and an instruction to
choose a unit. Every one of them is read once and then read past for the rest
of the game, and together they push the board up into a corner of its own pane.

## What Changes

- **The board fills the pane it is drawn in.** It scales to the width it is
  given rather than staying at its natural size, keeping its proportions, and
  is bounded by the height of the window so a tall board is never taller than
  the screen.
- **The explanatory paragraphs under the board go.** The legend of symbols,
  the flag key, the fight key, the note about a committed setup not being on
  the field, the note about committed orders, and the "choose one of your
  units" instruction are all removed from the board's pane.
- **What they said is said on the board instead**, where the thing they
  describe is: a unit's description already names it, its type, whose it is
  and what it has; it now also says when it is deployed and not yet on the
  field, and when its order is one that has been committed. The flag, the
  marks of a fight and the squares already describe themselves, and how to
  order from the keyboard is already said over a unit.
- **Nothing that is data moves into a hover.** Statistics stay in the Forces
  and Orders tables, who carries a flag stays in the roster, what the turn did
  stays in the feed, and that a committed setup takes the field with the first
  turn is still said by the waiting card, which is not in either pane.

## Capabilities

### New Capabilities

None. This is the existing web interface's board pane.

### Modified Capabilities

- `web-interface`: adds requirements for the board taking the width of its
  pane and for the board's pane carrying no explanatory prose — what a glyph
  means belongs to the glyph — and changes the requirement that puts the
  ordering controls in the board's pane, which asked for a written prompt
  where nothing is selected.

## Impact

- **Code**: `src/board_game_concept/http/static/play.js` (the paragraphs, and
  what the unit descriptions now carry), `board.js` (the descriptions
  themselves), `style.css` (the board's size in its pane).
- **Contract**: none.
- **Tests**: `tests/test_static_serving.py`.
