## 1. Keep the orders drawn

- [x] 1.1 Read this seat's committed move headings from `game.pending` when it
      has committed a turn past setup, and overlay them onto the units the
      board draws, so `board.js` draws the arrows it drew before the commit
- [x] 1.2 Add a board caption while committed, saying these are the orders that
      resolve when every seat has committed

## 2. Hold it to the contract

- [x] 2.1 A `test_web_flow` test that the committed `pending` view carries each
      moved unit's heading, so the board has what it needs to draw the arrows
- [x] 2.2 A source-level guard in `test_static_serving` that the play screen
      overlays committed headings rather than dropping them

## 3. Finishing

- [x] 3.1 `node --check` the changed module, flake8 the tests
- [x] 3.2 Drive it in a browser: order, commit, and see the arrows stay
- [x] 3.3 Run the whole suite on both backends
- [x] 3.4 Sync the specs and archive the change
