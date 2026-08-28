## 1. A game that has begun can be finished

- [x] 1.1 Make `has_started` in `service/turn.py` answer from the board *or*
      from any player having ever committed, with the reasoning in its
      docstring
- [x] 1.2 Test: a first turn in which every deployment is refused as contested
      records turn 1, eliminates both players and decides the game as a draw
- [x] 1.3 Test: the administrator's setup commit is still not a turn and still
      eliminates nobody, in a game whose players have committed nothing
- [x] 1.4 Test: one player's whole army refused and the other's standing leaves
      the standing player the winner
- [x] 1.5 Test: the same over the served contract, so the state a seat reads
      says the game is decided rather than showing an empty board with no
      outcome
- [ ] 1.6 Check both backends answer the same, since the commit marker is read
      from storage
- [x] 1.7 Put a player whose flag never reached the board out, like one whose
      flag has fallen, and report every player's flag in a game that has begun
- [x] 1.8 Test: a player whose carrier was refused is out while the rest of
      their army stands, and the flags record says their flag is not standing

## 2. The armoury keeps what is half-chosen

- [x] 2.1 Hold the deployed type in `state.deployType`, read it when the
      chooser is built and write it back on change, falling back to the first
      type when what it held is gone
- [x] 2.2 Hold a typed board size in `state.boardSize`, falling back to the
      board's own size, and clear it when a size is accepted
- [x] 2.3 Test that both are held in `state` rather than in the page, in the
      style of the other source-level guards in `test_static_serving.py`

## 3. A seat past setup is not offered setup

- [x] 3.1 Draw the committed-setup panel for a seat whose setup is closed, not
      only for one with orders in flight, and say which of the two it is
- [x] 3.2 Test that the armoury offers no design or deployment to a seat whose
      setup turn has resolved

## 4. Finishing

- [ ] 4.1 `node --check` every changed module, and run flake8 over the package
- [ ] 4.2 Run the whole suite on both backends
- [ ] 4.3 Sync the specs and archive the change
