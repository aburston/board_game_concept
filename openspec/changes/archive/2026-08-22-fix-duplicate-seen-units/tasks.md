## 1. Record contact once

- [x] 1.1 Record each contestant at most once in the other's contact list while
      a fight resolves, and verify a unit test of a multi-round fight leaves
      each unit recorded once

## 2. Publish each unit once

- [x] 2.1 List a unit once in a player's view however many of that player's
      units made contact with it, and verify a unit test of two units engaging
      one enemy lists that enemy once

## 3. Restore a unit the board already holds

- [x] 3.1 Add a board lookup that answers whether a player holds a unit by a
      given name instead of asserting, and verify a unit test covering a known
      name, an unknown name, and a name held by another player
- [x] 3.2 Restore a unit the board already holds for that player by putting the
      saved coordinates, health, energy, destroyed and on-board state into it
      rather than registering a second unit, and verify a unit test restoring
      the same unit twice leaves one unit carrying the last state
- [x] 3.3 Keep refusing a reused name on placement and name the player by
      number in that error, and verify a unit test asserting on the message

## 4. Regression coverage and validation

- [x] 4.1 Add an integration test in which two units fight over more than one
      round and a client then reads the resulting view, and verify it fails
      against the unfixed engine and passes against the fixed one
- [x] 4.2 Run the full test suite and `openspec validate fix-duplicate-seen-units`
      and verify both pass
