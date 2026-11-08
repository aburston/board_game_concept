## Context

See proposal.md - Why. What shapes the work is that the glyph already has one
owner: `Empty.__str__` in `domain/square.py`. `cli/render.py` reads it into
`EMPTY_SQUARE`, `http/views.py` publishes it as the board view's `empty` field,
and `board.js` asks the view for it rather than assuming one. So the behaviour
change is a one-character edit in the domain; the work is in the two places
that still name `#` literally (the `emptySymbol` fallback in `board.js`, and
the example grid in the `render.py` docstring), in the new symbol rule, and in
the tests that recognise a board by the character it used to draw nothing with.

The symbol rule has one owner too: `UnitType.__init__` asserts the length, and
every route into the game - the CLI parser, the HTTP API, and reading a saved
player file - constructs a `UnitType` and catches the assertion. Tightening the
assertion therefore tightens all three at once.

## Goals / Non-Goals

**Goals:**

- One place decides what an empty square looks like, and every reader keeps
  asking it rather than knowing the answer.
- The board's drawing reserves no printable character from the players.
- Tests recognise a drawn board by something that is structurally a board.

**Non-Goals:**

- Changing what the grid rules (`+-+-+`) or the legend look like.
- Reserving any other glyph. The web view's flag `!` is drawn only where a
  session cannot see the carrier, and a player defining `!` collides with it
  exactly as they did before this change - out of scope here.
- Rewriting historic transcripts (`matches/logs/`, `SPEC_COVERAGE.md`), which
  record what was printed at the time.

## Decisions

**The glyph stays a single character rather than becoming an empty string.**
The grid draws one character between each pair of `|` rules and the columns
must line up, so a zero-width empty would have to be padded by every reader
that draws a board. A space is the padding, and keeping it one character wide
means no reader changes its layout code. It also keeps `board.js`'s
`if (board.empty)` test working, because `' '` is truthy where `''` is not.

**Whitespace is refused at the domain, in `UnitType.__init__`.** Alternatives
were the CLI parser (which already cannot produce a whitespace symbol, since it
splits the line on whitespace) and the HTTP request handler (which would leave
saved files unchecked). The constructor is the one gate all three routes pass
through, and it is where the length rule already lives, so the two halves of
the symbol rule stay in one sentence of code.

**Tests re-anchor on the rule line, not on a unit's symbol.** The CLI surface
tests currently do `read_until('#')` to mean "a board has been drawn". Waiting
for a space would match almost any output, and waiting for a specific unit's
symbol would couple the test to a fixture's design. `+-+-+` is drawn by every
board and by nothing else, so those waits become `read_until('+-')`. The two
HTTP tests asserting `'+' in output or '#' in output` lose the `#` half, which
was already redundant beside the `+`.

**The `empty` field stays in the board view JSON.** It exists so a reader does
not have to guess the glyph, and a space is exactly the value that would be
hardest to guess - a JSON reader cannot tell a blank cell from a missing one
without being told which it is.

## Risks / Trade-offs

- [A space is invisible, so a board drawn without its rules would read as
  nothing at all] → The rules are drawn by `render_grid` around every row and
  are not optional, so a square is always delimited. The spec pins the column
  width as a scenario.
- [A saved player file written by hand could hold a whitespace symbol and would
  now make the game unreadable, where before it loaded and drew a blank-looking
  unit] → The refusal is the intended behaviour: `UnreadableGame` names the
  type and the reason. No file the CLI or the web UI has ever written can hold
  one, so this is only reachable by hand-editing.
- [Trailing-space sensitivity: a test or a diff tool that strips trailing
  whitespace could alter a drawn board] → Every row ends with `|`, so no drawn
  line ends in a space. Worth keeping true if the grid is ever restyled.
- [Terminal transcripts of old games no longer match new output] → They are
  records, not fixtures; nothing reads them back.

## Migration Plan

None needed. Saved games record units and their types, never the glyph an empty
square was drawn with, so a game saved before this change loads afterwards and
simply draws its empty squares blank. There is no persisted representation to
convert and no rollback step beyond reverting the code.
