## 1. Rest

- [x] 1.1 Add `UnitType.REST_GAIN`, beside `MOVE_COST`, so what a turn gives
      back sits with what a turn costs.
- [x] 1.2 Take a snapshot at the top of `Board.commit` of what every unit that
      was given no order is holding, before `_move` consumes the order
      (design.md — Decision 1).
- [x] 1.3 Add `_rest` as a fourth phase after `_fight`: a unit in the snapshot
      whose energy is unchanged, which is not destroyed and is on the board,
      gains `REST_GAIN`, capped at `type_energy`. Emit a `rested` event and
      describe it in `events.py` (Decision 2).
- [x] 1.4 Verify rest lands before elimination is judged in `service/turn.py`
      (Decision 3).
- [x] 1.5 `tests/test_energy_regeneration.py`: a quiet unit recovers; the cap
      holds; an ordered unit does not rest even when the order was refused at
      the board edge; a unit that fought does not rest; a unit attacked while
      too spent to strike back does rest.

## 2. Walls

- [x] 2.1 Widen the attack range to 0–10 and the energy range to 0–100 in
      `UnitType.__init__`, and assert the two are zero only together
      (Decision 4).
- [x] 2.2 Skip a unit with `attack <= 0` in `exchangeAttacks`, before the
      affordability check, so a wall lands no attacks and a fight with one in
      it terminates (Decision 5).
- [x] 2.3 `tests/test_walls.py`: a wall costs its health; one zero without the
      other is refused; the ranges still hold at their new edges; a wall lands
      no attacks and the fight ends; a wall can be broken; a wall never rests;
      a wall cannot be ordered to move.
- [x] 2.4 `tests/test_cli_client_surface.py`: defining a wall through the
      client works, and a half wall is refused with a message that says why.

## 3. What counts at the end

- [x] 3.1 Judge `eliminated_players` on `type_energy > 0` rather than on the
      energy a unit is holding (Decision 6).
- [x] 3.2 `tests/test_game_outcome.py`: a spent unit keeps its owner in; a
      player left holding only walls is out; losing the last playable unit
      together is a draw.
- [x] 3.3 Check the fixtures that walked a lone unit down to nothing and played
      on — they were written when that ended the game, and now they do not need
      to be, but they should still say what they mean.
- [x] 3.4 Verify that `openspec/specs/` carries exactly the requirements in
      this change's deltas, word for word, so the specs and the code cannot
      have drifted apart in the writing.

## 4. Say so everywhere it is said

- [x] 4.1 `GAME_RULES.md`: add R2.10 (walls) and R3.9 (rest), restate R2.4,
      R2.5, R3.4, R5.10, R7.1 and R7.2, and close Q1 as answered.
- [x] 4.2 `SPEC_COVERAGE.md`: record that divergence 21's settled question was
      reopened and settled again.
- [x] 4.3 Run the whole suite on both storage backends.

## 5. Play it

- [x] 5.1 Add `matches/bots/bulwark.py`, a doctrine that spends half its points
      on walls, so the new type is exercised by something that wants it.
- [x] 5.2 Replay the twenty-game series against the new rules and write up what
      changed in `matches/RESULTS-REST-AND-WALLS.md`.
- [x] 5.3 Replay it a second time once elimination stopped counting on held
      energy (task 3.1), because the first pass had been played against the
      rule that changed. Record which results moved and why, and drop the logs
      of the superseded pass rather than leaving two contradictory records of
      the same twenty pairings.
- [x] 5.4 Mark the two earlier series as played under superseded rules, so no
      reader takes them for how the game behaves now.
