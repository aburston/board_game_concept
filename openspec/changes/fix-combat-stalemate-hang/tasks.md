## 1. Combat termination

- [x] 1.1 Add a failing regression test for the hang: two units with energy below their attack value moved into the same empty cell, asserting the turn resolves under a timeout
- [x] 1.2 Recount undestroyed contestants at the top of each combat round in `UnitType.commit`, replacing the running `unit_count` decrement; verify the existing combat tests still pass
- [x] 1.3 End combat for a cell when a round lands no attacks, leaving every survivor undestroyed; verify test 1.1 now passes
- [x] 1.4 Add a test that an undecided contest destroys nobody and that both survivors report `destroyed is False` and remain on the board
- [x] 1.5 Draw each round's attackers and targets from the units standing when the round begins; add a test that a unit destroyed in an earlier round no longer attacks

## 2. Retreat and cell ownership

- [x] 2.1 Record the cell a unit vacates during `preCommit`, and clear that record at the start of each turn
- [x] 2.2 Assign the contested cell its sole survivor when the contest is decided, empty it when none survive, and return every survivor that moved in to the cell it came from when it is undecided; verify with a test covering all three outcomes
- [x] 2.3 Add a test that an undecided contest against a unit already holding the cell leaves that unit in place and sends the attacker back
- [x] 2.4 Add a test that a three-way contest with one survivor leaves that survivor holding the cell, covering the survivor-count bug from 1.2
- [x] 2.5 Remove only the departing unit when a unit leaves a cell, rather than clearing the whole cell; verify with a test that a unit sharing the cell stays on the board
- [x] 2.6 Render a shared cell in `Board.print` via a representative unit for both the full and player views; verify with a test that both render without raising and that a player sees their own unit
- [x] 2.7 Add a test that an opponent with energy can attack and destroy an inert unit holding a cell

## 3. Placement and persistence

- [x] 3.1 Remove the empty-cell assertion from the `INITIAL` branches of `UnitType.preCommit` and `UnitType.commit` so a unit deployed onto an occupied cell joins it; verify with a test that deployment onto an occupied cell resolves as a contest
- [x] 3.2 Apply the server's move orders to the named unit belonging to the ordering player instead of `getUnitByCoords`; verify with a test that a move order applies correctly when the unit's cell is shared
- [x] 3.3 Add a save/load round-trip test proving a game containing a shared cell reloads with every unit restored to that cell

## 4. Friendly fire

- [x] 4.1 Confirm against the code that combat does not distinguish friendly units from enemy units, and state it in the `combat-resolution` spec
- [x] 4.2 Add a test that two units of the same player contesting a cell attack each other

## 5. Verification

- [x] 5.1 Run the full test suite and confirm all tests pass, including the 14 that existed before this change
- [x] 5.2 Confirm the reported scenarios fail against the unmodified engine: the stalemate hangs, deployment onto an occupied cell asserts, and the three-way contest empties the cell out from under the survivor
- [x] 5.3 Run the CI lint gate (`flake8 --select=E9,F63,F7,F82`) and confirm it is clean
- [ ] 5.4 Run `openspec validate --specs --strict` — not run: the `openspec` CLI is not installed in this environment
