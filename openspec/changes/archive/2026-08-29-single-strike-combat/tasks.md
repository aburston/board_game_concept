## 1. One strike a turn

- [x] 1.1 Replace the round loop in `exchangeAttacks` with a single exchange:
      snapshot the standing units, charge each payer once, gather every blow,
      then apply them together
- [x] 1.2 Leave `resolveContest` and `resolveCollision` unchanged, confirming
      they settle a square from any survivor count

## 2. Hold the arithmetic to the new rule

- [x] 2.1 A differential test: R5 re-implemented from the prose as a single
      exchange, fought against the engine over a wide space of statistics
- [x] 2.2 Sums by hand: one strike costs the attack value once, hits every
      other unit in the square, and a lethal strike still decides the square
- [x] 2.3 The turn a running game reported — one order onto a wall — now
      strikes once, not six times, and the unit keeps the energy it did not
      spend
- [x] 2.4 Two identical units both survive one exchange, and only annihilate
      when a single strike is lethal

## 3. The tests that assumed rounds

- [x] 3.1 Update the contest tests that ground a crowd down over rounds to the
      single-exchange outcome (sole survivor only on a lethal strike, else
      undecided)
- [x] 3.2 Update `test_attack_cost` and `test_turn_events` where they counted
      rounds or expected an attrition kill

## 4. Write the rule down

- [x] 4.1 Rewrite `GAME_RULES.md` R5, and the two consequences it spells out
      (identical units, `ceil(health ÷ attack)`)

## 5. Finishing

- [x] 5.1 flake8 the package, and confirm determinism still holds
- [x] 5.2 Run the whole suite on both backends
- [x] 5.3 Sync the specs and archive the change
