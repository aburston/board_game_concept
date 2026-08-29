## 1. The rule, in one place

- [x] 1.1 Add `domain/placement.py`: `area(number, numbers, size_x, size_y)`
      and `allows(number, numbers, x, y, size_x, size_y)`, the two-player
      top/bottom split with a neutral middle row on an odd row count, and the
      whole board for any other count
- [x] 1.2 Unit-test the helper directly: lower number takes the top, higher
      the bottom; even boards have no neutral row and odd boards have exactly
      the middle one; one, three and more players are unrestricted; the numbers
      used do not matter, only their order; a game reloaded answers the same

## 2. Refuse an out-of-area deployment

- [x] 2.1 In `service/games.py` `deploy_unit`, refuse a placement the helper
      does not allow, before anything is placed, with a message that says
      whether it was the other half or the neutral row
- [x] 2.2 In `service/turn.py` `_refused_deployments`, refuse an out-of-area
      deployment at resolution too, reported like a contested square, so a
      loaded or hand-written deployment is bound by the same rule
- [x] 2.3 Tests for both: a client refusal that leaves the board untouched, and
      a resolution refusal of a deployment that never went through the client

## 3. Publish the area

- [x] 3.1 Add `placement_view(number, players, board)` to `http/views.py`
      returning the board size, the rows this seat may use, and whether it is
      restricted; the whole board for a watcher or a non-two-player game
- [x] 3.2 Register the `placement` view in `http/app.py` (needs a board), and
      cover it over HTTP: a restricted seat reads its half, an unrestricted one
      reads the whole board, and the two seats of a game read opposite halves
- [x] 3.3 Add `placement` to the roles' show subjects and a printer, as a table
      and JSON, so the one-contract parity test holds

## 4. Grey it out in the browser

- [x] 4.1 Fetch the placement view in `loadSeat` and hold it in state
- [x] 4.2 Pass the allowed rows to `renderBoard` from the deploy board, grey
      the squares outside them, and refuse a click on a greyed square; leave
      the play board and a committed setup ungreyed
- [x] 4.3 A caption saying each player deploys on their own half and the middle
      row, where there is one, is neutral
- [x] 4.4 A `test_static_serving` source guard that the deploy board greys the
      disallowed squares, and a `test_web_flow` check that the page reads the
      placement view

## 5. A type with no attack may have energy

- [x] 5.1 Allow attack 0 with any energy, refusing energy 0 with an attack
      above it, and hold a type with energy to the movement-cost floor
- [x] 5.2 Replace the tests that asserted the two zeroes went together, and
      add a scout that moves, strikes nothing, is struck, and keeps its owner
      in the game
- [x] 5.3 Write it down in `GAME_RULES.md` R2.4 and R2.10

## 6. Finishing

- [x] 6.1 `node --check` the changed modules, flake8 the package and tests
- [x] 6.2 Drive it in a browser: the other half is greyed while deploying and a
      click there does nothing
- [x] 6.3 Run the whole suite on both backends
- [x] 6.4 Sync the specs and archive the change
