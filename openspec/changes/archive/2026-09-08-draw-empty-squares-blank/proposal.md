## Why

An empty square is drawn as `#`, which spends a printable character on nothing
and takes it away from the players: a unit type defined with the symbol `#` is
indistinguishable from the empty squares around it, so one of the few glyphs a
player might reasonably reach for is unusable. A blank square is also what a
board actually looks like - the grid rules already say where the squares are,
so the character inside one only needs to speak when something is standing
there.

## What Changes

- **BREAKING** The empty marker renders as a single space instead of `#`. Every
  reader of a drawn board sees it: the CLI grid (`| |` between rules), the
  `empty` field of the board view JSON, and the web board's fallback glyph.
- `#` becomes an ordinary symbol a player may give a unit type, with no special
  meaning anywhere.
- A unit type's symbol must now be a single **non-whitespace** character. The
  one-character rule alone would let a symbol of `" "` through the HTTP API and
  draw a unit that looked like an empty square; refusing whitespace keeps the
  blank meaning exactly one thing.
- Tests that recognise a drawn board by waiting for `#` are re-anchored on
  something that still identifies a grid (the `+-+-+` rule), and the fixtures
  and assertions naming `#` as the empty glyph are updated.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `board-model`: the Empty Square Representation requirement changes the glyph
  an unoccupied square renders as, from `#` to a single space.
- `unit-types`: the Unit Type Validation requirement tightens the symbol rule
  from "exactly one character" to "exactly one non-whitespace character", and
  says that no printable character - `#` included - is reserved.

## Impact

- `src/board_game_concept/domain/square.py`: `Empty.__str__` returns `" "`.
- `src/board_game_concept/domain/unit.py`: `UnitType.__init__` symbol assertion.
- `src/board_game_concept/cli/render.py`: `EMPTY_SQUARE` follows the domain
  already; the module docstring's example grid needs redrawing.
- `src/board_game_concept/http/views.py`: `board_view`'s `empty` field and the
  flag-placement comparison follow the domain already - no change expected,
  confirmed by test.
- `src/board_game_concept/http/static/board.js`: the `'#'` fallback in
  `emptySymbol` becomes `' '`.
- Tests: `tests/test_basic.py`, `tests/test_board_conventions.py`,
  `tests/test_cli_views.py`, `tests/test_cli_tables.py`,
  `tests/test_cli_server_surface.py`, `tests/test_cli_client_surface.py`,
  `tests/test_cli_observer_surface.py`, `tests/test_observer_over_http.py`,
  `tests/test_admin_client_over_http.py`, and
  `src/board_game_concept/test_suite.py`.
- Not affected: saved games (YAML records units, never square glyphs), so no
  migration; `matches/logs/` and `SPEC_COVERAGE.md` hold transcripts of past
  runs and stay as they were printed.
