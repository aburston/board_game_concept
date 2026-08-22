## 1. Charge for the move

- [x] 1.1 Charge the movement cost in the branch of `UnitType.preCommit` that
      engages a standing unit, and refuse the move when the unit cannot pay it,
      keeping the existing test that it has at least its attack value in energy
      (design.md — Decision 1). Verify a unit that engages spends the same on
      the move as one crossing open ground.

## 2. Cover it

- [x] 2.1 Test that engaging a standing unit costs a move at all. Verify it
      fails against the previous behaviour, where the move was free.
- [x] 2.2 Test that engaging and crossing open ground cost the same, reading
      the attacker's share of combat out of the turn's events so the move can
      be told apart from the fight. Verify it passes.
- [x] 2.3 Test that a unit which can pay for its attack but not for the move
      stays where it is and starts no engagement (design.md — Decision 2).
      Verify its position and energy are unchanged.

## 3. Check it

- [x] 3.1 Run the full suite and the lint CI runs. Verify both are clean and
      that no test needed changing to accommodate the charge.
- [x] 3.2 Record the divergence in `SPEC_COVERAGE.md`, correcting the earlier
      entry that described it as unspecified rather than as a departure from
      `unit-movement`. Verify the entry names the scenario that covers it.
