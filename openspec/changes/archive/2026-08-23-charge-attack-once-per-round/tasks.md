## 1. Pin the current behaviour down first

- [x] 1.1 Add a test that a unit contesting a cell with two opponents is charged its attack value once for the round, not twice; verify it fails today
- [x] 1.2 Add a test that three units with energy for one round each take the same damage whatever order the cell holds them in; verify it fails today across all six orderings
- [x] 1.3 Add a test that a unit with energy for N rounds can still attack in N rounds however many opponents it faces; verify it fails today

## 2. Charge once per round

- [x] 2.1 Move the affordability test and the energy charge out of the per-target loop in `exchangeAttacks`, leaving damage, events and visibility per target; verify 1.1, 1.2 and 1.3 pass
- [x] 2.2 Verify the two-unit case is unchanged — one opponent, one charge — by the existing combat tests still passing

## 3. Update what the old arithmetic was written into

- [x] 3.1 Update the energy assertions in `tests/test_combat_stalemate.py` and `tests/test_turn_events.py`, changing only energy and leaving the damage expectations alone; verify the suite passes — nothing needed changing: every existing energy assertion is a two-unit contest, where one opponent means one charge either way
- [x] 3.2 Update `GAME_RULES.md` R5.3, which states the per-opponent arithmetic explicitly; verify it matches the new rule

## 4. Hold the game to the no-randomness invariant

- [x] 4.1 Add `tests/test_determinism.py` with a seeded search that builds many random scenarios and resolves each against every permutation of registration order, asserting one identical outcome per scenario; verify it passes
- [x] 4.2 Extend it to assert the same orders resolved twice give the same events in the same order; verify it passes
- [x] 4.3 Add a test asserting the engine imports no source of randomness — no `random`, no clock, no identity-derived ordering; verify it passes
- [x] 4.4 Record the invariant in `openspec/config.yaml`, so it is in front of anyone proposing a rule; verify the context names it
- [x] 4.5 State the invariant in `GAME_RULES.md` R1, alongside "no dice, no randomness, no hidden roll"; verify it says what it constrains

## 5. Verify

- [x] 5.1 Run `pytest` and verify the full suite passes
- [x] 5.2 Run `openspec validate charge-attack-once-per-round --strict` and verify it reports the change valid
