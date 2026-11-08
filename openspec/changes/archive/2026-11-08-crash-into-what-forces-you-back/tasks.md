## 1. The rule

- [x] 1.1 A survivor with nowhere to fall back crashes into whoever took its square, one exchange on the ordinary terms, and the unit in the way falls back in its turn down the column; no square ends a turn holding two units, and the `shared` outcome is gone. Built in `ae0b5e1`, "Crash into whoever forces you back, and never share a square": `domain/unit.py` (`_fall_back`, `resolveContest`) and `domain/board.py`.
- [x] 1.2 A unit strikes each other unit at most once a turn, however many exchanges the turn holds, and pays nothing where it has nobody unstruck left to strike. Built in the same commit: the record of who has struck whom in `exchangeAttacks`.
- [x] 1.3 Being forced back costs nothing: the fare paid for the ordered move covers being put back out of it. Built in `9fddfb9`, "Charge nothing for being forced back".

## 2. Holding it

- [x] 2.1 `tests/test_nobody_shares_a_square.py`: the column that crashes into itself all the way down, the crash that clears the way, a unit damaged twice in one turn, a unit too spent to fight landing nothing, and no square holding two units.
- [x] 2.2 `GAME_RULES.md` R5.8a states the rule, and games 201-240 of the match series show it: a column that walks into what it cannot shift destroys its own second rank.

## 3. Closing

- [x] 3.1 Sync the delta into `combat-resolution`: the crash scenarios under "Square Ownership After Combat", and "Simultaneous Damage Application" as the requirement the main spec never carried. Done at the archive.
- [x] 3.2 Remove the wording of the `shared` event, which nothing emits any more.
