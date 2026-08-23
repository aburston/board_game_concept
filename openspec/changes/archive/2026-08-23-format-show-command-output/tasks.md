## 1. The view layer

- [x] 1.1 Add `cli/views.py` with the word translations the tables and the JSON
  share: unit state to `waiting`/`moving`/`holding`/`destroyed`, direction to
  `north`/`east`/`south`/`west`/none, player status to `active`/`eliminated`,
  and a pending order to `move <direction>`/`deploy`/`hold`
- [x] 1.2 Add `types_view(players)` — one entry per unit type, with `player`,
  `name`, `symbol`, `attack`, `health`, `energy`
- [x] 1.3 Add `units_view(board)` — one entry per unit, with `player`, `name`,
  `type`, `symbol`, the unit's current `attack`, `health` and `energy`, `x`,
  `y` (null when it is not on the board), `state` and `direction`
- [x] 1.4 Add `players_view(players, eliminated)` — one entry per registered
  player, with `player` and `status`
- [x] 1.5 Add `pending_view(players)` — one entry per ordered unit, with
  `player`, `unit`, `order`, `x` and `y`, read from each player's published
  orders and flattened across players
- [x] 1.6 Add `board_view(board)` — `size_x`, `size_y`, the rows of square
  characters as the caller may see them, and the distinct symbols drawn with
  the player and type each stands for
- [x] 1.7 Unit-test the views directly against a small game: the values, the
  translated words, `null` position for a destroyed unit, and an empty result
  for each subject

## 2. The table renderer

- [x] 2.1 Add `table(headers, rows, numeric=())` to `cli/render.py`: pad each
  column to the widest of its header and its cells, join with two spaces,
  right-align the numeric columns, write `-` for a missing value, and strip
  trailing whitespace from every line
- [x] 2.2 Unit-test `table` for alignment across rows, right-aligned numbers of
  differing width, the `-` for a missing value, and no trailing whitespace
- [x] 2.3 Add the per-subject table printers, each taking a view and using the
  columns the spec names, and the one-line "nothing yet" message each subject
  prints when its view is empty
- [x] 2.4 Extend `print_board` to print the grid, then a blank line, then the
  `SYMBOL`/`PLAYER`/`TYPE` legend, and to print no legend when no symbol is
  visible

## 3. Grammar and parser

- [x] 3.1 Give `commands.Show` a `format` field, defaulting to `table`
- [x] 3.2 Teach `_parse_show` to accept an optional trailing `json`, and to
  raise `invalid show command` for any other trailing word instead of ignoring
  it
- [x] 3.3 Add the `json` form to each `show` usage in `grammar.py` so `help`
  lists it
- [x] 3.4 Extend `tests/test_parser.py`: `show <subject>` parses with format
  `table`, `show <subject> json` with format `json`, and `show <subject>
  wibble` is refused

## 4. One shared dispatch

- [x] 4.1 Add `cli/show.py` with `perform_show(data, command)`: build the view
  for the subject, then print it as a table or as one `json.dumps(..., indent=2)`
  document keyed by the subject name
- [x] 4.2 Keep the "must create board - set size and commit" message for
  `show board` and `show units` before a board exists, in both formats
- [x] 4.3 Replace the `show` ladder in `bgcserver.py` with a call to
  `perform_show`, removing its pending-orders loop and its `show_board`,
  `show_player` and `show_types` stubs
- [x] 4.4 Replace the `show` ladder in `bgcclient.py` with a call to
  `perform_show`
- [x] 4.5 Replace the `show` ladder in `bgcobserver.py` with a call to
  `perform_show`, removing its copy of the pending-orders loop
- [x] 4.6 Leave `storage/serialise.py` untouched, and check that the server
  still publishes and logs the same YAML it did — only the `show units` display
  moves

## 5. Tests over the roles

- [x] 5.1 Rewrite the `show` assertions in `tests/test_cli_server_surface.py`,
  `tests/test_cli_client_surface.py` and `tests/test_cli_observer_surface.py`
  against the table output, replacing the `number: 1` and `player: 1, moves:`
  expectations
- [x] 5.2 Add a scenario per role driving `show <subject> json`, parsing what
  came back with `json.loads`, and asserting on a field of it
- [x] 5.3 Add a test that the table and the JSON of `show units` describe the
  same units with the same values for one game
- [x] 5.4 Add a client test that `show units json` holds no unit the player has
  not seen, and no storage-internal field
- [x] 5.5 Add a test that `show units wibble` is reported as invalid and prints
  nothing else
- [x] 5.6 Run the full suite and `pylint` over `src/`, and fix what this change
  broke

## 6. Documentation

- [x] 6.1 Update the `show` commands in `GAME_RULES.md` R8 to describe the
  table output and the `json` form
- [x] 6.2 Note the `json` form in `README.md` where the console scripts are
  described
- [x] 6.3 Record in `SPEC_COVERAGE.md` any divergence this change leaves behind

## 7. The read-back after an order

- [x] 7.1 Add `show_units(data)` to `cli/show.py`, printing the units table
  from the same view `show units` uses
- [x] 7.2 Have `bgcclient.py` read a player's units back with it after `move`,
  in place of `serialise_units()`, and drop the import it no longer needs
- [x] 7.3 Rewrite the ordering test in `tests/test_cli_client_surface.py`
  against the table, replacing the `state: 1` expectation

## 8. Name the direction column for what it is

- [x] 8.1 Rename the units column `FACING` to `DIRECTION`, and the view and
  JSON field `facing` to `direction`: a unit holds an order's direction until
  the turn resolves, and does not face anywhere
- [x] 8.2 State in `cli-output` that `DIRECTION` is the order's direction and
  not a heading the unit keeps
- [x] 8.3 Update the tests and the `README.md` example that named the column
