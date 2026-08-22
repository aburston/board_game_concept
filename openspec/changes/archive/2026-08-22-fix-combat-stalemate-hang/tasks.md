## 1. Combat termination

- [x] 1.1 Add a failing regression test for the hang: two units with energy below their attack value moved into the same empty square, asserting the turn resolves under a timeout
- [x] 1.2 Recount undestroyed contestants at the top of each combat round in `UnitType.commit`, replacing the running `unit_count` decrement; verify the existing combat tests still pass
- [x] 1.3 End combat for a square when a round lands no attacks, leaving every survivor undestroyed; verify test 1.1 now passes
- [x] 1.4 Add a test that an undecided contest destroys nobody and that both survivors report `destroyed is False` and remain on the board
- [x] 1.5 Draw each round's attackers and targets from the units standing when the round begins; add a test that a unit destroyed in an earlier round no longer attacks

## 2. Retreat and square ownership

- [x] 2.1 Record the square a unit vacates during `preCommit`, and clear that record at the start of each turn
- [x] 2.2 Assign the contested square its sole survivor when the contest is decided, empty it when none survive, and return every survivor that moved in to the square it came from when it is undecided; verify with a test covering all three outcomes
- [x] 2.3 Add a test that an undecided contest against a unit already holding the square leaves that unit in place and sends the attacker back
- [x] 2.4 Add a test that a three-way contest with one survivor leaves that survivor holding the square, covering the survivor-count bug from 1.2
- [x] 2.5 Remove only the departing unit when a unit leaves a square, rather than clearing the whole square; verify with a test that a unit sharing the square stays on the board
- [x] 2.6 Render a shared square in `Board.print` via a representative unit for both the full and player views; verify with a test that both render without raising and that a player sees their own unit
- [x] 2.7 Add a test that an opponent with energy can attack and destroy an inert unit holding a square

## 3. Deployment onto an occupied square is illegal

- [x] 3.1 Add `Board.squareIsFree`, covering both a square that is held and a square another unit is waiting to be placed on
- [x] 3.2 Refuse a deployment onto a square that is not free in `Board.add`, before any state is mutated, replacing the assertion that crashed the turn; verify with tests that the refusal names the square and that the refused unit is not registered
- [x] 3.3 Exempt the restore path from the rule, so a saved game holding a shared square still loads; verify with a save/load round-trip test
- [x] 3.4 Catch a refused deployment in the server's order application, report it, and resolve the turn without that order; verify end to end with two players deploying onto the same square on the first turn
- [x] 3.5 Verify end to end that a client refuses a second unit on a square it already holds and stays usable afterwards
- [x] 3.6 Add a test that moving onto an occupied square is still allowed and still resolves as combat

## 4. Telling the player what was refused

- [x] 4.1 Collect refused orders per player while resolving a turn, and publish them as `players/<number>_rejected.yaml`, written for every player on every turn so it describes the turn just resolved
- [x] 4.2 Skip the rejection files in the client's player-file scan, the way `_units_seen.yaml` is skipped, and read them separately into the game data
- [x] 4.3 Report refused orders in the client before it takes the next command, naming the unit, its square and the reason
- [x] 4.4 Refuse an order with an unknown state through the same channel, replacing the assertion that aborted the turn; verify end to end with a published order carrying an invalid state
- [x] 4.5 Refuse a move order naming a unit the player does not own, and fix `getUnitByName` asserting `True` on the miss path, which always passed and returned `None`
- [x] 4.6 Treat `units: None` as no orders when resolving a turn, matching the load path: YAML reads it back as a string, so a player holding no units used to kill the server on commit
- [x] 4.7 Verify end to end that the refused player sees the report on next login, that the accepted player sees nothing, and that a later clean turn clears it

## 5. Persistence

- [x] 5.1 Apply the server's move orders to the named unit belonging to the ordering player instead of `getUnitByCoords`; verify with a test that a move order applies correctly when the unit's square is shared
- [x] 5.2 Add a save/load round-trip test proving a game containing a shared square reloads with every unit restored to that square

## 6. Friendly fire

- [x] 6.1 Confirm against the code that combat does not distinguish friendly units from enemy units, and state it in the `combat-resolution` spec
- [x] 6.2 Add a test that two units of the same player contesting a square attack each other

## 7. Verification

- [x] 7.1 Run the full test suite and confirm all tests pass, including the 14 that existed before this change
- [x] 7.2 Confirm the reported scenarios fail against the unmodified engine: the stalemate hangs, deployment onto an occupied square asserts, and the three-way contest empties the square out from under the survivor
- [x] 7.3 Run the CI lint gate (`flake8 --select=E9,F63,F7,F82`) and confirm it is clean
- [x] 7.4 Confirm the suite passes with the real `board` package installed, as CI installs it from `requirements.txt`
- [x] 7.5 Run `openspec validate --specs --strict` and confirm the main specs validate: 10 passed, 0 failed
- [x] 7.6 Run `openspec validate --changes --strict` and confirm this change's deltas validate
