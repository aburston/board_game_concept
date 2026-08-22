## 1. Combat termination

- [ ] 1.1 Add a failing regression test for the hang: two units with energy below their attack value moved into the same empty cell, asserting the turn resolves under a timeout
- [ ] 1.2 Recount undestroyed contestants at the top of each combat round in `UnitType.commit`, replacing the running `unit_count` decrement; verify the existing combat tests still pass
- [ ] 1.3 End combat for a cell when a round lands no attacks, leaving every survivor undestroyed; verify test 1.1 now passes
- [ ] 1.4 Add a test that a stalemate destroys nobody and that both survivors report `destroyed is False` and remain on the board

## 2. Stacked cells in the engine

- [ ] 2.1 Assign the contested cell its sole survivor when the contest is decided, empty it when none survive, and leave the stack in place when it is undecided; verify with a test covering all three outcomes
- [ ] 2.2 Add a test that a three-way contest with one survivor leaves that survivor holding the cell, covering the survivor-count bug from 1.2
- [ ] 2.3 Render a stacked cell in `Board.print` via a representative unit for both the full and player views; verify with a test that both render without raising and that a player sees their own unit
- [ ] 2.4 Add a test that an opponent with energy can attack and destroy an inert unit holding a cell

## 3. Placement and persistence

- [ ] 3.1 Remove the empty-cell assertion from the `INITIAL` branches of `UnitType.preCommit` and `UnitType.commit` so a unit deployed onto an occupied cell joins it; verify with a test that deployment onto an occupied cell resolves as a contest
- [ ] 3.2 Apply the server's move orders to the named unit belonging to the ordering player instead of `getUnitByCoords`; verify with a test that a move order applies correctly when the unit's cell is stacked
- [ ] 3.3 Add a save/load round-trip test proving a game containing a stacked cell reloads with every unit restored to that cell

## 4. Verification

- [ ] 4.1 Run the full test suite and confirm all tests pass, including the 14 that existed before this change
- [ ] 4.2 Run `openspec validate --specs --strict` and confirm the main specs still validate after syncing
- [ ] 4.3 Reproduce issue #2's original scenario end to end and confirm the server completes the turn instead of spinning
