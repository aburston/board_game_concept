## 1. The empty glyph

- [x] 1.1 Change `Empty.__str__` in `src/board_game_concept/domain/square.py` to
      return `" "`, and verify with `python -c "from board_game_concept import
      Empty; print(repr(str(Empty())))"` printing `' '`
- [x] 1.2 Update the example grid in the `src/board_game_concept/cli/render.py`
      module docstring so it draws blanks rather than `#`, and verify no `#`
      remains in that docstring
- [x] 1.3 Change the `emptySymbol` fallback in
      `src/board_game_concept/http/static/board.js` from `'#'` to `' '`, and
      verify by reading the function that the fallback is only reached for a
      view drawn before the `empty` field existed
- [x] 1.4 Confirm `cli/render.py`'s `EMPTY_SQUARE` and `http/views.py`'s
      `board_view` still take the glyph from `Empty()` and name no literal, by
      grepping both files for `'#'` and finding none

## 2. Freeing the character for players

- [x] 2.1 Tighten the symbol assertion in `UnitType.__init__`
      (`src/board_game_concept/domain/unit.py`) to require exactly one
      non-whitespace character, with a message that says which half failed, and
      verify `UnitType('X', ' ', 1, 5, 50)` raises while `UnitType('X', '#', 1,
      5, 50)` is accepted
- [x] 2.2 Verify the refusal reaches every route without further code: a
      `type ... " " ...` definition at the CLI prompt, a define-type request
      over HTTP, and a hand-written player file loaded by
      `service/game.py`, each reporting a refusal rather than an
      `AssertionError` escaping

## 3. Tests that named the old glyph

- [x] 3.1 Update the empty-marker assertions in `tests/test_basic.py:96` and
      `src/board_game_concept/test_suite.py:156` to expect `' '`, and verify
      both suites pass (`pytest tests/test_basic.py` and `python -m
      board_game_concept.test_suite`)
- [x] 3.2 Update the drawn-board expectations in
      `tests/test_board_conventions.py:45-46`, `tests/test_cli_views.py:147`
      and `:160`, and the view fixtures in `tests/test_cli_tables.py:76` and
      `:88`, and verify those three files pass
- [x] 3.3 Re-anchor the board waits at `tests/test_cli_server_surface.py:85`,
      `:210`, `:253`, `tests/test_cli_client_surface.py:312` and
      `tests/test_cli_observer_surface.py:111` from `read_until('#')` to
      `read_until('+-')`, and verify each surface test still fails if the
      board is never drawn (check by temporarily withholding the `show board`)
- [x] 3.4 Drop the redundant `or '#' in ...` half of the assertions in
      `tests/test_observer_over_http.py:99-100` and
      `tests/test_admin_client_over_http.py:98`, and verify both pass

## 4. New behaviour under test

- [x] 4.1 Add a test that a unit type may be defined with the symbol `#`, that
      a unit of it is drawn as `#` on the board, and that it appears in the
      `show board` legend as its type - verify it fails against the old
      one-character-only rule for the right reason
- [x] 4.2 Add a test that a whitespace symbol is refused at construction, and
      one that a board drawn with a single unit has rows of equal width with
      spaces everywhere else (the column-width scenario in the board-model
      delta)

## 5. Whole-suite verification

- [x] 5.1 Run the full suite (`pytest`) plus `python -m
      board_game_concept.test_suite` and verify both are green, with no test
      left waiting on a character the board no longer draws
- [x] 5.2 Play a short game through `bgcserver`/`bgcclient` and through the web
      board, and verify an empty board reads as blank squares between rules in
      both, and that a `#`-symbol unit is visible on each
